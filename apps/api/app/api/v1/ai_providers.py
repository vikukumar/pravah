"""
Org-level AI Provider Management API
=====================================
Allows organisations to configure their own AI providers (BYOA — Bring Your Own API Key).
These override the platform-level admin defaults in the resolution chain:

  Org Provider  →  Admin Default  →  Env Fallback

All API keys are AES-256 encrypted at rest. The API never returns the raw key.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import TenantContext, require_permission, get_db
from app.core.encryption import decrypt_string, encrypt_string
from app.core.exceptions import PravahException
from app.models.ai import AIProvider
from app.models.system import AuditLog
from app.services.ai_service import AIService, PROVIDER_CATALOG

router = APIRouter()


def _provider_to_dict(p: AIProvider, include_masked_key: bool = True) -> Dict[str, Any]:
    """Serialise AIProvider to response dict. Never returns raw key."""
    masked = None
    if include_masked_key and p.api_key_encrypted:
        try:
            raw = decrypt_string(p.api_key_encrypted)
            if len(raw) > 8:
                masked = raw[:4] + "•" * (len(raw) - 8) + raw[-4:]
            else:
                masked = "••••••••"
        except Exception:
            masked = "••••••••"

    return {
        "id": p.id,
        "name": p.name,
        "provider_type": p.provider_type,
        "api_endpoint": p.api_endpoint,
        "has_api_key": bool(p.api_key_encrypted),
        "masked_api_key": masked,
        "is_default": p.is_default,
        "is_enabled": p.is_enabled,
        "default_model": p.default_model,
        "supports_text": p.supports_text,
        "supports_image": p.supports_image,
        "supports_vision": p.supports_vision,
        "supports_embeddings": p.supports_embeddings,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }


@router.get("/catalog")
async def list_provider_catalog() -> List[Dict[str, Any]]:
    """
    Returns the full catalog of supported AI providers with their models,
    default URIs, and documentation links. No auth required — used for the
    provider selection UI.
    """
    return AIService.get_provider_catalog()


@router.get("")
async def list_org_providers(
    tenant: TenantContext = Depends(require_permission("ai.custom_provider")),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    """List all AI providers configured for this organisation."""
    res = await db.execute(
        select(AIProvider)
        .where(AIProvider.organisation_id == tenant.organisation.id)
        .order_by(AIProvider.is_default.desc(), AIProvider.created_at.asc())
    )
    providers = res.scalars().all()
    return [_provider_to_dict(p) for p in providers]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_org_provider(
    payload: Dict[str, Any],
    tenant: TenantContext = Depends(require_permission("ai.custom_provider")),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Add an AI provider for this organisation.
    The API key is encrypted with AES-256 before storage.
    """
    provider_type = (payload.get("provider_type") or "custom").lower().strip()
    api_key_raw = (payload.get("api_key") or "").strip()
    name = (payload.get("name") or "").strip()

    if not name:
        # Auto-name from catalog
        catalog_entry = next((c for c in PROVIDER_CATALOG if c["id"] == provider_type), None)
        name = catalog_entry["name"] if catalog_entry else f"{provider_type.capitalize()} Provider"

    if not api_key_raw:
        raise HTTPException(status_code=422, detail="API key is required.")

    # Look up default URI from catalog if not provided
    api_endpoint = (payload.get("api_endpoint") or "").strip()
    if not api_endpoint:
        catalog_entry = next((c for c in PROVIDER_CATALOG if c["id"] == provider_type), None)
        api_endpoint = catalog_entry["default_uri"] if catalog_entry else ""

    encrypted_key = encrypt_string(api_key_raw)

    # If this will be the first provider, mark as default
    existing_count_res = await db.execute(
        select(AIProvider).where(AIProvider.organisation_id == tenant.organisation.id)
    )
    is_first = len(existing_count_res.scalars().all()) == 0

    provider = AIProvider(
        organisation_id=tenant.organisation.id,
        name=name,
        provider_type=provider_type,
        api_endpoint=api_endpoint,
        api_key_encrypted=encrypted_key,
        is_default=payload.get("is_default", is_first),
        is_enabled=True,
        default_model=payload.get("default_model") or None,
        supports_text=payload.get("supports_text", True),
        supports_image=payload.get("supports_image", provider_type in ("openai", "openrouter")),
        supports_vision=payload.get("supports_vision", provider_type in ("openai", "openrouter", "google")),
        supports_embeddings=payload.get("supports_embeddings", False),
    )
    db.add(provider)

    # If set as default, unset others
    if provider.is_default:
        existing_res = await db.execute(
            select(AIProvider).where(
                AIProvider.organisation_id == tenant.organisation.id,
                AIProvider.is_default == True,
            )
        )
        for existing in existing_res.scalars().all():
            existing.is_default = False

    audit = AuditLog(
        actor_id=tenant.user.id,
        actor_email=tenant.user.email,
        organisation_id=tenant.organisation.id,
        action="ai_provider.created",
        target_type="ai_provider",
        result="success",
        details={"provider_type": provider_type, "name": name, "endpoint": api_endpoint},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(provider)
    return _provider_to_dict(provider)


@router.patch("/{provider_id}")
async def update_org_provider(
    provider_id: str,
    payload: Dict[str, Any],
    tenant: TenantContext = Depends(require_permission("ai.custom_provider")),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Update an existing org AI provider. Partial updates supported."""
    res = await db.execute(
        select(AIProvider).where(
            AIProvider.id == provider_id,
            AIProvider.organisation_id == tenant.organisation.id,
        )
    )
    provider = res.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="AI provider not found.")

    if "name" in payload and payload["name"]:
        provider.name = payload["name"].strip()
    if "api_endpoint" in payload and payload["api_endpoint"]:
        provider.api_endpoint = payload["api_endpoint"].strip()
    if "api_key" in payload and payload["api_key"]:
        provider.api_key_encrypted = encrypt_string(payload["api_key"].strip())
    if "default_model" in payload:
        provider.default_model = payload["default_model"] or None
    if "is_enabled" in payload:
        provider.is_enabled = bool(payload["is_enabled"])
    if "supports_text" in payload:
        provider.supports_text = bool(payload["supports_text"])
    if "supports_image" in payload:
        provider.supports_image = bool(payload["supports_image"])
    if "supports_vision" in payload:
        provider.supports_vision = bool(payload["supports_vision"])

    if payload.get("is_default"):
        # Unset all other defaults for this org
        others_res = await db.execute(
            select(AIProvider).where(
                AIProvider.organisation_id == tenant.organisation.id,
                AIProvider.id != provider_id,
            )
        )
        for other in others_res.scalars().all():
            other.is_default = False
        provider.is_default = True

    await db.commit()
    await db.refresh(provider)
    return _provider_to_dict(provider)


@router.post("/{provider_id}/set-default")
async def set_default_provider(
    provider_id: str,
    tenant: TenantContext = Depends(require_permission("ai.custom_provider")),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Set a provider as the default for this organisation."""
    res = await db.execute(
        select(AIProvider).where(
            AIProvider.id == provider_id,
            AIProvider.organisation_id == tenant.organisation.id,
        )
    )
    provider = res.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="AI provider not found.")

    # Unset all defaults
    all_res = await db.execute(
        select(AIProvider).where(AIProvider.organisation_id == tenant.organisation.id)
    )
    for p in all_res.scalars().all():
        p.is_default = False

    provider.is_default = True
    await db.commit()
    await db.refresh(provider)
    return _provider_to_dict(provider)


@router.post("/{provider_id}/test")
async def test_org_provider(
    provider_id: str,
    tenant: TenantContext = Depends(require_permission("ai.custom_provider")),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Live-test an org AI provider connectivity and credentials.
    Returns success/error status without exposing the raw API key.
    """
    res = await db.execute(
        select(AIProvider).where(
            AIProvider.id == provider_id,
            AIProvider.organisation_id == tenant.organisation.id,
        )
    )
    provider = res.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="AI provider not found.")

    if not provider.api_key_encrypted:
        return {"status": "error", "message": "No API key configured for this provider."}

    try:
        api_key = decrypt_string(provider.api_key_encrypted)
    except Exception:
        return {"status": "error", "message": "Failed to decrypt API key — provider may need to be reconfigured."}

    ai_svc = AIService(db)
    result = await ai_svc.test_provider_connection(
        provider_id=provider.provider_type,
        base_uri=provider.api_endpoint or "https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    return result


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_org_provider(
    provider_id: str,
    tenant: TenantContext = Depends(require_permission("ai.custom_provider")),
    db: AsyncSession = Depends(get_db),
):
    """Remove an org AI provider. If it was the default, the platform default takes over."""
    res = await db.execute(
        select(AIProvider).where(
            AIProvider.id == provider_id,
            AIProvider.organisation_id == tenant.organisation.id,
        )
    )
    provider = res.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="AI provider not found.")

    audit = AuditLog(
        actor_id=tenant.user.id,
        actor_email=tenant.user.email,
        organisation_id=tenant.organisation.id,
        action="ai_provider.deleted",
        target_type="ai_provider",
        result="success",
        details={"provider_type": provider.provider_type, "name": provider.name},
    )
    db.add(audit)
    await db.delete(provider)
    await db.commit()


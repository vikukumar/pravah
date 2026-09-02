"""
PRAVAH AI Provider Resolution Engine
=======================================
Implements the provider selection chain from PRD §8 and §30:

  User-scoped Provider
        ↓
  Organisation-scoped Provider
        ↓
  Admin Platform Default (SystemSetting ai_config)
        ↓
  Built-in Fallback (env/settings)

Capabilities: text, image, vision, embeddings, moderation

The resolver returns a fully-hydrated ProviderConfig that the AI service
uses directly without needing to know which provider was selected.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.encryption import decrypt_string
from app.core.exceptions import PravahException
from app.models.ai import AIProvider, AIModel
from app.models.system import SystemSetting

logger = logging.getLogger("pravah.provider_resolver")


@dataclass
class ProviderConfig:
    """Fully resolved provider ready for API calls."""
    provider_id: str          # e.g. "openrouter", "openai", "anthropic", "custom"
    provider_name: str
    base_uri: str
    api_key: str              # Decrypted at runtime, never logged
    model: str
    capability: str           # "text", "image", "vision", "embeddings"
    timeout_seconds: int = 30
    max_tokens: int = 1200
    temperature: float = 0.7
    fallback_provider: Optional["ProviderConfig"] = None
    source: str = "platform_default"  # "user" | "organisation" | "admin" | "platform_default"

    def masked_key(self) -> str:
        """Return a safely masked API key for logging."""
        if not self.api_key or len(self.api_key) < 8:
            return "****"
        return self.api_key[:4] + "****" + self.api_key[-4:]


class ProviderResolver:
    """
    Resolves the correct AI provider for a given operation.
    Follows the PRD §30 priority chain without exposing secrets.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def resolve(
        self,
        capability: str = "text",
        org_id: Optional[str] = None,
        user_id: Optional[str] = None,
        model_override: Optional[str] = None,
        provider_override: Optional[str] = None,
    ) -> ProviderConfig:
        """
        Resolve provider for the given capability following the priority chain.

        Returns ProviderConfig with decrypted credentials.
        Raises PravahException if no valid provider found.
        """

        # --- Level 1: Organisation-configured provider (plan-gated BYOA) ---
        if org_id:
            org_provider = await self._resolve_org_provider(org_id, capability, model_override)
            if org_provider:
                logger.info(
                    "Provider resolved from organisation scope for org=%s capability=%s provider=%s",
                    org_id, capability, org_provider.provider_id
                )
                return org_provider

        # --- Level 2: Admin platform default (SystemSetting ai_config) ---
        admin_provider = await self._resolve_admin_provider(capability, model_override)
        if admin_provider:
            logger.info("Provider resolved from admin platform config capability=%s provider=%s",
                       capability, admin_provider.provider_id)
            return admin_provider

        # --- Level 3: Environment fallback ---
        fallback = self._build_env_fallback(capability, model_override)
        if fallback:
            logger.info("Provider resolved from environment fallback capability=%s", capability)
            return fallback

        raise PravahException(
            detail=f"No AI provider configured for capability '{capability}'. Please configure an AI provider in Admin → AI Models.",
            error_code="NO_PROVIDER_CONFIGURED",
        )

    async def _resolve_org_provider(
        self, org_id: str, capability: str, model_override: Optional[str]
    ) -> Optional[ProviderConfig]:
        """Find active organisation-level AI provider for the requested capability."""
        try:
            query = (
                select(AIProvider)
                .where(
                    AIProvider.organisation_id == org_id,
                    AIProvider.is_active == True,
                    AIProvider.is_deleted == False,
                )
                .order_by(AIProvider.priority.asc())
                .limit(5)
            )
            res = await self.db.execute(query)
            providers = res.scalars().all()

            for prov in providers:
                if not prov.api_key_encrypted:
                    continue
                try:
                    api_key = decrypt_string(prov.api_key_encrypted)
                except Exception:
                    continue

                # Match capability
                prov_caps = prov.capabilities or []
                if capability not in prov_caps and "text" not in prov_caps:
                    continue

                model = model_override or prov.default_model or "gpt-4o-mini"

                return ProviderConfig(
                    provider_id=prov.provider_type or "custom",
                    provider_name=prov.name,
                    base_uri=prov.base_url or "https://openrouter.ai/api/v1",
                    api_key=api_key,
                    model=model,
                    capability=capability,
                    timeout_seconds=prov.timeout_seconds or 30,
                    max_tokens=prov.max_tokens or 1200,
                    temperature=float(prov.temperature or 0.7),
                    source="organisation",
                )
        except Exception as e:
            logger.warning("Error resolving org provider for org=%s: %s", org_id, e)
        return None

    async def _resolve_admin_provider(
        self, capability: str, model_override: Optional[str]
    ) -> Optional[ProviderConfig]:
        """Find admin-configured platform default AI provider."""
        try:
            res = await self.db.execute(
                select(SystemSetting).where(SystemSetting.key == "ai_config")
            )
            sys_setting = res.scalar_one_or_none()

            if sys_setting and isinstance(sys_setting.value, dict):
                cfg = sys_setting.value

                # Pick the right key + model for the requested capability
                api_key = ""
                provider_id = cfg.get("provider_id", "openrouter")
                base_uri = cfg.get("base_uri", "https://openrouter.ai/api/v1")

                if capability == "image":
                    api_key = cfg.get("image_api_key") or cfg.get("openrouter_api_key", "")
                    model = model_override or cfg.get("default_image_model", "black-forest-labs/flux-1-schnell")
                else:
                    api_key = cfg.get("openrouter_api_key") or cfg.get("api_key", "")
                    model = model_override or cfg.get("default_text_model", settings.DEFAULT_AI_MODEL)

                if api_key:
                    return ProviderConfig(
                        provider_id=provider_id,
                        provider_name=cfg.get("provider_name", "Admin Default"),
                        base_uri=base_uri,
                        api_key=api_key,
                        model=model,
                        capability=capability,
                        source="admin",
                    )
        except Exception as e:
            logger.warning("Error resolving admin provider: %s", e)
        return None

    def _build_env_fallback(
        self, capability: str, model_override: Optional[str]
    ) -> Optional[ProviderConfig]:
        """Build provider config from environment variables."""
        api_key = settings.OPENROUTER_API_KEY or ""
        if not api_key:
            return None

        if capability == "image":
            model = model_override or settings.IMAGE_AI_MODEL
        else:
            model = model_override or settings.DEFAULT_AI_MODEL

        return ProviderConfig(
            provider_id="openrouter",
            provider_name="OpenRouter (Environment Default)",
            base_uri="https://openrouter.ai/api/v1",
            api_key=api_key,
            model=model,
            capability=capability,
            source="platform_default",
        )

    async def test_provider(self, config: ProviderConfig) -> Dict[str, Any]:
        """Live-test a resolved provider config. Used for health checks."""
        import httpx
        uri = config.base_uri.rstrip("/")

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                if config.provider_id == "anthropic":
                    resp = await client.post(
                        f"{uri}/messages",
                        headers={
                            "x-api-key": config.api_key,
                            "anthropic-version": "2023-06-01",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": "claude-3-5-haiku-latest",
                            "max_tokens": 1,
                            "messages": [{"role": "user", "content": "ping"}],
                        },
                    )
                else:
                    resp = await client.get(
                        f"{uri}/models",
                        headers={"Authorization": f"Bearer {config.api_key}"},
                    )
                return {
                    "status": "success" if resp.status_code in (200, 201) else "error",
                    "status_code": resp.status_code,
                    "provider": config.provider_id,
                    "model": config.model,
                    "source": config.source,
                }
        except Exception as e:
            return {
                "status": "error",
                "provider": config.provider_id,
                "error": str(e),
            }

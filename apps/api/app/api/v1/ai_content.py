"""
PRAVAH AI Auto-Content API Router
Provides SEO content generation, one-click auto-publish, and content suggestions.
All endpoints require an AI provider to be configured in Admin → AI Providers.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import TenantContext, get_db, require_permission
from app.services.ai_service import AIService
from app.services.social_posts_service import SocialPostsService

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────────────────────

class SEOGenerateRequest(BaseModel):
    topic: str
    platforms: List[str]
    brand_voice: str = "professional"  # professional | casual | viral | educational | inspirational
    keywords: Optional[List[str]] = None
    call_to_action: Optional[str] = None
    use_post_history: bool = False
    account_ids: Optional[List[str]] = None  # For fetching post history context
    model_override: Optional[str] = None


class AutoContentRequest(BaseModel):
    topic: str
    platforms: List[str]
    account_ids: List[str]  # Target social accounts
    brand_voice: str = "professional"
    keywords: Optional[List[str]] = None
    call_to_action: Optional[str] = None
    generate_image: bool = True
    image_style: str = "photorealistic"  # photorealistic | illustration | flat | 3d | watercolor
    action: str = "draft"  # draft | schedule | publish
    scheduled_at: Optional[datetime] = None
    approval_required: bool = False
    use_post_history: bool = False


class ImageGenerateRequest(BaseModel):
    prompt: str
    style: str = "photorealistic"
    aspect_ratio: str = "1:1"  # 1:1 | 4:5 | 16:9 | 9:16


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/generate-seo", summary="Generate SEO-optimized social media content")
async def generate_seo_content(
    payload: SEOGenerateRequest,
    tenant: TenantContext = Depends(require_permission("content.create")),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Generate SEO-optimized, platform-specific social media content.
    Supports all configured AI providers (ChatGPT, Gemini, Claude, Groq, etc.)

    Returns structured content with:
    - Platform-specific body text
    - Hashtags per platform
    - Image alt text
    - Meta description
    - AI image generation prompt
    - Suggested posting time
    """
    ai_svc = AIService(db)

    # Optionally fetch post history context for style matching
    post_history_context = None
    if payload.use_post_history and payload.account_ids:
        posts_svc = SocialPostsService(db)
        post_history_context = await posts_svc.get_style_context(
            org_id=tenant.organisation.id,
            account_ids=payload.account_ids,
            limit=8,
        )

    return await ai_svc.generate_seo_content(
        org=tenant.organisation,
        user=tenant.user,
        topic=payload.topic,
        platforms=payload.platforms,
        brand_voice=payload.brand_voice,
        keywords=payload.keywords,
        call_to_action=payload.call_to_action,
        post_history_context=post_history_context,
        model_override=payload.model_override,
    )


@router.post("/auto-content", summary="One-click: Generate + Image + Create content")
async def auto_generate_content(
    payload: AutoContentRequest,
    tenant: TenantContext = Depends(require_permission("content.create")),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Full automation pipeline:
    1. Generate SEO-optimized text for each target platform
    2. Generate an AI image (if enabled)
    3. Create a Content record in the database
    4. Optionally schedule or publish immediately

    This is the "Auto Generate & Post" one-click feature.
    """
    ai_svc = AIService(db)

    post_history_context = None
    if payload.use_post_history and payload.account_ids:
        posts_svc = SocialPostsService(db)
        post_history_context = await posts_svc.get_style_context(
            org_id=tenant.organisation.id,
            account_ids=payload.account_ids,
            limit=8,
        )

    return await ai_svc.auto_generate_and_publish(
        org=tenant.organisation,
        user=tenant.user,
        topic=payload.topic,
        platforms=payload.platforms,
        account_ids=payload.account_ids,
        brand_voice=payload.brand_voice,
        keywords=payload.keywords,
        call_to_action=payload.call_to_action,
        generate_image=payload.generate_image,
        image_style=payload.image_style,
        action=payload.action,
        scheduled_at=payload.scheduled_at,
        approval_required=payload.approval_required,
        post_history_context=post_history_context,
    )


@router.post("/generate-image", summary="Generate a platform-optimized AI image")
async def generate_ai_image(
    payload: ImageGenerateRequest,
    tenant: TenantContext = Depends(require_permission("content.create")),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Generate an AI image using the configured image provider (DALL-E 3, FLUX, Stable Diffusion).
    Supports multiple aspect ratios for platform optimization.
    """
    ai_svc = AIService(db)
    return await ai_svc.generate_creative_image(
        prompt=payload.prompt,
        org=tenant.organisation,
        user=tenant.user,
        style=payload.style,
        aspect_ratio=payload.aspect_ratio,
    )

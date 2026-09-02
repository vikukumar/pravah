from typing import Any, Dict, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import TenantContext, get_tenant_context, require_permission
from app.core.database import get_db
from app.schemas.ai import (
    AIGenerateImageRequest,
    AIGenerateImageResponse,
    AIGenerateTextRequest,
    AIGenerateTextResponse,
    AIProviderResponse,
    AIUsageResponse,
)
from app.schemas.content import BestTimeRecommendationResponse
from app.services.ai_service import AIService
from app.services.best_time_engine import BestTimeEngine

router = APIRouter()

@router.post("/generate-text", response_model=AIGenerateTextResponse)
async def generate_text(
    payload: AIGenerateTextRequest,
    tenant: TenantContext = Depends(require_permission("ai.generate_text")),
    db: AsyncSession = Depends(get_db)
):
    ai_svc = AIService(db)
    result = await ai_svc.generate_social_content(
        org_id=tenant.organisation.id,
        user=tenant.user,
        topic=payload.topic,
        platform=payload.platform,
        tone=payload.tone or "professional",
        objective=payload.objective or "engagement",
        language=payload.language,
        keywords=payload.keywords,
        hashtags=payload.hashtags,
        cta=payload.cta,
        max_length=payload.max_length,
        provider_id=payload.provider_id,
        model_name=payload.model_name,
        include_emojis=payload.include_emojis,
    )
    return AIGenerateTextResponse(**result)

@router.post("/generate-image", response_model=AIGenerateImageResponse)
async def generate_image(
    payload: AIGenerateImageRequest,
    tenant: TenantContext = Depends(require_permission("ai.generate_image")),
    db: AsyncSession = Depends(get_db)
):
    ai_svc = AIService(db)
    result = await ai_svc.generate_image_asset(
        org_id=tenant.organisation.id,
        user=tenant.user,
        prompt=payload.prompt,
        aspect_ratio=payload.aspect_ratio,
        style=payload.style or "photorealistic",
    )
    return AIGenerateImageResponse(**result)

@router.get("/recommend-best-time", response_model=BestTimeRecommendationResponse)
async def recommend_best_time(
    platform: str = Query("x"),
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    engine = BestTimeEngine(db)
    result = await engine.get_recommendation(
        org_id=tenant.organisation.id,
        platform=platform,
    )
    return BestTimeRecommendationResponse(**result)

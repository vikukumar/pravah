from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.api.deps import get_current_active_super_admin
from app.core.database import get_db
from app.models.cms import CMSBlock, CMSPage, Form, Menu, SEOConfiguration
from app.models.user import User
from app.schemas.cms import (
    CMSBlockSchema,
    CMSPageCreate,
    CMSPageResponse,
    CMSPageUpdate,
    FormResponse,
    FormSubmitRequest,
    MenuResponse,
    SEOSchema,
)
from app.services.cms_service import CMSService

router = APIRouter()

@router.get("/pages/{slug}", response_model=CMSPageResponse)
async def get_cms_page(slug: str, db: AsyncSession = Depends(get_db)):
    cms_svc = CMSService(db)
    page = await cms_svc.get_page_by_slug(slug)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    return CMSPageResponse(
        id=page.id,
        title=page.title,
        slug=page.slug,
        description=page.description,
        is_published=page.is_published,
        is_system=page.is_system,
        published_at=page.published_at,
        version=page.version,
        blocks=[
            CMSBlockSchema(
                id=b.id,
                block_type=b.block_type,
                name=b.name,
                content=b.content,
                display_order=b.display_order,
                is_visible=b.is_visible,
            )
            for b in page.blocks if b.is_visible
        ],
        seo=SEOSchema(
            meta_title=page.seo.meta_title,
            meta_description=page.seo.meta_description,
            keywords=page.seo.keywords,
            canonical_url=page.seo.canonical_url,
            og_image_url=page.seo.og_image_url,
            no_index=page.seo.no_index,
        ) if page.seo else None,
        created_at=page.created_at,
        updated_at=page.updated_at,
    )

@router.get("/menus/{location}", response_model=List[Dict[str, Any]])
async def get_menu(location: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Menu).where(Menu.location == location, Menu.is_active == True))
    menu = res.scalar_one_or_none()
    if not menu:
        return []
    return menu.items

@router.post("/forms/submit", status_code=status.HTTP_201_CREATED)
async def submit_form(
    payload: FormSubmitRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    cms_svc = CMSService(db)
    client_ip = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent", "Unknown")

    submission = await cms_svc.submit_form(
        form_name=payload.form_name,
        data=payload.data,
        ip_address=client_ip,
        user_agent=user_agent,
    )
    return {
        "message": "Form submitted successfully.",
        "submission_id": submission.id,
    }

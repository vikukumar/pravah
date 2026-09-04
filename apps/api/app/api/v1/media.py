import os
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import TenantContext, require_permission
from app.core.config import settings
from app.core.database import get_db
from app.models.content import ContentAsset

router = APIRouter()

ALLOWED_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml",
    "video/mp4", "video/webm", "video/quicktime",
}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@router.get("")
async def list_media(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    asset_type: Optional[str] = Query(None),
    tenant: TenantContext = Depends(require_permission("content.view")),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    """List media assets belonging to this organisation."""
    query = (
        select(ContentAsset)
        .where(ContentAsset.organisation_id == tenant.organisation.id)
        .order_by(ContentAsset.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if asset_type == "image":
        query = query.where(ContentAsset.mime_type.like("image/%"))
    elif asset_type == "video":
        query = query.where(ContentAsset.mime_type.like("video/%"))

    res = await db.execute(query)
    assets = res.scalars().all()

    return [
        {
            "id": a.id,
            "filename": a.original_filename,
            "file_url": a.file_url,
            "mime_type": a.mime_type,
            "file_size_bytes": a.file_size_bytes,
            "dimensions": a.dimensions,
            "is_ai_generated": a.is_ai_generated,
            "tags": a.tags or [],
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in assets
    ]


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_media(
    file: UploadFile = File(...),
    tenant: TenantContext = Depends(require_permission("content.create")),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Upload a media asset (image or video) for this organisation."""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {file.content_type}. Allowed: images and videos."
        )

    # Read file to check size
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is 100 MB."
        )

    # Save to local storage
    upload_dir = os.path.join(settings.STORAGE_LOCAL_PATH, "media", tenant.organisation.id)
    os.makedirs(upload_dir, exist_ok=True)

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in (file.filename or "") else "bin"
    safe_filename = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(upload_dir, safe_filename)

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # Build public URL (served via /uploads/ static mount or proxy)
    file_url = f"/uploads/media/{tenant.organisation.id}/{safe_filename}"

    # Detect image dimensions
    dimensions = None
    if file.content_type.startswith("image/"):
        try:
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(file_bytes))
            dimensions = f"{img.width}x{img.height}"
        except Exception:
            pass

    asset = ContentAsset(
        organisation_id=tenant.organisation.id,
        uploader_id=tenant.user.id,
        filename=safe_filename,
        original_filename=file.filename or safe_filename,
        file_path=file_path,
        file_url=file_url,
        mime_type=file.content_type,
        file_size_bytes=len(file_bytes),
        dimensions=dimensions,
        is_ai_generated=False,
        tags=[],
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)

    return {
        "id": asset.id,
        "filename": asset.original_filename,
        "file_url": asset.file_url,
        "mime_type": asset.mime_type,
        "file_size_bytes": asset.file_size_bytes,
        "dimensions": asset.dimensions,
        "is_ai_generated": False,
        "tags": [],
        "created_at": asset.created_at.isoformat() if asset.created_at else None,
    }


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_media(
    asset_id: str,
    tenant: TenantContext = Depends(require_permission("content.delete")),
    db: AsyncSession = Depends(get_db),
):
    """Delete a media asset."""
    res = await db.execute(
        select(ContentAsset).where(
            ContentAsset.id == asset_id,
            ContentAsset.organisation_id == tenant.organisation.id,
        )
    )
    asset = res.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found.")

    # Remove physical file if it exists in local storage
    try:
        if os.path.isfile(asset.file_path):
            os.remove(asset.file_path)
    except Exception:
        pass

    await db.delete(asset)
    await db.commit()

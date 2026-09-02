from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class CMSBlockSchema(BaseModel):
    id: Optional[str] = None
    block_type: str
    name: str
    content: Dict[str, Any]
    display_order: int = 0
    is_visible: bool = True

class SEOSchema(BaseModel):
    meta_title: str
    meta_description: str
    keywords: Optional[List[str]] = None
    canonical_url: Optional[str] = None
    og_image_url: Optional[str] = None
    no_index: bool = False

class CMSPageCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    blocks: List[CMSBlockSchema] = Field(default_factory=list)
    seo: Optional[SEOSchema] = None
    is_published: bool = False

class CMSPageUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    blocks: Optional[List[CMSBlockSchema]] = None
    seo: Optional[SEOSchema] = None
    is_published: Optional[bool] = None

class CMSPageResponse(BaseModel):
    id: str
    title: str
    slug: str
    description: Optional[str]
    is_published: bool
    is_system: bool
    published_at: Optional[datetime]
    version: int
    blocks: List[CMSBlockSchema] = Field(default_factory=list)
    seo: Optional[SEOSchema] = None
    created_at: datetime
    updated_at: datetime

class MenuCreate(BaseModel):
    name: str
    location: str
    items: List[Dict[str, Any]]
    is_active: bool = True

class MenuResponse(BaseModel):
    id: str
    name: str
    location: str
    items: List[Dict[str, Any]]
    is_active: bool

class FormSubmitRequest(BaseModel):
    form_name: str
    data: Dict[str, Any]

class FormResponse(BaseModel):
    id: str
    name: str
    title: str
    description: Optional[str]
    is_active: bool
    fields: List[Dict[str, Any]]
    submissions_count: int = 0

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

class AIGenerateTextRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    topic: str = Field(..., min_length=1)
    platform: str = "x" # x, facebook, instagram, linkedin, youtube
    tone: Optional[str] = "professional" # professional, casual, enthusiastic, humorous, bold
    objective: Optional[str] = "engagement" # engagement, sales, awareness, educational
    language: str = "en"
    keywords: Optional[List[str]] = None
    hashtags: Optional[List[str]] = None
    cta: Optional[str] = None
    max_length: Optional[int] = None
    provider_id: Optional[str] = None
    model_name: Optional[str] = None
    include_emojis: bool = True

class AIGenerateTextResponse(BaseModel):
    generated_text: str
    suggested_hashtags: List[str]
    suggested_cta: Optional[str]
    platform: str
    tokens_used: int
    provider: str
    model: str
    estimated_cost_usd: float

class AIGenerateImageRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    prompt: str = Field(..., min_length=1)
    aspect_ratio: str = "1:1" # 1:1, 16:9, 9:16, 4:5
    style: Optional[str] = "photorealistic" # photorealistic, minimal, digital_art, cinematic
    provider_id: Optional[str] = None
    model_name: Optional[str] = None

class AIGenerateImageResponse(BaseModel):
    image_url: str
    asset_id: str
    prompt: str
    provider: str
    model: str
    dimensions: str
    estimated_cost_usd: float

class AIProviderCreate(BaseModel):
    name: str
    provider_type: str = "openrouter" # openrouter, custom, openai, anthropic
    api_endpoint: Optional[str] = None
    api_key: str
    is_default: bool = False
    supports_text: bool = True
    supports_vision: bool = False
    supports_image: bool = False

class AIProviderResponse(BaseModel):
    id: str
    name: str
    provider_type: str
    api_endpoint: Optional[str]
    is_default: bool
    is_enabled: bool
    supports_text: bool
    supports_vision: bool
    supports_image: bool
    models_count: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AIUsageResponse(BaseModel):
    total_tokens: int
    total_images: int
    estimated_total_cost_usd: float
    usage_by_operation: Dict[str, Any]

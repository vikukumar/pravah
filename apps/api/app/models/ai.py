import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from app.core.database import BaseModel

class AIProvider(BaseModel):
    __tablename__ = "ai_providers"

    organisation_id = Column(String(36), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=True, index=True) # Null for platform default
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True) # Null if org/platform wide
    
    name = Column(String(100), nullable=False) # e.g. OpenRouter, OpenAI, Anthropic, Custom
    provider_type = Column(String(50), default="openrouter", nullable=False) # openrouter, custom, azure, etc.
    api_endpoint = Column(String(500), nullable=True)
    api_key_encrypted = Column(Text, nullable=True)
    
    is_default = Column(Boolean, default=False, nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    default_model = Column(String(200), nullable=True)  # e.g. "anthropic/claude-3.5-sonnet"
    
    # Capabilities
    supports_text = Column(Boolean, default=True, nullable=False)
    supports_vision = Column(Boolean, default=False, nullable=False)
    supports_image = Column(Boolean, default=False, nullable=False)
    supports_embeddings = Column(Boolean, default=False, nullable=False)

    models = relationship("AIModel", back_populates="provider", cascade="all, delete-orphan")

class AIModel(BaseModel):
    __tablename__ = "ai_models"

    provider_id = Column(String(36), ForeignKey("ai_providers.id", ondelete="CASCADE"), nullable=False, index=True)
    model_identifier = Column(String(100), nullable=False) # e.g. "openai/gpt-4o", "anthropic/claude-3.5-sonnet"
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    context_window = Column(Integer, default=8192, nullable=False)
    
    cost_per_1k_input_tokens = Column(Float, default=0.0, nullable=False)
    cost_per_1k_output_tokens = Column(Float, default=0.0, nullable=False)
    cost_per_image = Column(Float, default=0.0, nullable=False)
    
    is_active = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)

    provider = relationship("AIProvider", back_populates="models")

class AIUsage(BaseModel):
    __tablename__ = "ai_usages"

    organisation_id = Column(String(36), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    provider_id = Column(String(36), ForeignKey("ai_providers.id", ondelete="SET NULL"), nullable=True)
    model_name = Column(String(100), nullable=False)
    
    operation_type = Column(String(50), nullable=False) # text_generation, image_generation, profile_analysis, recommendation
    prompt_tokens = Column(Integer, default=0, nullable=False)
    completion_tokens = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    images_count = Column(Integer, default=0, nullable=False)
    estimated_cost_usd = Column(Float, default=0.0, nullable=False)
    
    status = Column(String(50), default="success", nullable=False) # success, error
    error_details = Column(Text, nullable=True)

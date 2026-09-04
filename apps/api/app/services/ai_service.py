import uuid
from typing import Any, Dict, List, Optional
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import PravahException
from app.models.ai import AIUsage
from app.models.content import ContentAsset
from app.models.organisation import Organisation
from app.models.user import User

PROVIDER_CATALOG = [
    {
        "id": "openrouter",
        "name": "OpenRouter (400+ Frontier AI Models)",
        "badge": "400+ Models",
        "default_uri": "https://openrouter.ai/api/v1",
        "doc_url": "https://openrouter.ai/keys",
        "description": "Unified gateway providing access to Claude 3.5 Sonnet, GPT-4o, Llama 3.3, Gemini 1.5, DeepSeek V3, and 400+ models with a single API key.",
        "models": [
            {"id": "anthropic/claude-3.5-sonnet", "name": "Claude 3.5 Sonnet", "type": "text", "tag": "Recommended"},
            {"id": "openai/gpt-4o", "name": "GPT-4o Omnimodal", "type": "text", "tag": "Flagship"},
            {"id": "meta-llama/llama-3.3-70b-instruct", "name": "Llama 3.3 70B Instruct", "type": "text", "tag": "Open Source"},
            {"id": "deepseek/deepseek-chat", "name": "DeepSeek V3 (Chat)", "type": "text", "tag": "High Performance"},
            {"id": "deepseek/deepseek-r1", "name": "DeepSeek R1 (Reasoning)", "type": "text", "tag": "Reasoning"},
            {"id": "google/gemini-pro-1.5", "name": "Gemini 1.5 Pro", "type": "text", "tag": "Multimodal"},
            {"id": "mistralai/mistral-large", "name": "Mistral Large 2411", "type": "text", "tag": "Enterprise"},
            {"id": "qwen/qwen-2.5-72b-instruct", "name": "Qwen 2.5 72B Instruct", "type": "text", "tag": "Fast"},
            {"id": "stabilityai/stable-diffusion-xl", "name": "Stable Diffusion XL 1.0", "type": "image", "tag": "Visual Asset"},
            {"id": "black-forest-labs/flux-1-schnell", "name": "FLUX.1 Schnell", "type": "image", "tag": "Photorealistic"},
        ],
    },
    {
        "id": "openai",
        "name": "OpenAI Direct API",
        "badge": "Official",
        "default_uri": "https://api.openai.com/v1",
        "doc_url": "https://platform.openai.com/api-keys",
        "description": "Direct official OpenAI developer API for GPT-4o, GPT-4o-mini, o1, and DALL-E 3 image generation.",
        "models": [
            {"id": "gpt-4o", "name": "GPT-4o", "type": "text", "tag": "Flagship"},
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "type": "text", "tag": "Fast & Low Cost"},
            {"id": "o1", "name": "OpenAI o1", "type": "text", "tag": "Advanced Reasoning"},
            {"id": "o3-mini", "name": "OpenAI o3-mini", "type": "text", "tag": "Speed & Logic"},
            {"id": "dall-e-3", "name": "DALL-E 3", "type": "image", "tag": "Image Generation"},
        ],
    },
    {
        "id": "anthropic",
        "name": "Anthropic Claude API",
        "badge": "Official",
        "default_uri": "https://api.anthropic.com/v1",
        "doc_url": "https://console.anthropic.com/settings/keys",
        "description": "Direct official Anthropic API for Claude 3.5 Sonnet, Claude 3.5 Haiku, and Claude 3 Opus.",
        "models": [
            {"id": "claude-3-5-sonnet-latest", "name": "Claude 3.5 Sonnet", "type": "text", "tag": "Creative Copy"},
            {"id": "claude-3-5-haiku-latest", "name": "Claude 3.5 Haiku", "type": "text", "tag": "High Velocity"},
            {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "type": "text", "tag": "Complex Strategy"},
        ],
    },
    {
        "id": "google",
        "name": "Google AI Studio (Gemini)",
        "badge": "Official",
        "default_uri": "https://generativelanguage.googleapis.com/v1beta/openai",
        "doc_url": "https://aistudio.google.com/app/apikey",
        "description": "Google Gemini 1.5 Pro, Flash, and 2.0 with ultra-long 1M+ token context windows.",
        "models": [
            {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "type": "text", "tag": "Long Context"},
            {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "type": "text", "tag": "Sub-Second"},
            {"id": "gemini-2.0-flash-exp", "name": "Gemini 2.0 Flash (Preview)", "type": "text", "tag": "Next-Gen"},
        ],
    },
    {
        "id": "groq",
        "name": "Groq LPU Inference",
        "badge": "Ultra-Fast",
        "default_uri": "https://api.groq.com/openai/v1",
        "doc_url": "https://console.groq.com/keys",
        "description": "LPU hardware acceleration delivering 500+ tokens/sec for Llama 3.3 and DeepSeek R1.",
        "models": [
            {"id": "llama-3.3-70b-versatile", "name": "Llama 3.3 70B Versatile", "type": "text", "tag": "Fastest"},
            {"id": "deepseek-r1-distill-llama-70b", "name": "DeepSeek R1 Distill 70B", "type": "text", "tag": "Reasoning"},
            {"id": "mixtral-8x7b-32768", "name": "Mixtral 8x7B", "type": "text", "tag": "Balanced"},
        ],
    },
    {
        "id": "deepseek",
        "name": "DeepSeek Direct API",
        "badge": "Cost-Efficient",
        "default_uri": "https://api.deepseek.com/v1",
        "doc_url": "https://platform.deepseek.com/api_keys",
        "description": "Direct DeepSeek V3 and DeepSeek R1 reasoning models with unmatched cost efficiency.",
        "models": [
            {"id": "deepseek-chat", "name": "DeepSeek-V3", "type": "text", "tag": "General Chat"},
            {"id": "deepseek-reasoner", "name": "DeepSeek-R1", "type": "text", "tag": "Deep Thinking"},
        ],
    },
    {
        "id": "mistral",
        "name": "Mistral AI Platform",
        "badge": "European AI",
        "default_uri": "https://api.mistral.ai/v1",
        "doc_url": "https://console.mistral.ai/api-keys/",
        "description": "Mistral Large 2, Pixtral vision models, and Codestral from Mistral AI.",
        "models": [
            {"id": "mistral-large-latest", "name": "Mistral Large", "type": "text", "tag": "Multilingual"},
            {"id": "pixtral-large-latest", "name": "Pixtral Large (Vision)", "type": "text", "tag": "Multimodal"},
            {"id": "mistral-small-latest", "name": "Mistral Small", "type": "text", "tag": "Lightweight"},
        ],
    },
    {
        "id": "together",
        "name": "Together AI",
        "badge": "Open Models",
        "default_uri": "https://api.together.xyz/v1",
        "doc_url": "https://api.together.xyz/settings/api-keys",
        "description": "Cloud hosting for open-source LLMs and FLUX image generation.",
        "models": [
            {"id": "meta-llama/Llama-3.3-70B-Instruct-Turbo", "name": "Llama 3.3 70B Turbo", "type": "text", "tag": "High Throughput"},
            {"id": "Qwen/Qwen2.5-72B-Instruct-Turbo", "name": "Qwen 2.5 72B Turbo", "type": "text", "tag": "Multilingual"},
            {"id": "black-forest-labs/FLUX.1-schnell", "name": "FLUX.1 Schnell", "type": "image", "tag": "Fast Images"},
        ],
    },
    {
        "id": "perplexity",
        "name": "Perplexity Online LLM",
        "badge": "Web Grounded",
        "default_uri": "https://api.perplexity.ai",
        "doc_url": "https://www.perplexity.ai/settings/api",
        "description": "Perplexity Sonar models with real-time web search citations and trend research.",
        "models": [
            {"id": "sonar-pro", "name": "Sonar Pro (Search)", "type": "text", "tag": "Live Web Data"},
            {"id": "sonar", "name": "Sonar Standard", "type": "text", "tag": "Fast Search"},
            {"id": "sonar-reasoning", "name": "Sonar Reasoning", "type": "text", "tag": "Web Research"},
        ],
    },
    {
        "id": "cohere",
        "name": "Cohere Command",
        "badge": "Enterprise",
        "default_uri": "https://api.cohere.com/v2",
        "doc_url": "https://dashboard.cohere.com/api-keys",
        "description": "Enterprise-grade Command R+ models optimized for RAG and business copywriting.",
        "models": [
            {"id": "command-r-plus", "name": "Command R+", "type": "text", "tag": "Enterprise"},
            {"id": "command-r", "name": "Command R", "type": "text", "tag": "Balanced"},
        ],
    },
    {
        "id": "custom",
        "name": "Custom / Self-Hosted Endpoint",
        "badge": "Self-Hosted",
        "default_uri": "http://localhost:11434/v1",
        "doc_url": "https://github.com/vllm-project/vllm",
        "description": "Connect any OpenAI-compatible inference server such as Ollama, vLLM, LocalAI, or private LLM clusters.",
        "models": [
            {"id": "custom-model", "name": "Custom Model (Specify below)", "type": "text", "tag": "Self-Hosted"},
        ],
    },
]

class AIService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def get_provider_catalog() -> List[Dict[str, Any]]:
        return PROVIDER_CATALOG

    async def test_provider_connection(self, provider_id: str, base_uri: str, api_key: str) -> Dict[str, Any]:
        """Tests live connectivity and credentials for any AI provider."""
        uri = base_uri.rstrip("/")
        test_url = f"{uri}/models"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        # Custom header for Anthropic if tested directly
        if provider_id == "anthropic":
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            }
            test_url = f"{uri}/messages"

        async with httpx.AsyncClient(timeout=8.0) as client:
            try:
                if provider_id == "anthropic":
                    # Minimal test ping for Anthropic
                    res = await client.post(
                        test_url,
                        headers=headers,
                        json={
                            "model": "claude-3-5-haiku-latest",
                            "max_tokens": 1,
                            "messages": [{"role": "user", "content": "ping"}],
                        },
                    )
                else:
                    res = await client.get(test_url, headers=headers)

                if res.status_code in (200, 201):
                    return {
                        "status": "success",
                        "status_code": res.status_code,
                        "message": f"Successfully connected to {provider_id.upper()} endpoint.",
                    }
                elif res.status_code == 401 or res.status_code == 403:
                    return {
                        "status": "error",
                        "status_code": res.status_code,
                        "message": "Authentication failed. Please verify your API key.",
                    }
                else:
                    return {
                        "status": "warning",
                        "status_code": res.status_code,
                        "message": f"Endpoint responded with status {res.status_code}.",
                    }
            except httpx.ConnectError:
                return {
                    "status": "error",
                    "status_code": 0,
                    "message": f"Could not connect to {uri}. Check server host and port.",
                }
            except Exception as e:
                return {
                    "status": "error",
                    "status_code": 0,
                    "message": f"Connection test failed: {str(e)}",
                }

    async def generate_social_post(
        self,
        prompt: str,
        platforms: List[str],
        org: Organisation,
        user: User,
        model_override: Optional[str] = None,
        tone_override: Optional[str] = None,
        target_char_count: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Generates brand-voice aligned social copy using OpenRouter or active provider."""
        brand_voice = ""
        brand_tone = tone_override or "engaging and professional"
        keywords = []

        if org.brand_identity:
            brand_voice = org.brand_identity.get("brand_voice", "")
            brand_tone = tone_override or org.brand_identity.get("tone", brand_tone)
            keywords = org.brand_identity.get("keywords", [])

        platform_str = ", ".join([p.upper() for p in platforms])

        system_prompt = (
            f"You are the senior AI social media director for {org.name}.\n"
            f"Brand Tone: {brand_tone}\n"
            f"Brand Guidelines: {brand_voice}\n"
            f"Core Keywords: {', '.join(keywords) if keywords else 'N/A'}\n"
            f"Target Platforms: {platform_str}\n\n"
            "Format your response as clean, high-impact social media posts tailored to each platform. "
            "Include engaging hooks, structured body paragraphs, call-to-action, and relevant hashtags."
        )

        from app.services.provider_resolver import ProviderResolver
        resolver = ProviderResolver(self.db)
        provider = await resolver.resolve(
            capability="text",
            org_id=org.id,
            model_override=model_override,
        )

        # Call AI Provider endpoint — no fake fallback
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{provider.base_uri.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {provider.api_key}",
                    "HTTP-Referer": "https://pravah.app",
                    "X-Title": "PRAVAH Social AI",
                    "Content-Type": "application/json",
                },
                json={
                    "model": provider.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1200,
                },
            )

        if resp.status_code == 200:
            data = resp.json()
            generated_content = data["choices"][0]["message"]["content"]
            tokens_used = data.get("usage", {}).get("total_tokens", 0)
            cost = tokens_used * 0.000003

            # Record usage meter
            usage_record = AIUsage(
                organisation_id=org.id,
                user_id=user.id,
                model=provider.model,
                prompt_tokens=data.get("usage", {}).get("prompt_tokens", 0),
                completion_tokens=data.get("usage", {}).get("completion_tokens", 0),
                total_tokens=tokens_used,
                cost_usd=cost,
            )
            self.db.add(usage_record)
            await self.db.commit()

            return {
                "content": generated_content,
                "model": provider.model,
                "tokens_used": tokens_used,
                "platforms": platforms,
            }
        elif resp.status_code == 401:
            raise PravahException(
                detail="AI provider authentication failed. Please check your API key in Admin → AI Providers.",
                error_code="AI_AUTH_ERROR"
            )
        elif resp.status_code == 429:
            raise PravahException(
                detail="AI provider rate limit exceeded. Please try again shortly.",
                error_code="AI_RATE_LIMITED"
            )
        else:
            raise PravahException(
                detail=f"AI provider returned error {resp.status_code}: {resp.text[:300]}",
                error_code="AI_API_ERROR"
            )

    async def generate_creative_image(
        self,
        prompt: str,
        org: Organisation,
        user: User,
        style: str = "photorealistic",
        aspect_ratio: str = "1:1",
    ) -> Dict[str, Any]:
        """Generates AI creative visual assets using the configured image provider."""
        from app.services.provider_resolver import ProviderResolver
        resolver = ProviderResolver(self.db)

        try:
            provider = await resolver.resolve(
                capability="image",
                org_id=org.id,
                model_override=None,
            )
        except Exception:
            raise PravahException(
                detail="No image generation provider is configured. Configure an AI provider with image capability in Admin → AI Providers.",
                error_code="IMAGE_PROVIDER_NOT_CONFIGURED"
            )

        # Build enriched image prompt with style direction
        enriched_prompt = f"{prompt}. Style: {style}. Brand context: {org.name}."
        if aspect_ratio == "16:9":
            enriched_prompt += " Landscape orientation, widescreen."
        elif aspect_ratio == "9:16":
            enriched_prompt += " Portrait orientation, mobile-first."

        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(
                f"{provider.base_uri.rstrip('/')}/images/generations",
                headers={
                    "Authorization": f"Bearer {provider.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": provider.model,
                    "prompt": enriched_prompt,
                    "n": 1,
                    "size": "1024x1024" if aspect_ratio == "1:1" else "1792x1024",
                    "response_format": "url",
                },
            )

        if resp.status_code != 200:
            raise PravahException(
                detail=f"Image generation failed ({resp.status_code}): {resp.text[:200]}",
                error_code="IMAGE_GEN_ERROR"
            )

        data = resp.json()
        image_url = data.get("data", [{}])[0].get("url", "")
        if not image_url:
            raise PravahException(
                detail="Image generation succeeded but provider returned no URL.",
                error_code="IMAGE_GEN_NO_URL"
            )

        # Record generated asset in database with real URL
        asset = ContentAsset(
            organisation_id=org.id,
            uploader_id=user.id,
            filename=f"ai_gen_{uuid.uuid4().hex[:8]}.png",
            original_filename=f"{prompt[:40].strip()}.png",
            file_path=f"uploads/generated/{uuid.uuid4().hex[:8]}.png",
            file_url=image_url,
            mime_type="image/png",
            file_size_bytes=0,
            dimensions="1024x1024" if aspect_ratio == "1:1" else "1792x1024",
            is_ai_generated=True,
            prompt=prompt,
            tags=["ai_generated", style, aspect_ratio],
        )
        self.db.add(asset)
        await self.db.commit()

        return {
            "asset_id": asset.id,
            "url": image_url,
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "style": style,
            "model": provider.model,
        }

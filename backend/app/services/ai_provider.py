"""
Abstract AI provider interface and concrete implementations:
- BackboardProvider: Uses backboard-sdk with open-weight models via OpenRouter
- OllamaProvider: Local inference via Ollama REST API
- MockProvider: Deterministic synthetic responses for demos and tests
"""
import json
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple

import httpx

from ..core.config import settings
from ..models.schemas import ProductInput

logger = logging.getLogger("sellerboost.ai")


class AIProvider(ABC):
    """Abstract base for all AI inference providers."""

    @abstractmethod
    async def generate(self, system_prompt: str, user_prompt: str, thread_id: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Send a prompt and return (response_text, metadata_dict).
        metadata_dict should include: provider, model, thread_id, input_tokens, output_tokens, total_tokens, estimated_cost_usd, latency_ms
        """
        ...

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Return provider health status."""
        ...


class BackboardProvider(AIProvider):
    """Backboard.io provider using backboard-sdk with open-weight models."""

    def __init__(self):
        self.api_key = settings.BACKBOARD_API_KEY
        self.base_url = settings.BACKBOARD_BASE_URL
        self.default_provider = settings.BACKBOARD_DEFAULT_PROVIDER
        self.default_model = settings.BACKBOARD_DEFAULT_MODEL
        self.multilingual_model = settings.BACKBOARD_MULTILINGUAL_MODEL
        self._client = None
        self._assistant_id = None

    async def _get_client(self):
        if self._client is None:
            from backboard import BackboardClient
            self._client = BackboardClient(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=120
            )
        return self._client

    async def generate(self, system_prompt: str, user_prompt: str, thread_id: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        client = await self._get_client()
        start = time.time()

        kwargs: Dict[str, Any] = {
            "content": user_prompt,
            "system_prompt": system_prompt,
            "llm_provider": self.default_provider,
            "model_name": self.default_model,
            "stream": False,
            "json_output": True,
            "memory": "off",
        }

        if thread_id:
            kwargs["thread_id"] = thread_id

        response = await client.send_message(**kwargs)
        latency = (time.time() - start) * 1000

        # Extract content from response
        content = ""
        input_tokens = 0
        output_tokens = 0
        resp_thread_id = thread_id

        if hasattr(response, "messages") and response.messages:
            # ChatMessagesResponse
            for msg in response.messages:
                if isinstance(msg, dict):
                    role_val = msg.get("role")
                    if hasattr(role_val, "value"):
                        role_val = role_val.value
                    if role_val == "assistant":
                        content = msg.get("content") or ""
                        input_tokens = msg.get("input_tokens") or 0
                        output_tokens = msg.get("output_tokens") or 0
                        resp_thread_id = str(msg.get("thread_id")) if msg.get("thread_id") else thread_id
                        break
                else:
                    role_val = getattr(msg, "role", None)
                    if hasattr(role_val, "value"):
                        role_val = role_val.value
                    if role_val == "assistant":
                        content = getattr(msg, "content", "") or ""
                        input_tokens = getattr(msg, "input_tokens", 0) or 0
                        output_tokens = getattr(msg, "output_tokens", 0) or 0
                        resp_thread_id = str(getattr(msg, "thread_id", None)) if getattr(msg, "thread_id", None) else thread_id
                        break
        elif hasattr(response, "content"):
            content = response.content or ""
            input_tokens = getattr(response, "input_tokens", 0) or 0
            output_tokens = getattr(response, "output_tokens", 0) or 0
            resp_thread_id = str(getattr(response, "thread_id", thread_id)) or thread_id

        if not content and hasattr(response, "content") and response.content:
            content = response.content

        total_tokens = input_tokens + output_tokens
        cost = (input_tokens * settings.INPUT_COST_PER_MILLION + output_tokens * settings.OUTPUT_COST_PER_MILLION) / 1_000_000

        metadata = {
            "provider": f"backboard/{self.default_provider}",
            "model": self.default_model,
            "thread_id": resp_thread_id,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_usd": round(cost, 8),
            "latency_ms": round(latency, 1),
        }

        return content, metadata

    async def health_check(self) -> Dict[str, Any]:
        try:
            client = await self._get_client()
            # Try a minimal request
            response = await client.send_message(
                content="Reply with just: OK",
                llm_provider=self.default_provider,
                model_name=self.default_model,
                stream=False,
                memory="off",
            )
            return {"status": "healthy", "model": self.default_model, "provider": f"backboard/{self.default_provider}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None


class OllamaProvider(AIProvider):
    """Local Ollama provider for fully offline inference."""

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_DEFAULT_MODEL

    async def generate(self, system_prompt: str, user_prompt: str, thread_id: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        start = time.time()

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.7,
                "num_predict": 4096,
            },
        }

        async with httpx.AsyncClient(timeout=180) as client:
            resp = await client.post(f"{self.base_url}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()

        latency = (time.time() - start) * 1000
        content = data.get("message", {}).get("content", "")
        prompt_tokens = data.get("prompt_eval_count", 0)
        completion_tokens = data.get("eval_count", 0)

        metadata = {
            "provider": "ollama",
            "model": self.model,
            "thread_id": None,
            "input_tokens": prompt_tokens,
            "output_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "estimated_cost_usd": 0.0,
            "latency_ms": round(latency, 1),
        }

        return content, metadata

    async def health_check(self) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                resp.raise_for_status()
                models = [m["name"] for m in resp.json().get("models", [])]
                available = self.model in models or any(self.model.split(":")[0] in m for m in models)
                return {
                    "status": "healthy" if available else "degraded",
                    "model": self.model,
                    "available_models": models[:10],
                }
        except Exception as e:
            return {"status": "error", "error": str(e)}


# ---------------------------------------------------------------------------
# Synthetic sample data for demo / mock mode
# ---------------------------------------------------------------------------
SAMPLE_PRODUCTS = {
    "handmade_soy_candle": {
        "name": "Lavender Dreams Hand-Poured Soy Candle",
        "category": "Home & Living",
        "features": ["hand-poured", "100% natural soy wax", "cotton wick", "lavender essential oil", "40-hour burn time"],
        "materials": "Natural soy wax, cotton wick, lavender essential oil blend",
        "target_customer": "Home decor enthusiasts, gift shoppers, aromatherapy lovers",
        "platform": "etsy",
        "tone": "artisanal",
        "language": "en",
        "brand": "Willow & Bloom",
        "price": 24.99,
    },
    "organic_cotton_tote": {
        "name": "Organic Cotton Canvas Tote Bag",
        "category": "Bags & Purses",
        "features": ["GOTS certified organic cotton", "reinforced stitching", "interior pocket", "screen-printed design", "reusable"],
        "materials": "100% GOTS certified organic cotton canvas, water-based ink",
        "target_customer": "Eco-conscious shoppers, students, everyday carry enthusiasts",
        "platform": "shopify",
        "tone": "friendly",
        "language": "en",
        "brand": "EarthThread Co.",
        "price": 18.50,
    },
    "ceramic_mug": {
        "name": "Artisan Stoneware Coffee Mug",
        "category": "Kitchen & Dining",
        "features": ["handmade stoneware", "food-safe glaze", "microwave safe", "dishwasher safe", "12 oz capacity"],
        "materials": "High-fire stoneware clay, lead-free food-safe glaze",
        "target_customer": "Coffee lovers, pottery enthusiasts, gift buyers",
        "platform": "etsy",
        "tone": "artisanal",
        "language": "en",
        "brand": "Kiln & Stone",
        "price": 32.00,
    },
    "minimalist_pendant": {
        "name": "Minimalist Gold Disc Pendant Necklace",
        "category": "Jewelry",
        "features": ["14k gold-filled", "hammered texture", "adjustable chain 16-18 inches", "hypoallergenic", "tarnish-resistant"],
        "materials": "14k gold-filled disc, 14k gold-filled cable chain",
        "target_customer": "Women who love minimalist jewelry, gift givers, bridesmaids",
        "platform": "amazon",
        "tone": "premium",
        "language": "en",
        "brand": "Luma Fine",
        "price": 42.00,
    },
    "wool_throw_blanket": {
        "name": "Merino Wool Herringbone Throw Blanket",
        "category": "Home & Living",
        "features": ["100% merino wool", "herringbone weave", "fringe edges", "50x60 inches", "naturally temperature-regulating"],
        "materials": "100% Australian merino wool",
        "target_customer": "Interior design enthusiasts, cozy home lovers, luxury gift shoppers",
        "platform": "shopify",
        "tone": "premium",
        "language": "en",
        "brand": "Highland Weave",
        "price": 89.00,
    },
}


def _generate_mock_listing(product: ProductInput) -> Dict[str, Any]:
    """Generate deterministic mock listing data without any API call."""
    name = product.name
    cat = product.category
    feats = product.features or ["quality craftsmanship"]
    mat = product.materials or "premium materials"
    brand = product.brand or "Artisan Studio"
    plat = product.platform
    tone = product.tone

    return {
        "titles": [
            {"title": f"{name} - {cat} | Handcrafted {feats[0].title()} | {brand}", "char_count": 80, "focus": "Keyword Rich & Search Optimized"},
            {"title": f"Meet the {name}: Where {feats[0].title()} Meets Everyday Beauty", "char_count": 70, "focus": "Artisanal & Storytelling"},
            {"title": f"{name} by {brand}", "char_count": 35, "focus": "Punchy & Concise"},
        ],
        "description": f"Introducing the {name} by {brand} — a carefully crafted piece from our {cat} collection. Made with {mat}, each piece showcases {', '.join(feats[:3])}. Designed for {product.target_customer or 'discerning buyers'} who appreciate quality and attention to detail. This {tone} piece brings together form and function, making it an ideal choice for personal use or as a thoughtful gift. Every detail has been considered to ensure lasting satisfaction.",
        "short_description": f"The {name} combines {feats[0]} with timeless design. Crafted by {brand} for those who value quality.",
        "benefits": [
            f"Crafted with {mat} for lasting quality",
            f"Features {feats[0]} for superior performance",
            f"Perfect for {product.target_customer or 'everyday use'}",
            f"Designed with {tone} aesthetics in mind",
            f"Makes an exceptional gift choice"
        ],
        "keywords": [name.lower(), cat.lower(), brand.lower(), feats[0].lower(), mat.split(",")[0].lower().strip(),
                     "handmade", "artisan", "gift idea", "unique", plat, tone, "quality", "crafted", "shop small", "handcrafted"],
        "tags": [name.split()[0].lower(), cat.split()[0].lower(), "handmade", "artisan", brand.split()[0].lower(),
                 feats[0].split()[0].lower(), "gift", "unique", plat, tone, "crafted", "quality", "shop-small"],
        "call_to_action": f"Add the {name} to your collection today — order now and experience {brand} quality!",
        "platform_presets": {
            "etsy": {
                "title": f"{name} | {feats[0].title()} {cat} | {brand}",
                "tags_13": [name.split()[0].lower(), cat.split()[0].lower(), "handmade", "artisan", brand.split()[0].lower(),
                            feats[0].split()[0].lower(), "gift", "unique", plat, tone, "crafted", "quality", "shop-small"],
                "materials": [m.strip() for m in mat.split(",")[:3]],
                "description": f"✨ {name} by {brand}\n\nLovingly crafted with {mat}. Each piece features {', '.join(feats[:3])}.\n\nPerfect for {product.target_customer or 'anyone who appreciates quality'}.\n\n🎁 Makes a wonderful gift!"
            },
            "amazon": {
                "title": f"{name} - {cat} | {feats[0].title()} | {brand} | Premium {cat}",
                "bullet_points": [
                    f"PREMIUM MATERIALS - Made with {mat} for exceptional quality and durability",
                    f"EXPERT CRAFTSMANSHIP - Features {feats[0]} ensuring superior performance",
                    f"PERFECT GIFT - Ideal for {product.target_customer or 'any occasion'}",
                    f"VERSATILE DESIGN - {tone.title()} aesthetic fits any style",
                    f"BRAND QUALITY - {brand} stands behind every product with attention to detail"
                ],
                "product_description": f"The {name} by {brand} represents the finest in {cat}. Crafted with {mat}, this piece embodies {tone} design principles.",
                "search_terms": [name.lower(), cat.lower(), feats[0].lower(), brand.lower(), "handmade"]
            },
            "shopify": {
                "page_title": f"{name} | {brand} - Premium {cat}",
                "meta_description": f"Discover the {name} by {brand}. Made with {mat}. Shop {tone} {cat} designed for quality.",
                "headline": f"The {name}",
                "body_html_text": f"Elevate your everyday with the {name}. Crafted by {brand} using {mat}, this piece is designed for those who appreciate {feats[0]}.",
                "feature_highlights": [f"Made with {mat}", f"Features {feats[0]}", f"Designed for {product.target_customer or 'quality seekers'}"],
                "call_to_action": "Add to Cart"
            },
            "ebay": {
                "title": f"{name} - {brand} {cat}",
                "item_specifics": {"Brand": brand, "Material": mat.split(",")[0].strip(), "Type": cat, "Style": tone.title()},
                "formatted_description": f"{name} by {brand}. Crafted with {mat}. Features: {', '.join(feats[:3])}."
            },
            "instagram": {
                "caption": f"✨ Meet the {name} by {brand} ✨\n\nCrafted with love using {mat}. Perfect for {product.target_customer or 'you'}! 💝\n\n👇 Link in bio to shop",
                "hook": f"This {name} is a game-changer 👀",
                "hashtags": [f"#{name.replace(' ', '')}", f"#{brand.replace(' ', '')}", f"#{cat.replace(' & ', '').replace(' ', '')}", "#Handmade", "#ShopSmall",
                             "#SupportSmallBusiness", "#Artisan", "#GiftIdea", f"#{tone.title()}", "#Crafted"],
                "call_to_action": "🔗 Link in bio — shop now!"
            }
        },
        "social_content": {
            "launch_post": f"🚀 NEW DROP: {name} by {brand}!\n\nWe're so excited to introduce our latest creation. Made with {mat} and designed with {tone} aesthetics. Available now!",
            "instagram_caption": f"✨ {name} ✨\nCrafted with {mat} by {brand}\n💝 Perfect gift idea\n\n#ShopSmall #Handmade #Artisan",
            "tiktok_reel_hook": f"Wait until you see this {name}... 👀",
            "hashtags": ["#NewDrop", "#ShopSmall", "#Handmade", f"#{brand.replace(' ', '')}", "#Artisan",
                         "#GiftIdea", "#SmallBusiness", f"#{cat.replace(' & ', '').replace(' ', '')}",
                         "#Crafted", f"#{tone.title()}", "#MadeWithLove", "#SupportSmall", "#Unique", "#QualityCrafts", "#ShopLocal"],
            "call_to_action": f"Shop the {name} now — link in bio! 🛒"
        }
    }


class MockProvider(AIProvider):
    """Deterministic mock provider for demo mode and testing. Zero API cost."""

    async def generate(self, system_prompt: str, user_prompt: str, thread_id: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        start = time.time()

        # Try to extract product name from prompt for more realistic mock
        mock_data = None
        prompt_lower = user_prompt.lower()
        for key, sample in SAMPLE_PRODUCTS.items():
            if sample["name"].lower() in prompt_lower or key.replace("_", " ") in prompt_lower:
                mock_data = _generate_mock_listing(ProductInput(**sample))
                break

        if mock_data is None:
            # Generate a generic mock from any extractable product info
            mock_data = _generate_mock_listing(ProductInput(
                name="Sample Product",
                category="General",
                features=["quality craftsmanship", "attention to detail"],
                materials="premium materials",
                target_customer="discerning buyers",
                platform="etsy",
                tone="artisanal",
                language="en",
                brand="Demo Studio",
            ))

        content = json.dumps(mock_data)
        latency = (time.time() - start) * 1000

        metadata = {
            "provider": "mock",
            "model": "sellerboost-demo-v1",
            "thread_id": None,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "estimated_cost_usd": 0.0,
            "latency_ms": round(latency, 1),
        }
        return content, metadata

    async def health_check(self) -> Dict[str, Any]:
        return {"status": "demo_mode", "model": "sellerboost-demo-v1"}


def get_provider() -> AIProvider:
    """Factory: return the configured AI provider instance."""
    if settings.AI_PROVIDER == "backboard" and settings.BACKBOARD_API_KEY:
        return BackboardProvider()
    elif settings.AI_PROVIDER == "ollama":
        return OllamaProvider()
    else:
        # Fallback to mock if no API key or explicitly set to mock
        if settings.AI_PROVIDER == "backboard" and not settings.BACKBOARD_API_KEY:
            logger.warning("BACKBOARD_API_KEY not set — falling back to demo mode. Set BACKBOARD_API_KEY in .env for live inference.")
        return MockProvider()

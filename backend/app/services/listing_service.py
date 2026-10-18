"""
Core listing generation service — orchestrates prompts, AI provider, response parsing, and quality audit.
"""
import json
import logging
from typing import Optional

from ..models.schemas import (
    ProductInput, ListingOutput, RefineRequest,
    TitleAlternative, PlatformPresets,
    EtsyPreset, AmazonPreset, ShopifyPreset, EbayPreset, InstagramPreset,
    SocialContent, QualityReport,
)
from .ai_provider import get_provider, AIProvider, _generate_mock_listing
from .prompts import SYSTEM_PROMPT, build_listing_prompt, build_refinement_prompt, build_product_summary
from .quality_auditor import audit_listing
from ..database.db import record_usage

logger = logging.getLogger("sellerboost.listing")


def _parse_listing_json(raw: str) -> dict:
    """Parse AI response into listing dict, handling common formatting issues."""
    text = raw.strip()

    # Remove markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last lines if they are fences
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON object within the text
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse AI response as JSON. Response starts with: {text[:200]}")


def _build_listing_output(data: dict, provider: str, model: str, tokens: dict, thread_id: Optional[str] = None) -> ListingOutput:
    """Convert parsed JSON dict into validated ListingOutput."""
    # Build title alternatives
    titles = []
    for t in data.get("titles", []):
        title_text = t.get("title", "")
        titles.append(TitleAlternative(
            title=title_text,
            char_count=t.get("char_count", len(title_text)),
            focus=t.get("focus", "General"),
        ))
    if not titles:
        titles = [TitleAlternative(title="Untitled Product", char_count=17, focus="Fallback")]

    # Build platform presets
    pp = data.get("platform_presets", {})

    etsy_data = pp.get("etsy", {})
    etsy = EtsyPreset(
        title=etsy_data.get("title", titles[0].title),
        tags_13=etsy_data.get("tags_13", data.get("tags", []))[:13],
        materials=etsy_data.get("materials", []),
        description=etsy_data.get("description", data.get("description", "")),
    )

    amz_data = pp.get("amazon", {})
    amazon = AmazonPreset(
        title=amz_data.get("title", titles[0].title),
        bullet_points=amz_data.get("bullet_points", data.get("benefits", []))[:5],
        product_description=amz_data.get("product_description", data.get("description", "")),
        search_terms=amz_data.get("search_terms", data.get("keywords", []))[:5],
    )

    shop_data = pp.get("shopify", {})
    shopify = ShopifyPreset(
        page_title=shop_data.get("page_title", titles[0].title[:70]),
        meta_description=shop_data.get("meta_description", data.get("short_description", "")[:160]),
        headline=shop_data.get("headline", titles[0].title),
        body_html_text=shop_data.get("body_html_text", data.get("description", "")),
        feature_highlights=shop_data.get("feature_highlights", data.get("benefits", []))[:5],
        call_to_action=shop_data.get("call_to_action", "Shop Now"),
    )

    ebay_data = pp.get("ebay", {})
    ebay = EbayPreset(
        title=ebay_data.get("title", titles[0].title[:80]),
        item_specifics=ebay_data.get("item_specifics", {}),
        formatted_description=ebay_data.get("formatted_description", data.get("description", "")),
    )

    ig_data = pp.get("instagram", {})
    instagram = InstagramPreset(
        caption=ig_data.get("caption", ""),
        hook=ig_data.get("hook", ""),
        hashtags=ig_data.get("hashtags", []),
        call_to_action=ig_data.get("call_to_action", "Link in bio!"),
    )

    platform_presets = PlatformPresets(
        etsy=etsy, amazon=amazon, shopify=shopify, ebay=ebay, instagram=instagram
    )

    # Social content
    sc = data.get("social_content", {})
    social = SocialContent(
        launch_post=sc.get("launch_post", ""),
        instagram_caption=sc.get("instagram_caption", ""),
        tiktok_reel_hook=sc.get("tiktok_reel_hook", ""),
        hashtags=sc.get("hashtags", []),
        call_to_action=sc.get("call_to_action", ""),
    )

    return ListingOutput(
        titles=titles,
        description=data.get("description", ""),
        short_description=data.get("short_description", ""),
        benefits=data.get("benefits", []),
        keywords=data.get("keywords", []),
        tags=data.get("tags", []),
        call_to_action=data.get("call_to_action", ""),
        platform_presets=platform_presets,
        social_content=social,
        thread_id=thread_id,
        provider_used=provider,
        model_used=model,
        tokens_used=tokens,
        estimated_cost_usd=tokens.get("estimated_cost_usd", 0.0),
    )


async def generate_listing(product: ProductInput) -> ListingOutput:
    """Generate a full product listing using the configured AI provider."""
    provider = get_provider()

    user_prompt = build_listing_prompt(product)
    raw_response, metadata = await provider.generate(SYSTEM_PROMPT, user_prompt)

    # Record usage
    await record_usage(
        provider=metadata.get("provider", "unknown"),
        model=metadata.get("model", "unknown"),
        prompt_tokens=metadata.get("input_tokens", 0),
        completion_tokens=metadata.get("output_tokens", 0),
        cost_usd=metadata.get("estimated_cost_usd", 0.0),
    )

    # Parse response
    parsed = _parse_listing_json(raw_response)

    tokens = {
        "input_tokens": metadata.get("input_tokens", 0),
        "output_tokens": metadata.get("output_tokens", 0),
        "total_tokens": metadata.get("total_tokens", 0),
        "estimated_cost_usd": metadata.get("estimated_cost_usd", 0.0),
    }

    listing = _build_listing_output(
        parsed,
        provider=metadata.get("provider", "unknown"),
        model=metadata.get("model", "unknown"),
        tokens=tokens,
        thread_id=metadata.get("thread_id"),
    )

    # Run quality audit
    listing.quality_report = audit_listing(product, listing)

    return listing


async def refine_listing(request: RefineRequest) -> ListingOutput:
    """Refine an existing listing based on user's plain-language instruction."""
    provider = get_provider()

    original_json = request.original_listing.model_dump()
    # Remove non-content fields for cleaner context
    for key in ["quality_report", "tokens_used", "estimated_cost_usd", "provider_used", "model_used", "thread_id"]:
        original_json.pop(key, None)

    product_summary = build_product_summary(request.product_data)
    user_prompt = build_refinement_prompt(
        instruction=request.instruction,
        original_json_str=json.dumps(original_json, indent=2),
        product_summary=product_summary,
    )

    raw_response, metadata = await provider.generate(
        SYSTEM_PROMPT, user_prompt, thread_id=request.thread_id
    )

    await record_usage(
        provider=metadata.get("provider", "unknown"),
        model=metadata.get("model", "unknown"),
        prompt_tokens=metadata.get("input_tokens", 0),
        completion_tokens=metadata.get("output_tokens", 0),
        cost_usd=metadata.get("estimated_cost_usd", 0.0),
    )

    parsed = _parse_listing_json(raw_response)

    tokens = {
        "input_tokens": metadata.get("input_tokens", 0),
        "output_tokens": metadata.get("output_tokens", 0),
        "total_tokens": metadata.get("total_tokens", 0),
        "estimated_cost_usd": metadata.get("estimated_cost_usd", 0.0),
    }

    listing = _build_listing_output(
        parsed,
        provider=metadata.get("provider", "unknown"),
        model=metadata.get("model", "unknown"),
        tokens=tokens,
        thread_id=metadata.get("thread_id"),
    )

    listing.quality_report = audit_listing(request.product_data, listing)
    return listing

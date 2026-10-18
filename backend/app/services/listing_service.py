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


def _to_str(val, max_len: Optional[int] = None, default: str = "") -> str:
    """Safely coerce any value (str, dict, list, int, None) to string with optional truncation."""
    if val is None:
        s = default
    elif isinstance(val, str):
        s = val
    elif isinstance(val, dict):
        str_vals = [v for v in val.values() if isinstance(v, str)]
        s = str_vals[0] if str_vals else json.dumps(val)
    elif isinstance(val, list):
        s = ", ".join(str(x) for x in val if x)
    else:
        s = str(val)
    s = s.strip()
    return s[:max_len] if max_len is not None else s


def _to_list_of_str(val, max_items: Optional[int] = None) -> list[str]:
    """Safely coerce any value to a list of strings."""
    if isinstance(val, list):
        items = []
        for item in val:
            if isinstance(item, str):
                items.append(item.strip())
            elif isinstance(item, dict):
                str_vals = [v for v in item.values() if isinstance(v, str)]
                items.append(str_vals[0] if str_vals else json.dumps(item))
            elif item is not None:
                items.append(str(item).strip())
        res = [it for it in items if it]
    elif isinstance(val, str):
        res = [s.strip() for s in val.split("\n") if s.strip()] or [s.strip() for s in val.split(",") if s.strip()]
    elif isinstance(val, dict):
        res = [str(v).strip() for v in val.values() if v]
    else:
        res = []
    return res[:max_items] if max_items is not None else res


def _build_listing_output(data: dict, provider: str, model: str, tokens: dict, thread_id: Optional[str] = None) -> ListingOutput:
    """Convert parsed JSON dict into validated ListingOutput."""
    # Build title alternatives
    raw_titles = data.get("titles", [])
    titles: list[TitleAlternative] = []
    if isinstance(raw_titles, list):
        for t in raw_titles:
            if isinstance(t, dict):
                title_text = _to_str(t.get("title", ""))
                char_c = t.get("char_count")
                if not isinstance(char_c, (int, float)):
                    char_c = len(title_text)
                titles.append(TitleAlternative(
                    title=title_text,
                    char_count=int(char_c),
                    focus=_to_str(t.get("focus", "General")),
                ))
            elif isinstance(t, str):
                titles.append(TitleAlternative(
                    title=t,
                    char_count=len(t),
                    focus="General",
                ))
    if not titles:
        first_title = _to_str(data.get("title") or "Untitled Product")
        titles = [TitleAlternative(title=first_title, char_count=len(first_title), focus="Fallback")]

    primary_title = titles[0].title
    desc_str = _to_str(data.get("description", ""))
    short_desc_str = _to_str(data.get("short_description") or desc_str)

    # Build platform presets
    pp = data.get("platform_presets") if isinstance(data.get("platform_presets"), dict) else {}

    etsy_data = pp.get("etsy") if isinstance(pp.get("etsy"), dict) else {}
    etsy = EtsyPreset(
        title=_to_str(etsy_data.get("title") or primary_title),
        tags_13=_to_list_of_str(etsy_data.get("tags_13") or data.get("tags", []), max_items=13),
        materials=_to_list_of_str(etsy_data.get("materials", [])),
        description=_to_str(etsy_data.get("description") or desc_str),
    )

    amz_data = pp.get("amazon") if isinstance(pp.get("amazon"), dict) else {}
    amazon = AmazonPreset(
        title=_to_str(amz_data.get("title") or primary_title),
        bullet_points=_to_list_of_str(amz_data.get("bullet_points") or data.get("benefits", []), max_items=5),
        product_description=_to_str(amz_data.get("product_description") or desc_str),
        search_terms=_to_list_of_str(amz_data.get("search_terms") or data.get("keywords", []), max_items=5),
    )

    shop_data = pp.get("shopify") if isinstance(pp.get("shopify"), dict) else {}
    shopify = ShopifyPreset(
        page_title=_to_str(shop_data.get("page_title") or primary_title, max_len=70),
        meta_description=_to_str(shop_data.get("meta_description") or short_desc_str or desc_str, max_len=160),
        headline=_to_str(shop_data.get("headline") or primary_title),
        body_html_text=_to_str(shop_data.get("body_html_text") or desc_str),
        feature_highlights=_to_list_of_str(shop_data.get("feature_highlights") or data.get("benefits", []), max_items=5),
        call_to_action=_to_str(shop_data.get("call_to_action") or "Shop Now"),
    )

    ebay_data = pp.get("ebay") if isinstance(pp.get("ebay"), dict) else {}
    raw_item_specifics = ebay_data.get("item_specifics") if isinstance(ebay_data.get("item_specifics"), dict) else {}
    item_specifics = {str(k): _to_str(v) for k, v in raw_item_specifics.items()}
    ebay = EbayPreset(
        title=_to_str(ebay_data.get("title") or primary_title, max_len=80),
        item_specifics=item_specifics,
        formatted_description=_to_str(ebay_data.get("formatted_description") or desc_str),
    )

    ig_data = pp.get("instagram") if isinstance(pp.get("instagram"), dict) else {}
    instagram = InstagramPreset(
        caption=_to_str(ig_data.get("caption", "")),
        hook=_to_str(ig_data.get("hook", "")),
        hashtags=_to_list_of_str(ig_data.get("hashtags", [])),
        call_to_action=_to_str(ig_data.get("call_to_action") or "Link in bio!"),
    )

    platform_presets = PlatformPresets(
        etsy=etsy, amazon=amazon, shopify=shopify, ebay=ebay, instagram=instagram
    )

    # Social content
    sc = data.get("social_content") if isinstance(data.get("social_content"), dict) else {}
    social = SocialContent(
        launch_post=_to_str(sc.get("launch_post", "")),
        instagram_caption=_to_str(sc.get("instagram_caption", "")),
        tiktok_reel_hook=_to_str(sc.get("tiktok_reel_hook", "")),
        hashtags=_to_list_of_str(sc.get("hashtags", [])),
        call_to_action=_to_str(sc.get("call_to_action", "")),
    )

    return ListingOutput(
        titles=titles,
        description=desc_str,
        short_description=short_desc_str,
        benefits=_to_list_of_str(data.get("benefits", [])),
        keywords=_to_list_of_str(data.get("keywords", [])),
        tags=_to_list_of_str(data.get("tags", [])),
        call_to_action=_to_str(data.get("call_to_action", "")),
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

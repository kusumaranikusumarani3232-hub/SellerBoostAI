"""
Prompt engineering module for SellerBoost AI.
Generates structured system + user prompts for each listing generation task.
"""
from ..models.schemas import ProductInput

SYSTEM_PROMPT = """You are SellerBoost AI — a professional e-commerce listing copywriter.

RULES:
1. Generate ONLY factual content based on the product details provided.
2. NEVER invent certifications, medical claims, FDA approvals, health benefits, specific dimensions, weights, or guarantees that are NOT in the provided product data.
3. NEVER claim "best seller", "#1", "guaranteed results", or "miracle" unless explicitly stated in the product facts.
4. Output ONLY valid JSON matching the requested schema. No markdown fences, no explanations outside JSON.
5. Make copy compelling, search-optimized, and suited to the specified platform and tone.
6. If the language is not English, translate ALL generated content into that language while keeping JSON keys in English.
7. Keep titles within platform character limits: Etsy=140, Amazon=200, Shopify=70, eBay=80, Instagram=100, General=150.
8. Generate exactly 13 tags for Etsy (each ≤20 chars), 5 bullet points for Amazon.
9. Never add HTML tags unless specifically for the Shopify body field.
10. Use natural keyword placement — no keyword stuffing."""

def build_listing_prompt(product: ProductInput) -> str:
    """Build the user-facing prompt for full listing generation."""
    features_str = ", ".join(product.features) if product.features else "Not specified"
    
    prompt = f"""Generate a complete e-commerce product listing for the following product.

PRODUCT DATA:
- Name: {product.name}
- Category: {product.category}
- Key Features: {features_str}
- Materials: {product.materials or "Not specified"}
- Target Customer: {product.target_customer or "General audience"}
- Primary Platform: {product.platform}
- Tone: {product.tone}
- Output Language: {product.language}
- Brand: {product.brand or "Not specified"}
- Price: {product.price or "Not specified"}
- Dimensions: {product.dimensions or "Not specified"}
- Care Instructions: {product.care_instructions or "Not specified"}
- Custom Notes: {product.custom_notes or "None"}

OUTPUT FORMAT (respond with ONLY this JSON, no markdown):
{{
  "titles": [
    {{"title": "...", "char_count": <int>, "focus": "Keyword Rich & Search Optimized"}},
    {{"title": "...", "char_count": <int>, "focus": "Artisanal & Storytelling"}},
    {{"title": "...", "char_count": <int>, "focus": "Punchy & Concise"}}
  ],
  "description": "Detailed 150-250 word product description",
  "short_description": "One compelling 1-2 sentence elevator pitch",
  "benefits": ["benefit 1", "benefit 2", "benefit 3", "benefit 4", "benefit 5"],
  "keywords": ["keyword1", "keyword2", ... up to 15 relevant search keywords],
  "tags": ["tag1", "tag2", ... up to 13 marketplace tags],
  "call_to_action": "Compelling CTA sentence",
  "platform_presets": {{
    "etsy": {{
      "title": "Etsy-optimized title (≤140 chars)",
      "tags_13": ["tag1", ..., "tag13"],
      "materials": ["material1", "material2"],
      "description": "Storytelling Etsy description"
    }},
    "amazon": {{
      "title": "Amazon-optimized title (≤200 chars)",
      "bullet_points": ["BENEFIT - detail", "BENEFIT - detail", "BENEFIT - detail", "BENEFIT - detail", "BENEFIT - detail"],
      "product_description": "Amazon A+ style description",
      "search_terms": ["term1", "term2", "term3", "term4", "term5"]
    }},
    "shopify": {{
      "page_title": "SEO page title (≤70 chars)",
      "meta_description": "Meta description (≤160 chars)",
      "headline": "Hero headline",
      "body_html_text": "Product page body copy",
      "feature_highlights": ["highlight1", "highlight2", "highlight3"],
      "call_to_action": "Add to Cart CTA text"
    }},
    "ebay": {{
      "title": "eBay title (≤80 chars)",
      "item_specifics": {{"Brand": "...", "Material": "...", "Type": "..."}},
      "formatted_description": "eBay listing description"
    }},
    "instagram": {{
      "caption": "Engaging Instagram caption with emojis",
      "hook": "First line hook to stop scrolling",
      "hashtags": ["#hashtag1", "#hashtag2", ... up to 30],
      "call_to_action": "Link in bio / Shop now CTA"
    }}
  }},
  "social_content": {{
    "launch_post": "Product launch announcement post",
    "instagram_caption": "Instagram-ready caption with emojis",
    "tiktok_reel_hook": "3-second TikTok hook script",
    "hashtags": ["#hashtag1", "#hashtag2", ... up to 15],
    "call_to_action": "Social media CTA"
  }}
}}"""
    return prompt


def build_refinement_prompt(instruction: str, original_json_str: str, product_summary: str) -> str:
    """Build refinement prompt that preserves product facts."""
    return f"""You previously generated this product listing:

{original_json_str}

ORIGINAL PRODUCT FACTS (do NOT change these facts):
{product_summary}

USER REFINEMENT REQUEST:
{instruction}

Apply the user's request while keeping all product facts accurate. Output the complete updated listing in the same JSON format. Do NOT invent new product facts, certifications, or guarantees. Output ONLY valid JSON."""


def build_product_summary(product: ProductInput) -> str:
    """Build a concise product fact sheet for context anchoring."""
    parts = [f"Product: {product.name}", f"Category: {product.category}"]
    if product.features:
        parts.append(f"Features: {', '.join(product.features)}")
    if product.materials:
        parts.append(f"Materials: {product.materials}")
    if product.target_customer:
        parts.append(f"Target: {product.target_customer}")
    if product.brand:
        parts.append(f"Brand: {product.brand}")
    if product.price:
        parts.append(f"Price: {product.price}")
    if product.dimensions:
        parts.append(f"Dimensions: {product.dimensions}")
    if product.care_instructions:
        parts.append(f"Care: {product.care_instructions}")
    return "\n".join(parts)

from typing import List, Optional, Dict, Any, Literal, Union
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

class ProductInput(BaseModel):
    name: str = Field(..., min_length=2, max_length=200, description="Product title or item name")
    category: str = Field(default="Home & Living", description="Primary product category")
    features: List[str] = Field(default_factory=list, description="Key features, ingredients, or highlights")
    materials: Optional[str] = Field(default=None, description="Physical materials, ingredients, or craftsmanship details")
    target_customer: Optional[str] = Field(default=None, description="Ideal buyer persona or intended recipient")
    platform: Literal["etsy", "shopify", "amazon", "ebay", "instagram", "general"] = Field(
        default="etsy", description="Primary marketplace target preset"
    )
    tone: Literal["artisanal", "premium", "friendly", "concise", "bold", "professional"] = Field(
        default="artisanal", description="Brand copywriting voice"
    )
    language: str = Field(default="en", description="Target output language code or name (e.g., en, hi, es, fr, de, ja)")
    brand: Optional[str] = Field(default=None, description="Seller or brand store name")
    price: Optional[float] = Field(default=None, ge=0, description="Listing price in local currency")
    dimensions: Optional[str] = Field(default=None, description="Product dimensions or sizing info")
    care_instructions: Optional[str] = Field(default=None, description="Maintenance, washing, or usage care instructions")
    custom_notes: Optional[str] = Field(default=None, description="Special instructions or unique selling angle")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Product name cannot be empty")
        return trimmed

class TitleAlternative(BaseModel):
    title: str
    char_count: int
    focus: str = Field(description="Angle e.g. 'Keyword Rich & Search Optimized', 'Artisanal & Storytelling', 'Punchy & Concise'")

class EtsyPreset(BaseModel):
    title: str
    tags_13: List[str] = Field(description="Exact 13 tags within 20 chars each for Etsy tag slots")
    materials: List[str] = Field(default_factory=list)
    description: str

class AmazonPreset(BaseModel):
    title: str
    bullet_points: List[str] = Field(description="5 high-converting bullet points with benefit lead-ins")
    product_description: str
    search_terms: List[str]

class ShopifyPreset(BaseModel):
    page_title: str
    meta_description: str
    headline: str
    body_html_text: str
    feature_highlights: List[str]
    call_to_action: str

class EbayPreset(BaseModel):
    title: str
    item_specifics: Dict[str, str]
    formatted_description: str

class InstagramPreset(BaseModel):
    caption: str
    hook: str
    hashtags: List[str]
    call_to_action: str

class PlatformPresets(BaseModel):
    etsy: EtsyPreset
    amazon: AmazonPreset
    shopify: ShopifyPreset
    ebay: EbayPreset
    instagram: InstagramPreset

class SocialContent(BaseModel):
    launch_post: str
    instagram_caption: str
    tiktok_reel_hook: str
    hashtags: List[str]
    call_to_action: str

class QualityAuditItem(BaseModel):
    id: str
    category: Literal["title", "details", "compliance", "seo", "readability"]
    title: str
    passed: bool
    severity: Literal["info", "warning", "critical"]
    message: str
    suggestion: Optional[str] = None

class ReadabilityStats(BaseModel):
    word_count: int
    sentence_count: int
    avg_words_per_sentence: float
    reading_ease_score: float
    reading_level: str

class QualityReport(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    grade: str
    passed_checks: int
    total_checks: int
    items: List[QualityAuditItem]
    readability: ReadabilityStats
    compliance_notes: List[str]

class ListingOutput(BaseModel):
    titles: List[TitleAlternative]
    description: str
    short_description: str
    benefits: List[str]
    keywords: List[str]
    tags: List[str]
    call_to_action: str
    platform_presets: PlatformPresets
    social_content: SocialContent
    quality_report: Optional[QualityReport] = None
    thread_id: Optional[str] = None
    provider_used: str
    model_used: str
    tokens_used: Optional[Dict[str, Union[int, float]]] = None
    estimated_cost_usd: Optional[float] = None

class RefineRequest(BaseModel):
    original_listing: ListingOutput
    product_data: ProductInput
    instruction: str = Field(..., min_length=3, max_length=500, description="Plain-language refinement request")
    target_field: Optional[str] = Field(default="all", description="Field to refine: all, description, titles, social, tone")
    thread_id: Optional[str] = None

class SavedProductRecord(BaseModel):
    id: str
    product_data: ProductInput
    listing: Optional[ListingOutput] = None
    created_at: str
    updated_at: str

class ProductListResponse(BaseModel):
    total: int
    products: List[SavedProductRecord]

class BulkImportItem(BaseModel):
    row_number: int
    valid: bool
    errors: List[str] = Field(default_factory=list)
    product_data: Optional[ProductInput] = None
    raw_row: Dict[str, Any]

class BulkImportPreviewResponse(BaseModel):
    total_rows: int
    valid_rows: int
    invalid_rows: int
    items: List[BulkImportItem]

class BulkGenerateRequest(BaseModel):
    products: List[ProductInput]

class BulkGenerateItemResult(BaseModel):
    index: int
    product_name: str
    category: Optional[str] = None
    platform: Optional[str] = None
    status: Literal["success", "error"]
    error_message: Optional[str] = None
    listing: Optional[ListingOutput] = None

class BulkGenerateResponse(BaseModel):
    total: int
    succeeded: int
    failed: int
    results: List[BulkGenerateItemResult]

class ModelStatusResponse(BaseModel):
    provider: str
    active_model: str
    display_name: str
    license: str
    is_open_weight: bool
    context_limit: int
    pricing_per_1m_tokens: str
    promo_credit_initial_usd: float
    estimated_used_usd: float
    estimated_remaining_usd: float
    total_inferences: int
    latency_ms: Optional[float] = None
    health_status: Literal["healthy", "degraded", "demo_mode", "error"]
    notes: str

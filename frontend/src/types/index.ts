// API types matching backend Pydantic schemas

export type Platform = 'etsy' | 'shopify' | 'amazon' | 'ebay' | 'instagram' | 'general'
export type Tone = 'artisanal' | 'premium' | 'friendly' | 'concise' | 'bold' | 'professional'

export interface ProductInput {
  name: string
  category: string
  features: string[]
  materials?: string
  target_customer?: string
  platform: Platform
  tone: Tone
  language: string
  brand?: string
  price?: number
  dimensions?: string
  care_instructions?: string
  custom_notes?: string
}

export interface TitleAlternative {
  title: string
  char_count: number
  focus: string
}

export interface EtsyPreset {
  title: string
  tags_13: string[]
  materials: string[]
  description: string
}

export interface AmazonPreset {
  title: string
  bullet_points: string[]
  product_description: string
  search_terms: string[]
}

export interface ShopifyPreset {
  page_title: string
  meta_description: string
  headline: string
  body_html_text: string
  feature_highlights: string[]
  call_to_action: string
}

export interface EbayPreset {
  title: string
  item_specifics: Record<string, string>
  formatted_description: string
}

export interface InstagramPreset {
  caption: string
  hook: string
  hashtags: string[]
  call_to_action: string
}

export interface PlatformPresets {
  etsy: EtsyPreset
  amazon: AmazonPreset
  shopify: ShopifyPreset
  ebay: EbayPreset
  instagram: InstagramPreset
}

export interface SocialContent {
  launch_post: string
  instagram_caption: string
  tiktok_reel_hook: string
  hashtags: string[]
  call_to_action: string
}

export interface QualityAuditItem {
  id: string
  category: 'title' | 'details' | 'compliance' | 'seo' | 'readability'
  title: string
  passed: boolean
  severity: 'info' | 'warning' | 'critical'
  message: string
  suggestion?: string
}

export interface ReadabilityStats {
  word_count: number
  sentence_count: number
  avg_words_per_sentence: number
  reading_ease_score: number
  reading_level: string
}

export interface QualityReport {
  overall_score: number
  grade: string
  passed_checks: number
  total_checks: number
  items: QualityAuditItem[]
  readability: ReadabilityStats
  compliance_notes: string[]
}

export interface ListingOutput {
  titles: TitleAlternative[]
  description: string
  short_description: string
  benefits: string[]
  keywords: string[]
  tags: string[]
  call_to_action: string
  platform_presets: PlatformPresets
  social_content: SocialContent
  quality_report?: QualityReport
  thread_id?: string
  provider_used: string
  model_used: string
  tokens_used?: Record<string, number>
  estimated_cost_usd?: number
}

export interface RefineRequest {
  original_listing: ListingOutput
  product_data: ProductInput
  instruction: string
  target_field?: string
  thread_id?: string
}

export interface SavedProductRecord {
  id: string
  product_data: ProductInput
  listing?: ListingOutput
  created_at: string
  updated_at: string
}

export interface ProductListResponse {
  total: number
  products: SavedProductRecord[]
}

export interface BulkImportItem {
  row_number: number
  valid: boolean
  errors: string[]
  product_data?: ProductInput
  raw_row: Record<string, string>
}

export interface BulkImportPreviewResponse {
  total_rows: number
  valid_rows: number
  invalid_rows: number
  items: BulkImportItem[]
}

export interface BulkGenerateItemResult {
  index: number
  product_name: string
  category?: string
  platform?: string
  status: 'success' | 'error'
  error_message?: string
  listing?: ListingOutput
}

export interface BulkGenerateResponse {
  total: number
  succeeded: number
  failed: number
  results: BulkGenerateItemResult[]
}

export interface ModelStatusResponse {
  provider: string
  active_model: string
  display_name: string
  license: string
  is_open_weight: boolean
  context_limit: number
  pricing_per_1m_tokens: string
  promo_credit_initial_usd: number
  estimated_used_usd: number
  estimated_remaining_usd: number
  total_inferences: number
  latency_ms?: number
  health_status: 'healthy' | 'degraded' | 'demo_mode' | 'error'
  notes: string
}

export interface SampleProduct {
  id: string
  name: string
  category: string
  features: string[]
  materials: string
  target_customer: string
  platform: Platform
  tone: Tone
  language: string
  brand: string
  price: number
}

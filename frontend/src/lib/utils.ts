// Utility functions

export function copyToClipboard(text: string): Promise<void> {
  if (navigator.clipboard && window.isSecureContext) {
    return navigator.clipboard.writeText(text)
  }
  // Fallback
  const el = document.createElement('textarea')
  el.value = text
  el.style.position = 'fixed'
  el.style.opacity = '0'
  document.body.appendChild(el)
  el.select()
  document.execCommand('copy')
  document.body.removeChild(el)
  return Promise.resolve()
}

export function formatCurrency(amount: number, currency = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 6,
  }).format(amount)
}

export function formatDate(isoString: string): string {
  return new Date(isoString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function truncate(str: string, max: number): string {
  if (str.length <= max) return str
  return str.slice(0, max - 3) + '...'
}

export function clsx(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ')
}

export const PLATFORM_LABELS: Record<string, string> = {
  etsy: 'Etsy',
  shopify: 'Shopify',
  amazon: 'Amazon',
  ebay: 'eBay',
  instagram: 'Instagram',
  general: 'General',
}

export const PLATFORM_COLORS: Record<string, string> = {
  etsy: '#f1641e',
  shopify: '#96bf48',
  amazon: '#ff9900',
  ebay: '#e53238',
  instagram: '#e1306c',
  general: '#7c3aed',
}

export const TONE_LABELS: Record<string, string> = {
  artisanal: 'Artisanal & Handcrafted',
  premium: 'Premium & Luxury',
  friendly: 'Friendly & Warm',
  concise: 'Concise & Direct',
  bold: 'Bold & Confident',
  professional: 'Professional & Corporate',
}

export const CATEGORY_OPTIONS = [
  'Home & Living',
  'Jewelry',
  'Clothing & Accessories',
  'Art & Collectibles',
  'Craft Supplies & Tools',
  'Vintage',
  'Paper & Party Supplies',
  'Bags & Purses',
  'Shoes',
  'Toys & Games',
  'Beauty & Personal Care',
  'Kitchen & Dining',
  'Garden & Outdoor',
  'Baby & Toddler',
  'Pet Supplies',
  'Electronics',
  'Sports & Outdoors',
  'Books & Media',
  'General',
]

export const LANGUAGE_OPTIONS = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'Hindi' },
  { code: 'es', label: 'Spanish' },
  { code: 'fr', label: 'French' },
  { code: 'de', label: 'German' },
  { code: 'it', label: 'Italian' },
  { code: 'pt', label: 'Portuguese' },
  { code: 'ja', label: 'Japanese' },
  { code: 'zh', label: 'Chinese (Simplified)' },
  { code: 'ar', label: 'Arabic' },
  { code: 'ko', label: 'Korean' },
]

export function getScoreColor(score: number): string {
  if (score >= 85) return '#10b981'
  if (score >= 70) return '#3b82f6'
  if (score >= 55) return '#f59e0b'
  if (score >= 40) return '#f97316'
  return '#ef4444'
}

export function getSeverityColor(severity: string): string {
  switch (severity) {
    case 'critical': return '#ef4444'
    case 'warning': return '#f59e0b'
    default: return '#3b82f6'
  }
}

export function formatProvider(rawProvider?: string): string {
  if (!rawProvider) return 'Unknown'
  const p = rawProvider.toLowerCase().trim()
  if (p.includes('backboard')) {
    if (p.includes('openrouter')) {
      return 'Backboard (via OpenRouter)'
    }
    return 'Backboard'
  }
  if (p === 'ollama') return 'Ollama (Local)'
  if (p === 'mock') return 'Demo Mode'
  return rawProvider
}


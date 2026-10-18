import axios from 'axios'
import type {
  ProductInput, ListingOutput, RefineRequest,
  SavedProductRecord, ProductListResponse,
  BulkImportPreviewResponse, ModelStatusResponse, SampleProduct
} from '../types'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' },
})

// ── Model Status ─────────────────────────────────────────────────────────
export const getModelStatus = (): Promise<ModelStatusResponse> =>
  api.get('/model-status').then(r => r.data)

export const getHealth = () =>
  api.get('/health').then(r => r.data)

// ── Sample Products ───────────────────────────────────────────────────────
export const getSamples = (): Promise<{ samples: SampleProduct[] }> =>
  api.get('/samples').then(r => r.data)

// ── Listing Generation ────────────────────────────────────────────────────
export const generateListing = (product: ProductInput): Promise<ListingOutput> =>
  api.post('/generate', product).then(r => r.data)

export const refineListing = (request: RefineRequest): Promise<ListingOutput> =>
  api.post('/refine', request).then(r => r.data)

// ── Products CRUD ─────────────────────────────────────────────────────────
export const createProduct = (product: ProductInput): Promise<SavedProductRecord> =>
  api.post('/products', product).then(r => r.data)

export const saveProductWithListing = (product: ProductInput, listing?: ListingOutput): Promise<SavedProductRecord> =>
  api.post('/products/save-with-listing', { product, listing }).then(r => r.data)

export const listProducts = (params?: {
  search?: string
  category?: string
  platform?: string
  limit?: number
  offset?: number
}): Promise<ProductListResponse> =>
  api.get('/products', { params }).then(r => r.data)

export const getProduct = (id: string): Promise<SavedProductRecord> =>
  api.get(`/products/${id}`).then(r => r.data)

export const updateProduct = (id: string, product: ProductInput): Promise<SavedProductRecord> =>
  api.put(`/products/${id}`, product).then(r => r.data)

export const deleteProduct = (id: string): Promise<void> =>
  api.delete(`/products/${id}`).then(r => r.data)

export const duplicateProduct = (id: string): Promise<SavedProductRecord> =>
  api.post(`/products/${id}/duplicate`).then(r => r.data)

// ── Bulk Operations ───────────────────────────────────────────────────────
export const downloadCSVTemplate = () => {
  window.open('/api/bulk/template', '_blank')
}

export const previewCSVImport = (file: File): Promise<BulkImportPreviewResponse> => {
  const form = new FormData()
  form.append('file', file)
  return api.post('/bulk/preview', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data)
}

export const bulkGenerateListings = (products: ProductInput[]) =>
  api.post('/bulk/generate', { products }).then(r => r.data)

// ── Error helper ─────────────────────────────────────────────────────────
export const getErrorMessage = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    return error.response?.data?.detail || error.message || 'Request failed'
  }
  if (error instanceof Error) return error.message
  return 'An unexpected error occurred'
}

export default api

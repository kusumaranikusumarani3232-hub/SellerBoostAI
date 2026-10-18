import React, { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Search, Plus, Trash2, Copy, ExternalLink,
  Library, RefreshCw
} from 'lucide-react'
import { listProducts, deleteProduct, duplicateProduct, getErrorMessage } from '../lib/api'
import type { SavedProductRecord } from '../types'
import { PLATFORM_LABELS, formatDate } from '../lib/utils'
import { LoadingSpinner } from '../components/LoadingSpinner'
import toast from 'react-hot-toast'

export const ProductLibrary: React.FC = () => {
  const navigate = useNavigate()
  const [products, setProducts] = useState<SavedProductRecord[]>([])
  const [total, setTotal] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [platformFilter, setPlatformFilter] = useState('')
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null)

  const load = useCallback(async () => {
    setIsLoading(true)
    try {
      const res = await listProducts({
        search: search || undefined,
        platform: platformFilter || undefined,
        limit: 50,
      })
      setProducts(res.products)
      setTotal(res.total)
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setIsLoading(false)
    }
  }, [search, platformFilter])

  useEffect(() => {
    const t = setTimeout(load, 300)
    return () => clearTimeout(t)
  }, [load])

  const handleDelete = async (id: string) => {
    try {
      await deleteProduct(id)
      setProducts(p => p.filter(x => x.id !== id))
      setTotal(t => t - 1)
      toast.success('Product deleted')
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setDeleteConfirm(null)
    }
  }

  const handleDuplicate = async (id: string) => {
    try {
      const copy = await duplicateProduct(id)
      setProducts(p => [copy, ...p])
      setTotal(t => t + 1)
      toast.success('Product duplicated!')
    } catch (err) {
      toast.error(getErrorMessage(err))
    }
  }

  return (
    <div className="px-4 md:px-8 py-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-primary flex items-center gap-3">
            <Library size={22} className="text-purple-400" />
            My Products
          </h1>
          <p className="text-sm text-muted mt-1">{total} saved product{total !== 1 ? 's' : ''}</p>
        </div>
        <button onClick={() => navigate('/create')} className="btn-primary">
          <Plus size={16} />
          New Listing
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <div className="relative flex-1">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
          <input
            className="input pl-9"
            placeholder="Search products, brands, materials…"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
        <select
          className="select w-full sm:w-48"
          value={platformFilter}
          onChange={e => setPlatformFilter(e.target.value)}
        >
          <option value="">All Platforms</option>
          {Object.entries(PLATFORM_LABELS).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
        <button onClick={load} className="btn-secondary flex-shrink-0">
          <RefreshCw size={15} />
          Refresh
        </button>
      </div>

      {/* Products grid */}
      {isLoading ? (
        <LoadingSpinner fullPage text="Loading your products…" />
      ) : products.length === 0 ? (
        <div className="text-center py-20">
          <div className="w-16 h-16 rounded-2xl bg-purple-600/10 flex items-center justify-center mx-auto mb-4">
            <Library size={28} className="text-purple-400" />
          </div>
          <h3 className="text-lg font-semibold text-primary mb-2">No products yet</h3>
          <p className="text-sm text-muted mb-6">
            {search || platformFilter ? 'No products match your filters.' : 'Create your first product listing to get started.'}
          </p>
          {!search && !platformFilter && (
            <button onClick={() => navigate('/create')} className="btn-primary">
              <Plus size={16} />
              Create First Listing
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {products.map(record => (
            <div key={record.id} className="card p-5 hover:card-glow transition-all group">
              {/* Header */}
              <div className="flex items-start justify-between gap-3 mb-3">
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-sm text-primary leading-snug line-clamp-2">
                    {record.product_data.name}
                  </h3>
                  <p className="text-xs text-muted mt-0.5">
                    {record.product_data.category}
                    {record.product_data.brand ? ` · ${record.product_data.brand}` : ''}
                  </p>
                </div>
                <span className="badge badge-purple text-xs flex-shrink-0">
                  {PLATFORM_LABELS[record.product_data.platform] || record.product_data.platform}
                </span>
              </div>

              {/* Listing preview */}
              {record.listing ? (
                <p className="text-xs text-muted leading-relaxed line-clamp-3 mb-3">
                  {record.listing.short_description || record.listing.description}
                </p>
              ) : (
                <div className="rounded-lg bg-yellow-500/5 border border-yellow-500/15 p-2.5 mb-3">
                  <p className="text-xs text-yellow-400">No listing generated yet</p>
                </div>
              )}

              {/* Quality score */}
              {record.listing?.quality_report && (
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-5 h-1.5 rounded-full bg-border overflow-hidden flex-1">
                    <div
                      className="h-full rounded-full transition-all"
                      style={{
                        width: `${record.listing.quality_report.overall_score}%`,
                        background: record.listing.quality_report.overall_score >= 70 ? '#10b981' : '#f59e0b'
                      }}
                    />
                  </div>
                  <span className="text-xs text-muted">{record.listing.quality_report.overall_score}/100</span>
                </div>
              )}

              <p className="text-xs text-muted mb-4">{formatDate(record.updated_at)}</p>

              {/* Actions */}
              <div className="flex items-center gap-2 pt-3 border-t border-subtle">
                <button
                  onClick={() => navigate('/create', {
                    state: { prefill: record.product_data }
                  })}
                  className="btn-primary flex-1 justify-center text-xs py-2"
                >
                  <ExternalLink size={13} />
                  {record.listing ? 'Edit & Regenerate' : 'Generate Listing'}
                </button>
                <button
                  onClick={() => handleDuplicate(record.id)}
                  className="btn-secondary p-2"
                  title="Duplicate"
                >
                  <Copy size={14} />
                </button>
                {deleteConfirm === record.id ? (
                  <div className="flex gap-1">
                    <button onClick={() => handleDelete(record.id)} className="btn-danger p-2 text-xs">
                      <Trash2 size={13} />
                    </button>
                    <button onClick={() => setDeleteConfirm(null)} className="btn-secondary p-2 text-xs">
                      ✕
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => setDeleteConfirm(record.id)}
                    className="btn-ghost p-2 hover:text-red-400"
                    title="Delete"
                  >
                    <Trash2 size={14} />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

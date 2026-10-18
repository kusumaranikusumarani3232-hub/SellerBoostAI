import React, { useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { Wand2, Save, RefreshCw, ChevronLeft } from 'lucide-react'
import { generateListing, refineListing, saveProductWithListing, getErrorMessage } from '../lib/api'
import type { ProductInput, ListingOutput } from '../types'
import { ProductForm } from '../components/ProductForm'
import { ListingWorkspace } from '../components/ListingWorkspace'
import { QualityPanel } from '../components/QualityPanel'
import { ListingSkeleton } from '../components/LoadingSpinner'
import toast from 'react-hot-toast'

export const CreateListing: React.FC = () => {
  const { state } = useLocation()
  const prefill = state?.prefill as ProductInput | undefined

  const [product, setProduct] = useState<ProductInput | null>(null)
  const [listing, setListing] = useState<ListingOutput | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [isRefining, setIsRefining] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [step, setStep] = useState<'form' | 'result'>('form')

  // Auto-generate if prefill provided
  useEffect(() => {
    if (prefill && !listing) {
      setProduct(prefill)
      handleGenerate(prefill)
    }
  }, [])

  const handleGenerate = async (data: ProductInput) => {
    setIsGenerating(true)
    setProduct(data)
    setStep('result')
    try {
      const result = await generateListing(data)
      setListing(result)
      toast.success('Listing generated!', { icon: '✨' })
    } catch (err) {
      toast.error(getErrorMessage(err))
      setStep('form')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleRefine = async (instruction: string) => {
    if (!listing || !product) return
    setIsRefining(true)
    try {
      const refined = await refineListing({
        original_listing: listing,
        product_data: product,
        instruction,
        thread_id: listing.thread_id,
      })
      setListing(refined)
      toast.success('Listing refined!', { icon: '✦' })
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setIsRefining(false)
    }
  }

  const handleSave = async () => {
    if (!product || !listing) return
    setIsSaving(true)
    try {
      await saveProductWithListing(product, listing)
      toast.success('Product saved to library!', { icon: '📚' })
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setIsSaving(false)
    }
  }

  const handleRegenerate = async () => {
    if (!product) return
    setListing(null)
    await handleGenerate(product)
  }

  return (
    <div className="px-4 md:px-8 py-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          {step === 'result' && (
            <button
              onClick={() => { setStep('form'); setListing(null) }}
              className="btn-ghost text-xs mb-3 gap-1.5"
            >
              <ChevronLeft size={14} /> Back to form
            </button>
          )}
          <h1 className="text-2xl font-bold text-primary">
            {step === 'form' ? 'Create Product Listing' : 'Your Generated Listing'}
          </h1>
          <p className="text-sm text-muted mt-1">
            {step === 'form'
              ? 'Fill in your product details and let AI create professional copy'
              : `Generated for: ${product?.name}`}
          </p>
        </div>
        {step === 'result' && listing && (
          <div className="flex gap-2">
            <button onClick={handleRegenerate} disabled={isGenerating} className="btn-secondary">
              <RefreshCw size={15} className={isGenerating ? 'animate-spin' : ''} />
              Regenerate
            </button>
            <button onClick={handleSave} disabled={isSaving} className="btn-primary">
              <Save size={15} />
              {isSaving ? 'Saving…' : 'Save to Library'}
            </button>
          </div>
        )}
      </div>

      {step === 'form' && (
        <div className="max-w-2xl mx-auto">
          <ProductForm
            defaultValues={prefill}
            onSubmit={handleGenerate}
            isLoading={isGenerating}
          />
        </div>
      )}

      {step === 'result' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Listing workspace */}
          <div className="lg:col-span-2">
            {isGenerating ? (
              <div>
                <div className="flex items-center gap-3 mb-6 p-4 rounded-xl bg-purple-600/10 border border-purple-500/20">
                  <div className="w-8 h-8 border-2 border-purple-500/30 border-t-purple-500 rounded-full animate-spin flex-shrink-0" />
                  <div>
                    <p className="text-sm font-semibold text-primary">Generating with open-weight AI…</p>
                    <p className="text-xs text-muted">Meta Llama 3.1 is crafting your listing</p>
                  </div>
                </div>
                <ListingSkeleton />
              </div>
            ) : listing ? (
              <ListingWorkspace
                listing={listing}
                product={product!}
                onRefine={handleRefine}
                isRefining={isRefining}
              />
            ) : null}
          </div>

          {/* Sidebar: form + quality */}
          <div className="space-y-5">
            {/* Edit product details */}
            <div className="card p-5">
              <h3 className="text-sm font-semibold text-primary mb-4 flex items-center gap-2">
                <Wand2 size={15} className="text-purple-400" />
                Edit & Regenerate
              </h3>
              <ProductForm
                defaultValues={product || undefined}
                onSubmit={handleGenerate}
                isLoading={isGenerating}
                submitLabel="Regenerate"
              />
            </div>

            {/* Quality report */}
            {listing?.quality_report && (
              <QualityPanel report={listing.quality_report} />
            )}
          </div>
        </div>
      )}
    </div>
  )
}

import React from 'react'
import { useForm, useFieldArray } from 'react-hook-form'
import { Plus, X, Wand2, Loader2, Info } from 'lucide-react'
import type { ProductInput } from '../types'
import {
  CATEGORY_OPTIONS, PLATFORM_LABELS, TONE_LABELS, LANGUAGE_OPTIONS
} from '../lib/utils'

interface ProductFormProps {
  defaultValues?: Partial<ProductInput>
  onSubmit: (data: ProductInput) => void
  isLoading?: boolean
  submitLabel?: string
}

export const ProductForm: React.FC<ProductFormProps> = ({
  defaultValues,
  onSubmit,
  isLoading,
  submitLabel = 'Generate Listing',
}) => {
  const { register, handleSubmit, control, formState: { errors } } = useForm<ProductInput>({
    defaultValues: {
      name: '',
      category: 'Home & Living',
      features: [''],
      platform: 'etsy',
      tone: 'artisanal',
      language: 'en',
      ...defaultValues,
    },
  })

  const { fields, append, remove } = useFieldArray({ control, name: 'features' as never })

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Core required */}
      <div className="card p-5 space-y-4">
        <div className="flex items-center gap-2 mb-1">
          <div className="w-5 h-5 rounded-md bg-purple-600/20 flex items-center justify-center">
            <span className="text-xs text-purple-400 font-bold">1</span>
          </div>
          <h3 className="font-semibold text-sm text-primary">Product Basics</h3>
          <span className="badge badge-purple text-xs ml-1">Required</span>
        </div>

        <div>
          <label className="label">Product Name *</label>
          <input
            {...register('name', { required: 'Product name is required', minLength: { value: 2, message: 'Minimum 2 characters' } })}
            className="input"
            placeholder="e.g. Lavender Dreams Hand-Poured Soy Candle"
          />
          {errors.name && <p className="text-xs text-red-400 mt-1">{errors.name.message}</p>}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="label">Category</label>
            <select {...register('category')} className="select">
              {CATEGORY_OPTIONS.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Brand / Shop Name</label>
            <input {...register('brand')} className="input" placeholder="e.g. Willow & Bloom" />
          </div>
        </div>

        {/* Features */}
        <div>
          <label className="label">Key Features / Highlights</label>
          <div className="space-y-2">
            {(fields as { id: string }[]).map((field, idx) => (
              <div key={field.id} className="flex gap-2">
                <input
                  {...register(`features.${idx}` as const)}
                  className="input"
                  placeholder={`Feature ${idx + 1} (e.g. hand-poured, cotton wick)`}
                />
                {fields.length > 1 && (
                  <button type="button" onClick={() => remove(idx)} className="btn-ghost p-2 flex-shrink-0">
                    <X size={15} />
                  </button>
                )}
              </div>
            ))}
          </div>
          <button
            type="button"
            onClick={() => append('')}
            className="mt-2 btn-ghost text-xs gap-1.5"
          >
            <Plus size={13} /> Add Feature
          </button>
        </div>
      </div>

      {/* Platform & Tone */}
      <div className="card p-5 space-y-4">
        <div className="flex items-center gap-2 mb-1">
          <div className="w-5 h-5 rounded-md bg-purple-600/20 flex items-center justify-center">
            <span className="text-xs text-purple-400 font-bold">2</span>
          </div>
          <h3 className="font-semibold text-sm text-primary">Platform & Style</h3>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="label">Target Platform</label>
            <select {...register('platform')} className="select">
              {Object.entries(PLATFORM_LABELS).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Tone & Voice</label>
            <select {...register('tone')} className="select">
              {Object.entries(TONE_LABELS).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="label">Output Language</label>
          <select {...register('language')} className="select">
            {LANGUAGE_OPTIONS.map(({ code, label }) => (
              <option key={code} value={code}>{label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Materials & Target */}
      <div className="card p-5 space-y-4">
        <div className="flex items-center gap-2 mb-1">
          <div className="w-5 h-5 rounded-md bg-purple-600/20 flex items-center justify-center">
            <span className="text-xs text-purple-400 font-bold">3</span>
          </div>
          <h3 className="font-semibold text-sm text-primary">Product Details</h3>
          <span className="badge badge-yellow text-xs ml-1">Improves Quality</span>
        </div>

        <div>
          <label className="label">Materials / Ingredients</label>
          <input {...register('materials')} className="input" placeholder="e.g. Natural soy wax, cotton wick, lavender essential oil" />
        </div>
        <div>
          <label className="label">Target Customer</label>
          <input {...register('target_customer')} className="input" placeholder="e.g. Home decor enthusiasts, gift shoppers" />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="label">Price (optional)</label>
            <input {...register('price', { valueAsNumber: true })} type="number" step="0.01" min="0" className="input" placeholder="24.99" />
          </div>
          <div>
            <label className="label">Dimensions (optional)</label>
            <input {...register('dimensions')} className="input" placeholder="e.g. 3 x 3 x 4 inches" />
          </div>
        </div>
        <div>
          <label className="label">Care Instructions (optional)</label>
          <input {...register('care_instructions')} className="input" placeholder="e.g. Trim wick to 1/4 inch before each burn" />
        </div>
        <div>
          <label className="label">Custom Notes (optional)</label>
          <textarea {...register('custom_notes')} className="textarea" rows={2} placeholder="Special instructions, unique selling angle, or additional context for the AI..." />
        </div>
      </div>

      {/* Disclaimer */}
      <div className="flex items-start gap-2.5 p-3.5 rounded-lg bg-blue-500/5 border border-blue-500/15">
        <Info size={14} className="text-blue-400 flex-shrink-0 mt-0.5" />
        <p className="text-xs text-muted leading-relaxed">
          SellerBoost AI generates copy based only on the details you provide. The AI will not invent certifications,
          health claims, dimensions, or guarantees. Review all generated content before publishing.
        </p>
      </div>

      {/* Submit */}
      <button type="submit" disabled={isLoading} className="btn-primary w-full py-3.5 text-base justify-center">
        {isLoading ? (
          <>
            <Loader2 size={18} className="animate-spin" />
            Generating with AI…
          </>
        ) : (
          <>
            <Wand2 size={18} />
            {submitLabel}
          </>
        )}
      </button>
    </form>
  )
}

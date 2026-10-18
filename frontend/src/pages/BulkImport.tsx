import React, { useState, useRef } from 'react'
import {
  Upload, Download, FileText, CheckCircle2, XCircle,
  PlayCircle, Loader2, AlertTriangle, ChevronDown, ChevronUp
} from 'lucide-react'
import { previewCSVImport, bulkGenerateListings, getErrorMessage, getTemplateUrl } from '../lib/api'
import type { BulkImportPreviewResponse, BulkGenerateItemResult } from '../types'
import { PLATFORM_LABELS } from '../lib/utils'
import toast from 'react-hot-toast'

export const BulkImport: React.FC = () => {
  const fileRef = useRef<HTMLInputElement>(null)
  const [dragOver, setDragOver] = useState(false)
  const [preview, setPreview] = useState<BulkImportPreviewResponse | null>(null)
  const [results, setResults] = useState<BulkGenerateItemResult[] | null>(null)
  const [isPreviewing, setIsPreviewing] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [progress, setProgress] = useState(0)
  const [expandedRow, setExpandedRow] = useState<number | null>(null)

  const handleFile = async (file: File) => {
    setIsPreviewing(true)
    setPreview(null)
    setResults(null)
    try {
      const prev = await previewCSVImport(file)
      setPreview(prev)
      if (prev.invalid_rows > 0) {
        toast(`${prev.invalid_rows} row(s) have validation errors`, { icon: '⚠️' })
      } else {
        toast.success(`${prev.valid_rows} products ready to generate`)
      }
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setIsPreviewing(false)
    }
  }

  const handleGenerate = async () => {
    if (!preview) return
    const validProducts = preview.items.filter(i => i.valid && i.product_data).map(i => i.product_data!)
    if (validProducts.length === 0) return

    setIsGenerating(true)
    setProgress(0)
    try {
      const res = await bulkGenerateListings(validProducts)
      setResults(res.results)
      setProgress(100)
      toast.success(`${res.succeeded}/${res.total} listings generated!`, { icon: '✨' })
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setIsGenerating(false)
    }
  }

  const handleExport = () => {
    if (!results || !preview) return
    const validProducts = preview.items.filter(i => i.valid && i.product_data).map(i => i.product_data!)
    const rows: string[][] = [
      ['Product Name', 'Category', 'Platform', 'Title 1', 'Title 2', 'Description', 'Keywords', 'Tags', 'Status']
    ]
    results.forEach(r => {
      const origProduct = validProducts[r.index]
        ?? preview.items.find(i => i.product_data?.name === r.product_name)?.product_data
        ?? validProducts.find(p => p.name === r.product_name)
      const category = r.category || origProduct?.category || ''
      const platform = r.platform || origProduct?.platform || ''

      if (r.status === 'success' && r.listing) {
        const l = r.listing
        rows.push([
          r.product_name,
          category,
          platform,
          l.titles[0]?.title ?? '',
          l.titles[1]?.title ?? '',
          l.description,
          l.keywords.join('; '),
          l.tags.join('; '),
          'success'
        ])
      } else {
        rows.push([r.product_name, category, platform, '', '', '', '', '', `error: ${r.error_message}`])
      }
    })
    const csv = rows.map(r => r.map(c => `"${(c ?? '').replace(/"/g, '""')}"`).join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = 'sellerboost_bulk_export.csv'; a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="px-4 md:px-8 py-8 max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-primary flex items-center gap-3">
          <Upload size={22} className="text-purple-400" />
          Bulk Listing Studio
        </h1>
        <p className="text-sm text-muted mt-1">Import a CSV, preview data, and generate listings for multiple products at once</p>
      </div>

      {/* Step 1: Upload */}
      <div className="card p-6 mb-6">
        <div className="flex items-center gap-2 mb-5">
          <div className="w-6 h-6 rounded-md bg-purple-600/20 flex items-center justify-center text-xs text-purple-400 font-bold">1</div>
          <h2 className="font-semibold text-base text-primary">Upload CSV File</h2>
        </div>

        {/* Download template */}
        <div className="flex items-center justify-between p-4 rounded-xl bg-secondary border border-subtle mb-4">
          <div>
            <p className="text-sm font-medium text-primary">Need the template?</p>
            <p className="text-xs text-muted mt-0.5">Download our CSV template with headers and an example row</p>
          </div>
          <a href={getTemplateUrl()} download="sellerboost_template.csv" className="btn-secondary">
            <Download size={15} />
            Download Template
          </a>
        </div>

        {/* Drop zone */}
        <div
          className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all ${
            dragOver ? 'border-purple-500 bg-purple-500/5' : 'border-border hover:border-purple-500/50 hover:bg-purple-500/3'
          }`}
          onDragOver={e => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          onDrop={e => {
            e.preventDefault(); setDragOver(false)
            const f = e.dataTransfer.files[0]
            if (f) handleFile(f)
          }}
          onClick={() => fileRef.current?.click()}
        >
          <input
            ref={fileRef}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={e => { const f = e.target.files?.[0]; if (f) handleFile(f) }}
          />
          {isPreviewing ? (
            <Loader2 size={28} className="animate-spin text-purple-400 mx-auto mb-3" />
          ) : (
            <FileText size={28} className="text-muted mx-auto mb-3" />
          )}
          <p className="text-sm font-medium text-primary">
            {isPreviewing ? 'Validating CSV…' : 'Drop CSV here or click to browse'}
          </p>
          <p className="text-xs text-muted mt-1">Max 5MB · UTF-8 encoding</p>
        </div>
      </div>

      {/* Step 2: Preview */}
      {preview && (
        <div className="card p-6 mb-6">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-md bg-purple-600/20 flex items-center justify-center text-xs text-purple-400 font-bold">2</div>
              <h2 className="font-semibold text-base text-primary">Preview & Validate</h2>
            </div>
            <div className="flex gap-3 text-xs">
              <span className="badge badge-green">{preview.valid_rows} valid</span>
              {preview.invalid_rows > 0 && <span className="badge badge-red">{preview.invalid_rows} errors</span>}
            </div>
          </div>

          {/* Summary stats */}
          <div className="grid grid-cols-3 gap-4 mb-5">
            {[
              { label: 'Total Rows', value: preview.total_rows },
              { label: 'Valid Rows', value: preview.valid_rows, color: 'text-green-400' },
              { label: 'Invalid Rows', value: preview.invalid_rows, color: preview.invalid_rows > 0 ? 'text-red-400' : 'text-muted' },
            ].map(({ label, value, color }) => (
              <div key={label} className="rounded-xl bg-secondary p-4 text-center">
                <p className={`text-2xl font-bold ${color || 'text-primary'}`}>{value}</p>
                <p className="text-xs text-muted mt-0.5">{label}</p>
              </div>
            ))}
          </div>

          {/* Row list */}
          <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
            {preview.items.map(item => (
              <div
                key={item.row_number}
                className={`rounded-lg border p-3 cursor-pointer transition-colors ${
                  item.valid ? 'border-green-500/20 bg-green-500/5' : 'border-red-500/20 bg-red-500/5'
                }`}
                onClick={() => setExpandedRow(expandedRow === item.row_number ? null : item.row_number)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    {item.valid
                      ? <CheckCircle2 size={14} className="text-green-400" />
                      : <XCircle size={14} className="text-red-400" />
                    }
                    <span className="text-sm text-primary font-medium">
                      Row {item.row_number}: {item.raw_row.name || '(unnamed)'}
                    </span>
                    {item.valid && item.product_data && (
                      <span className="badge badge-purple text-xs">
                        {PLATFORM_LABELS[item.product_data.platform] || item.product_data.platform}
                      </span>
                    )}
                  </div>
                  {expandedRow === item.row_number ? <ChevronUp size={14} className="text-muted" /> : <ChevronDown size={14} className="text-muted" />}
                </div>
                {expandedRow === item.row_number && !item.valid && item.errors.length > 0 && (
                  <ul className="mt-2 space-y-0.5">
                    {item.errors.map((e, i) => (
                      <li key={i} className="text-xs text-red-400 flex items-center gap-1.5">
                        <AlertTriangle size={10} /> {e}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>

          {/* Generate button */}
          {preview.valid_rows > 0 && (
            <div className="mt-5 space-y-3">
              <button
                onClick={handleGenerate}
                disabled={isGenerating}
                className="btn-primary w-full justify-center py-3 text-base"
              >
                {isGenerating ? (
                  <><Loader2 size={18} className="animate-spin" /> Generating {preview.valid_rows} listings…</>
                ) : (
                  <><PlayCircle size={18} /> Generate {preview.valid_rows} Listing{preview.valid_rows !== 1 ? 's' : ''}</>
                )}
              </button>
              {isGenerating && (
                <div className="w-full bg-subtle rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-purple-500 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${progress > 0 ? progress : 60}%` }}
                  />
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Step 3: Results */}
      {results && (
        <div className="card p-6">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-md bg-purple-600/20 flex items-center justify-center text-xs text-purple-400 font-bold">3</div>
              <h2 className="font-semibold text-base text-primary">Results</h2>
            </div>
            <button onClick={handleExport} className="btn-primary">
              <Download size={15} />
              Export CSV
            </button>
          </div>

          <div className="space-y-3">
            {results.map(r => (
              <div
                key={r.index}
                className={`rounded-xl border p-4 ${
                  r.status === 'success' ? 'border-green-500/20 bg-green-500/5' : 'border-red-500/20 bg-red-500/5'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    {r.status === 'success'
                      ? <CheckCircle2 size={15} className="text-green-400" />
                      : <XCircle size={15} className="text-red-400" />
                    }
                    <span className="text-sm font-medium text-primary">{r.product_name}</span>
                  </div>
                  {r.status === 'success' && r.listing && (
                    <span className="text-xs text-green-400">{r.listing.keywords.length} keywords · {r.listing.titles.length} titles</span>
                  )}
                </div>
                {r.status === 'error' && r.error_message && (
                  <p className="text-xs text-red-400 mt-1.5 ml-6">{r.error_message}</p>
                )}
                {r.status === 'success' && r.listing && (
                  <p className="text-xs text-muted mt-1.5 ml-6 line-clamp-2">{r.listing.short_description}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

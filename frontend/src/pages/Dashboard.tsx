import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Zap, PlusCircle, Library, Upload, TrendingUp,
  Sparkles, ArrowRight, ChevronRight, BarChart3,
  Star, Cpu, Shield, Globe, Wand2
} from 'lucide-react'
import { getSamples, getModelStatus } from '../lib/api'
import type { SampleProduct, ModelStatusResponse } from '../types'
import { PLATFORM_LABELS, formatProvider } from '../lib/utils'

const FEATURE_CARDS = [
  {
    icon: Sparkles,
    title: 'AI Listing Generator',
    desc: 'Generate 3 title variants, description, keywords, and platform-optimized copy from simple product details.',
    color: 'from-purple-600/20 to-purple-400/5',
    border: 'border-purple-500/20',
  },
  {
    icon: Wand2,
    title: 'Listing Refinement',
    desc: 'Refine any listing with plain-language instructions — "Make it more premium", "Translate to Hindi".',
    color: 'from-blue-600/20 to-blue-400/5',
    border: 'border-blue-500/20',
  },
  {
    icon: BarChart3,
    title: 'Quality Auditor',
    desc: 'Transparent rule-based checks for title length, missing details, unsupported claims, and readability.',
    color: 'from-green-600/20 to-green-400/5',
    border: 'border-green-500/20',
  },
  {
    icon: Globe,
    title: 'Multi-Platform',
    desc: 'Auto-formatted for Etsy, Amazon, Shopify, eBay, and Instagram — the right format every time.',
    color: 'from-orange-600/20 to-orange-400/5',
    border: 'border-orange-500/20',
  },
]

export const Dashboard: React.FC = () => {
  const navigate = useNavigate()
  const [samples, setSamples] = useState<SampleProduct[]>([])
  const [status, setStatus] = useState<ModelStatusResponse | null>(null)

  useEffect(() => {
    getSamples().then(r => setSamples(r.samples)).catch(() => {})
    getModelStatus().then(setStatus).catch(() => {})
  }, [])

  const handleTrySample = (sample: SampleProduct) => {
    navigate('/create', { state: { prefill: sample } })
  }

  return (
    <div className="px-4 md:px-8 py-8 max-w-6xl mx-auto space-y-10">
      {/* Hero */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-purple-900/40 via-purple-800/20 to-bg-secondary border border-purple-500/20 p-8 md:p-12">
        {/* Background glow */}
        <div className="absolute top-0 right-0 w-80 h-80 bg-purple-600/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-60 h-60 bg-purple-400/5 rounded-full blur-3xl pointer-events-none" />

        <div className="relative">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-purple-500/15 border border-purple-500/25 text-purple-300 text-xs font-medium mb-5">
            <Zap size={12} />
            Open-Weight AI · Hacktoberfest 2026 · Best Use of Backboard
          </div>
          <h1 className="text-3xl md:text-5xl font-bold text-primary mb-4 leading-tight">
            Turn product details into<br />
            <span className="gradient-text">professional listings</span>
          </h1>
          <p className="text-secondary text-base md:text-lg max-w-2xl mb-8 leading-relaxed">
            SellerBoost AI helps small online sellers, handmade creators, and marketplace entrepreneurs
            generate search-optimized product listings using open-weight AI — fast, affordable, and in your voice.
          </p>
          <div className="flex flex-wrap gap-3">
            <button onClick={() => navigate('/create')} className="btn-primary text-base px-6 py-3">
              <PlusCircle size={18} />
              Create Your First Listing
              <ArrowRight size={16} />
            </button>
            <button onClick={() => navigate('/library')} className="btn-secondary text-base px-6 py-3">
              <Library size={17} />
              My Products
            </button>
          </div>
        </div>
      </div>

      {/* AI Status Card */}
      {status && (
        <div className={`card p-5 border flex flex-col md:flex-row md:items-center gap-4 ${
          status.health_status === 'demo_mode'
            ? 'border-yellow-500/20 bg-yellow-500/5'
            : 'border-green-500/20 bg-green-500/5'
        }`}>
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
              status.health_status === 'demo_mode' ? 'bg-yellow-500/20' : 'bg-green-500/20'
            }`}>
              <Cpu size={18} className={status.health_status === 'demo_mode' ? 'text-yellow-400' : 'text-green-400'} />
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <p className="font-semibold text-sm text-primary">{status.display_name}</p>
                <span className="badge badge-purple text-[10px]">Provider: {formatProvider(status.provider)}</span>
                <span className="badge badge-blue font-mono text-[10px]" title={`Exact Model ID: ${status.active_model}`}>Model: {status.active_model}</span>
              </div>
              <p className="text-xs text-muted mt-0.5">{status.notes.slice(0, 100)}</p>
            </div>
          </div>
          <div className="flex flex-wrap gap-4 md:ml-auto text-xs text-muted">
            <span className="flex items-center gap-1">
              <Shield size={11} className="text-purple-400" />
              {status.license.split('—')[0].trim()}
            </span>
            <span className="flex items-center gap-1">
              <Zap size={11} className="text-purple-400" />
              {status.pricing_per_1m_tokens}
            </span>
            <span className="flex items-center gap-1 capitalize">
              <Star size={11} className="text-purple-400" />
              {status.total_inferences} inferences
            </span>
          </div>
        </div>
      )}

      {/* Feature grid */}
      <div>
        <h2 className="text-xl font-bold text-primary mb-5">What SellerBoost AI Does</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {FEATURE_CARDS.map(({ icon: Icon, title, desc, color, border }) => (
            <div key={title} className={`card p-5 bg-gradient-to-br ${color} border ${border} hover:scale-[1.01] transition-transform`}>
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center flex-shrink-0">
                  <Icon size={18} className="text-purple-300" />
                </div>
                <div>
                  <h3 className="font-semibold text-sm text-primary mb-1">{title}</h3>
                  <p className="text-xs text-muted leading-relaxed">{desc}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { icon: PlusCircle, label: 'Create Listing', sub: 'From scratch', to: '/create', primary: true },
          { icon: Upload, label: 'Bulk Import', sub: 'CSV batch mode', to: '/bulk', primary: false },
          { icon: Library, label: 'My Library', sub: 'Saved products', to: '/library', primary: false },
        ].map(({ icon: Icon, label, sub, to, primary }) => (
          <button
            key={to}
            onClick={() => navigate(to)}
            className={`card p-5 text-left hover:scale-[1.02] transition-transform group ${primary ? 'border-purple-500/30 bg-purple-600/5' : ''}`}
          >
            <div className={`w-11 h-11 rounded-xl flex items-center justify-center mb-3 ${primary ? 'bg-purple-600/20' : 'bg-card'}`}>
              <Icon size={20} className={primary ? 'text-purple-400' : 'text-muted group-hover:text-secondary transition-colors'} />
            </div>
            <p className="font-semibold text-sm text-primary">{label}</p>
            <p className="text-xs text-muted mt-0.5">{sub}</p>
            <ChevronRight size={14} className="mt-3 text-muted group-hover:text-purple-400 group-hover:translate-x-1 transition-all" />
          </button>
        ))}
      </div>

      {/* Sample Products */}
      {samples.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-5">
            <div>
              <h2 className="text-xl font-bold text-primary">Try Sample Products</h2>
              <p className="text-sm text-muted mt-1">Explore SellerBoost AI with pre-loaded products — no setup needed</p>
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {samples.slice(0, 6).map((sample) => (
              <button
                key={sample.id}
                onClick={() => handleTrySample(sample)}
                className="card p-5 text-left hover:card-glow hover:scale-[1.01] transition-all group"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-600/20 to-purple-400/10 flex items-center justify-center text-lg">
                    {sample.category.includes('Candle') || sample.name.toLowerCase().includes('candle') ? '🕯️' :
                     sample.category.includes('Bag') || sample.name.toLowerCase().includes('tote') ? '👜' :
                     sample.category.includes('Mug') || sample.name.toLowerCase().includes('mug') ? '☕' :
                     sample.category.includes('Jewel') || sample.name.toLowerCase().includes('pendant') ? '💍' :
                     '🧶'}
                  </div>
                  <span className="badge badge-purple text-xs">
                    {PLATFORM_LABELS[sample.platform] || sample.platform}
                  </span>
                </div>
                <h3 className="font-semibold text-sm text-primary leading-snug mb-1">{sample.name}</h3>
                <p className="text-xs text-muted mb-3">{sample.category} · {sample.brand}</p>
                <div className="flex items-center gap-1.5 text-xs text-purple-400 font-medium group-hover:gap-2.5 transition-all">
                  <Zap size={11} />
                  Generate listing
                  <ArrowRight size={11} className="group-hover:translate-x-1 transition-transform" />
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Why Open Innovation */}
      <div className="card p-6 border-purple-500/15">
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 rounded-xl bg-purple-600/20 flex items-center justify-center flex-shrink-0">
            <TrendingUp size={18} className="text-purple-400" />
          </div>
          <div>
            <h3 className="font-bold text-base text-primary mb-2">Why Open Innovation Matters</h3>
            <p className="text-sm text-muted leading-relaxed max-w-3xl">
              SellerBoost AI is built on <strong className="text-secondary">Meta Llama 3.1 8B Instruct</strong> — a genuinely open-weight model
              with a community license permitting commercial use. Unlike proprietary APIs that can change pricing, restrict access, or
              discontinue models, open-weight models give small businesses control, predictability, and the ability to self-host when needed.
              Using Backboard as the hosted inference gateway keeps setup simple while preserving the ability to migrate to local Ollama
              inference at any time — truly portable AI for independent sellers.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

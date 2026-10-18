import React, { useState } from 'react'
import {
  FileText, Star, Hash, Share2, ShoppingBag,
  ChevronDown, ChevronUp, Tag, List
} from 'lucide-react'
import type { ListingOutput, ProductInput } from '../types'
import { PLATFORM_LABELS, formatProvider } from '../lib/utils'
import { CopyButton } from './CopyButton'

interface ListingWorkspaceProps {
  listing: ListingOutput
  product: ProductInput
  onRefine?: (instruction: string) => void
  isRefining?: boolean
}

type TabKey = 'titles' | 'description' | 'keywords' | 'platforms' | 'social'

const TABS: { key: TabKey; label: string; icon: React.ElementType }[] = [
  { key: 'titles', label: 'Titles', icon: Star },
  { key: 'description', label: 'Description', icon: FileText },
  { key: 'keywords', label: 'Keywords', icon: Hash },
  { key: 'platforms', label: 'Platforms', icon: ShoppingBag },
  { key: 'social', label: 'Social', icon: Share2 },
]

const PLATFORM_EMOJIS: Record<string, string> = {
  etsy: '🟠', amazon: '🟡', shopify: '🟢', ebay: '🔴', instagram: '💜'
}

export const ListingWorkspace: React.FC<ListingWorkspaceProps> = ({
  listing, product, onRefine, isRefining
}) => {
  const [activeTab, setActiveTab] = useState<TabKey>('titles')
  const [refineInstruction, setRefineInstruction] = useState('')
  const [expandedPlatform, setExpandedPlatform] = useState<string | null>('etsy')

  const REFINE_PRESETS = [
    'Make this description more premium',
    'Shorten the description for Instagram',
    `Translate everything into ${product.language !== 'en' ? product.language : 'Hindi'}`,
    'Rewrite in a friendly, warm tone',
    'Emphasize handmade craftsmanship',
    'Make titles more search-optimized',
  ]

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Token / cost info & Provider/Model display */}
      <div className="flex flex-wrap items-center gap-3 text-xs text-muted">
        <span className="badge badge-purple" title={`Provider: ${formatProvider(listing.provider_used)}`}>
          Provider: <strong className="text-purple-300 font-semibold ml-1">{formatProvider(listing.provider_used)}</strong>
        </span>
        <span className="badge badge-blue font-mono text-[11px]" title={`Exact Model ID: ${listing.model_used}`}>
          Model: <strong className="text-blue-300 ml-1">{listing.model_used}</strong>
        </span>
        {listing.tokens_used && (
          <>
            <span>{listing.tokens_used.total_tokens?.toLocaleString() ?? 0} tokens used</span>
            {listing.estimated_cost_usd && listing.estimated_cost_usd > 0 && (
              <span className="text-green-400">~${listing.estimated_cost_usd.toFixed(6)} cost</span>
            )}
            {listing.estimated_cost_usd === 0 && (
              <span className="text-yellow-400">⚡ Demo mode — synthetic response</span>
            )}
          </>
        )}
      </div>

      {/* Tab bar */}
      <div className="tab-bar overflow-x-auto">
        {TABS.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            className={`tab flex-shrink-0 flex items-center gap-1.5 ${activeTab === key ? 'active' : ''}`}
            onClick={() => setActiveTab(key)}
          >
            <Icon size={13} />
            {label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="space-y-4">
        {/* TITLES */}
        {activeTab === 'titles' && (
          <div className="space-y-3">
            {listing.titles.map((t, i) => (
              <div key={i} className="card p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="badge badge-purple text-xs">{t.focus}</span>
                      <span className="text-xs text-muted">{t.char_count} chars</span>
                    </div>
                    <p className="text-sm text-primary leading-relaxed font-medium">{t.title}</p>
                  </div>
                  <CopyButton text={t.title} copyKey={`title-${i}`} />
                </div>
              </div>
            ))}

            {/* Short description */}
            <div className="card p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-muted uppercase tracking-wide">Short Description</span>
                <CopyButton text={listing.short_description} copyKey="short" />
              </div>
              <p className="text-sm text-secondary leading-relaxed">{listing.short_description}</p>
            </div>

            {/* CTA */}
            <div className="card p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-muted uppercase tracking-wide">Call to Action</span>
                <CopyButton text={listing.call_to_action} copyKey="cta" />
              </div>
              <p className="text-sm text-secondary">{listing.call_to_action}</p>
            </div>
          </div>
        )}

        {/* DESCRIPTION */}
        {activeTab === 'description' && (
          <div className="space-y-4">
            <div className="card p-5">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-semibold text-primary">Main Description</span>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted">{listing.description.split(' ').length} words</span>
                  <CopyButton text={listing.description} copyKey="desc" />
                </div>
              </div>
              <p className="text-sm text-secondary leading-relaxed whitespace-pre-wrap">{listing.description}</p>
            </div>

            {/* Benefits */}
            <div className="card p-5">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <List size={15} className="text-purple-400" />
                  <span className="text-sm font-semibold text-primary">Key Benefits</span>
                </div>
                <CopyButton text={listing.benefits.map(b => `• ${b}`).join('\n')} copyKey="benefits" />
              </div>
              <ul className="space-y-2">
                {listing.benefits.map((b, i) => (
                  <li key={i} className="flex items-start gap-2.5 text-sm text-secondary">
                    <span className="text-purple-400 mt-0.5 flex-shrink-0">✦</span>
                    {b}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* KEYWORDS */}
        {activeTab === 'keywords' && (
          <div className="space-y-4">
            <div className="card p-5">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Hash size={15} className="text-purple-400" />
                  <span className="text-sm font-semibold text-primary">Search Keywords</span>
                  <span className="badge badge-purple text-xs">{listing.keywords.length}</span>
                </div>
                <CopyButton text={listing.keywords.join(', ')} copyKey="keywords" />
              </div>
              <div className="flex flex-wrap gap-2">
                {listing.keywords.map((kw, i) => (
                  <span key={i} className="badge badge-purple cursor-default hover:bg-purple-500/25 transition-colors">
                    {kw}
                  </span>
                ))}
              </div>
            </div>

            <div className="card p-5">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Tag size={15} className="text-blue-400" />
                  <span className="text-sm font-semibold text-primary">Marketplace Tags</span>
                  <span className="badge badge-blue text-xs">{listing.tags.length}</span>
                </div>
                <CopyButton text={listing.tags.join(', ')} copyKey="tags" />
              </div>
              <div className="flex flex-wrap gap-2">
                {listing.tags.map((tag, i) => (
                  <span key={i} className="badge badge-blue cursor-default">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* PLATFORMS */}
        {activeTab === 'platforms' && (
          <div className="space-y-3">
            {Object.entries(listing.platform_presets).map(([platform, preset]) => {
              const isExpanded = expandedPlatform === platform
              return (
                <div key={platform} className={`card overflow-hidden ${isExpanded ? 'card-glow' : ''}`}>
                  <button
                    className="w-full flex items-center justify-between p-4 hover:bg-card-hover transition-colors"
                    onClick={() => setExpandedPlatform(isExpanded ? null : platform)}
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-lg">{PLATFORM_EMOJIS[platform] || '🛒'}</span>
                      <span className="font-semibold text-sm text-primary capitalize">
                        {PLATFORM_LABELS[platform] || platform}
                      </span>
                    </div>
                    {isExpanded ? <ChevronUp size={16} className="text-muted" /> : <ChevronDown size={16} className="text-muted" />}
                  </button>

                  {isExpanded && (
                    <div className="px-4 pb-4 pt-0 space-y-3 border-t border-subtle">
                      {'title' in preset && (
                        <div>
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs text-muted">Title</span>
                            <CopyButton text={(preset as { title: string }).title} copyKey={`${platform}-title`} />
                          </div>
                          <p className="text-sm text-primary font-medium">{(preset as { title: string }).title}</p>
                        </div>
                      )}

                      {platform === 'etsy' && (
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-xs text-muted">13 Etsy Tags</span>
                            <CopyButton text={(preset as { tags_13: string[] }).tags_13.join(', ')} copyKey="etsy-tags" />
                          </div>
                          <div className="flex flex-wrap gap-1.5">
                            {(preset as { tags_13: string[] }).tags_13.map((tag, i) => {
                              const isOverLimit = tag.length > 20
                              return (
                                <span
                                  key={i}
                                  className={`badge text-xs ${
                                    isOverLimit
                                      ? 'bg-red-500/20 text-red-300 border border-red-500/40'
                                      : 'badge-purple'
                                  }`}
                                  title={isOverLimit ? `${tag.length} chars (exceeds Etsy's 20-character limit)` : `${tag.length}/20 chars`}
                                >
                                  {tag}
                                  {isOverLimit && (
                                    <span className="ml-1 text-[10px] text-red-400 font-bold">({tag.length} chars)</span>
                                  )}
                                </span>
                              )
                            })}
                          </div>
                        </div>
                      )}

                      {platform === 'amazon' && (
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-xs text-muted">5 Bullet Points</span>
                            <CopyButton text={(preset as { bullet_points: string[] }).bullet_points.map(b => `• ${b}`).join('\n')} copyKey="amazon-bullets" />
                          </div>
                          <ul className="space-y-1.5">
                            {(preset as { bullet_points: string[] }).bullet_points.map((b, i) => (
                              <li key={i} className="text-sm text-secondary flex gap-2">
                                <span className="text-yellow-400 flex-shrink-0">•</span>{b}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {platform === 'shopify' && (
                        <div className="space-y-2">
                          <div>
                            <span className="text-xs text-muted">SEO Title</span>
                            <p className="text-sm text-secondary mt-0.5">{(preset as { page_title: string }).page_title}</p>
                          </div>
                          <div>
                            <span className="text-xs text-muted">Meta Description</span>
                            <p className="text-sm text-secondary mt-0.5">{(preset as { meta_description: string }).meta_description}</p>
                          </div>
                        </div>
                      )}

                      {'description' in preset && (
                        <div>
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs text-muted">Description</span>
                            <CopyButton text={(preset as { description: string }).description} copyKey={`${platform}-desc`} />
                          </div>
                          <p className="text-sm text-secondary leading-relaxed whitespace-pre-wrap">
                            {(preset as { description: string }).description}
                          </p>
                        </div>
                      )}

                      {'formatted_description' in preset && (
                        <div>
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs text-muted">Description</span>
                            <CopyButton text={(preset as { formatted_description: string }).formatted_description} copyKey={`${platform}-fdesc`} />
                          </div>
                          <p className="text-sm text-secondary leading-relaxed">
                            {(preset as { formatted_description: string }).formatted_description}
                          </p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}

        {/* SOCIAL */}
        {activeTab === 'social' && (
          <div className="space-y-4">
            {[
              { label: '🚀 Product Launch Post', key: 'launch_post', field: listing.social_content.launch_post },
              { label: '📸 Instagram Caption', key: 'ig_caption', field: listing.social_content.instagram_caption },
              { label: '🎬 TikTok Reel Hook', key: 'tiktok', field: listing.social_content.tiktok_reel_hook },
            ].map(({ label, key, field }) => (
              <div key={key} className="card p-5">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-semibold text-primary">{label}</span>
                  <CopyButton text={field} copyKey={key} />
                </div>
                <p className="text-sm text-secondary leading-relaxed whitespace-pre-wrap">{field}</p>
              </div>
            ))}

            <div className="card p-5">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-primary"># Hashtags</span>
                  <span className="badge badge-purple text-xs">{listing.social_content.hashtags.length}</span>
                </div>
                <CopyButton text={listing.social_content.hashtags.join(' ')} copyKey="hashtags" />
              </div>
              <div className="flex flex-wrap gap-2">
                {listing.social_content.hashtags.map((h, i) => (
                  <span key={i} className="badge badge-blue text-xs">{h}</span>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Refinement panel */}
      {onRefine && (
        <div className="card p-5 border-purple-500/20 bg-purple-600/5">
          <h3 className="text-sm font-semibold text-primary mb-3 flex items-center gap-2">
            <span className="w-5 h-5 rounded-md bg-purple-600/30 flex items-center justify-center text-xs text-purple-300">✦</span>
            Refine with AI
          </h3>
          <p className="text-xs text-muted mb-3">
            Tell the AI how to improve this listing in plain language. Your product facts are preserved.
          </p>

          {/* Presets */}
          <div className="flex flex-wrap gap-2 mb-3">
            {REFINE_PRESETS.map(preset => (
              <button
                key={preset}
                onClick={() => setRefineInstruction(preset)}
                className="text-xs px-2.5 py-1 rounded-full border border-purple-500/25 text-purple-300 hover:bg-purple-500/15 transition-colors"
              >
                {preset}
              </button>
            ))}
          </div>

          <div className="flex gap-2">
            <textarea
              className="textarea text-xs"
              rows={2}
              placeholder="e.g. Make this description more premium and luxurious..."
              value={refineInstruction}
              onChange={e => setRefineInstruction(e.target.value)}
            />
          </div>
          <button
            onClick={() => { if (refineInstruction.trim()) { onRefine(refineInstruction); setRefineInstruction('') } }}
            disabled={!refineInstruction.trim() || isRefining}
            className="btn-primary mt-2 w-full justify-center"
          >
            {isRefining ? (
              <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Refining…</>
            ) : (
              '✦ Apply Refinement'
            )}
          </button>
        </div>
      )}
    </div>
  )
}

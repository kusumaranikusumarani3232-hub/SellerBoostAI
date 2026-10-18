import React from 'react'
import { CheckCircle, XCircle, AlertCircle, Info, ChevronDown, ChevronUp } from 'lucide-react'
import type { QualityReport } from '../types'
import { getScoreColor, getSeverityColor } from '../lib/utils'
import { useState } from 'react'

interface QualityPanelProps {
  report: QualityReport
}

const SEVERITY_ICONS = {
  critical: XCircle,
  warning: AlertCircle,
  info: Info,
}

export const QualityPanel: React.FC<QualityPanelProps> = ({ report }) => {
  const [expanded, setExpanded] = useState(true)
  const scoreColor = getScoreColor(report.overall_score)

  const failures = report.items.filter(i => !i.passed)
  const passes = report.items.filter(i => i.passed)

  return (
    <div className="card overflow-hidden">
      {/* Header */}
      <button
        className="w-full flex items-center justify-between p-5 hover:bg-card-hover transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-4">
          {/* Score ring */}
          <div className="relative w-14 h-14 flex-shrink-0">
            <svg className="w-full h-full -rotate-90" viewBox="0 0 56 56">
              <circle cx="28" cy="28" r="22" fill="none" stroke="#2a2a3d" strokeWidth="5" />
              <circle
                cx="28" cy="28" r="22" fill="none"
                stroke={scoreColor}
                strokeWidth="5"
                strokeDasharray={`${2 * Math.PI * 22}`}
                strokeDashoffset={`${2 * Math.PI * 22 * (1 - report.overall_score / 100)}`}
                strokeLinecap="round"
                style={{ transition: 'stroke-dashoffset 0.6s ease' }}
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-sm font-bold" style={{ color: scoreColor }}>
                {report.overall_score}
              </span>
            </div>
          </div>
          <div className="text-left">
            <p className="font-semibold text-sm text-primary">Quality Score</p>
            <p className="text-xs text-muted mt-0.5">{report.grade}</p>
            <p className="text-xs text-muted">{report.passed_checks}/{report.total_checks} checks passed</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {failures.length > 0 && (
            <span className="badge badge-yellow text-xs">{failures.length} issues</span>
          )}
          {expanded ? <ChevronUp size={16} className="text-muted" /> : <ChevronDown size={16} className="text-muted" />}
        </div>
      </button>

      {expanded && (
        <div className="px-5 pb-5 space-y-4 border-t border-subtle">
          {/* Readability stats */}
          <div className="grid grid-cols-3 gap-3 pt-4">
            <div className="rounded-lg bg-secondary p-3 text-center">
              <p className="text-lg font-bold text-primary">{report.readability.word_count}</p>
              <p className="text-xs text-muted">Words</p>
            </div>
            <div className="rounded-lg bg-secondary p-3 text-center">
              <p className="text-lg font-bold text-primary">{report.readability.reading_ease_score}</p>
              <p className="text-xs text-muted">Readability</p>
            </div>
            <div className="rounded-lg bg-secondary p-3 text-center">
              <p className="text-xs font-semibold text-primary leading-tight">{report.readability.reading_level.split(' ')[0]}</p>
              <p className="text-xs text-muted">Level</p>
            </div>
          </div>

          {/* Issues first */}
          {failures.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-muted uppercase tracking-wide mb-2">Issues to Address</p>
              <div className="space-y-2">
                {failures.map(item => {
                  const Icon = SEVERITY_ICONS[item.severity]
                  const color = getSeverityColor(item.severity)
                  return (
                    <div key={item.id} className="rounded-lg p-3" style={{ background: `${color}10`, border: `1px solid ${color}20` }}>
                      <div className="flex items-start gap-2.5">
                        <Icon size={13} style={{ color }} className="flex-shrink-0 mt-0.5" />
                        <div>
                          <p className="text-xs font-semibold text-primary">{item.title}</p>
                          <p className="text-xs text-muted mt-0.5 leading-relaxed">{item.message}</p>
                          {item.suggestion && (
                            <p className="text-xs mt-1.5" style={{ color }}>→ {item.suggestion}</p>
                          )}
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Passes */}
          {passes.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-muted uppercase tracking-wide mb-2">Checks Passed</p>
              <div className="space-y-1.5">
                {passes.map(item => (
                  <div key={item.id} className="flex items-center gap-2 text-xs text-muted">
                    <CheckCircle size={12} className="text-green-400 flex-shrink-0" />
                    {item.title} — <span className="text-muted/70">{item.message}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Compliance notes */}
          {report.compliance_notes.length > 0 && (
            <div className="rounded-lg bg-blue-500/5 border border-blue-500/15 p-3">
              {report.compliance_notes.map((note, i) => (
                <p key={i} className="text-xs text-muted leading-relaxed">{note}</p>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

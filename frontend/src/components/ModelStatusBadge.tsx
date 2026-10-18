import React, { useState, useEffect } from 'react'
import { Cpu, AlertTriangle, CheckCircle, WifiOff, DollarSign, Activity, Server } from 'lucide-react'
import { getModelStatus } from '../lib/api'
import type { ModelStatusResponse } from '../types'
import { formatCurrency, formatProvider } from '../lib/utils'

export const ModelStatusBadge: React.FC = () => {
  const [status, setStatus] = useState<ModelStatusResponse | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    const load = async () => {
      try {
        const data = await getModelStatus()
        setStatus(data)
        setError(false)
      } catch {
        setError(true)
      }
    }
    load()
    const interval = setInterval(load, 60000)
    return () => clearInterval(interval)
  }, [])

  if (error) {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-red-500/10 border border-red-500/20">
        <WifiOff size={13} className="text-red-400" />
        <span className="text-xs text-red-400">Backend offline</span>
      </div>
    )
  }

  if (!status) {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-card border border-default">
        <Activity size={13} className="text-muted animate-pulse" />
        <span className="text-xs text-muted">Checking status…</span>
      </div>
    )
  }

  const isDemo = status.health_status === 'demo_mode'
  const isHealthy = status.health_status === 'healthy'

  return (
    <div className="flex items-center gap-2 flex-wrap">
      {/* Status indicator */}
      <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-medium
        ${isDemo ? 'bg-yellow-500/10 border-yellow-500/20 text-yellow-400' :
          isHealthy ? 'bg-green-500/10 border-green-500/20 text-green-400' :
          'bg-red-500/10 border-red-500/20 text-red-400'}`}>
        {isDemo ? <AlertTriangle size={12} /> : isHealthy ? <CheckCircle size={12} /> : <AlertTriangle size={12} />}
        {isDemo ? 'Demo Mode' : isHealthy ? 'AI Active' : 'Degraded'}
      </div>

      {/* Real Provider badge */}
      <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-card border border-default text-xs" title={`Inference Provider: ${formatProvider(status.provider)}`}>
        <Server size={11} className="text-purple-400" />
        <span className="text-muted">Provider:</span>
        <span className="text-primary font-medium">{formatProvider(status.provider)}</span>
      </div>

      {/* Exact Model ID tag */}
      <div className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-card border border-default text-xs" title={`Exact Model ID: ${status.active_model}`}>
        <Cpu size={11} className="text-blue-400" />
        <span className="text-muted">Model:</span>
        <span className="text-primary font-mono text-[11px] font-medium">
          {status.active_model}
        </span>
      </div>

      {/* Credit tracker (only when real AI active) */}
      {!isDemo && (
        <div className="hidden xl:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-card border border-default text-xs">
          <DollarSign size={11} className="text-purple-400" />
          <span className="text-muted">Credit:</span>
          <span className="text-primary font-medium">
            {formatCurrency(status.estimated_remaining_usd)}
          </span>
          <span className="text-muted">left</span>
        </div>
      )}
    </div>
  )
}

import React from 'react'
import { Loader2 } from 'lucide-react'

interface LoadingSpinnerProps {
  size?: number
  text?: string
  fullPage?: boolean
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ size = 24, text, fullPage }) => {
  if (fullPage) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
        <div className="relative">
          <div className="w-16 h-16 rounded-full border-2 border-purple-500/20 border-t-purple-500 animate-spin" />
          <div className="absolute inset-2 rounded-full border-2 border-purple-400/10 border-b-purple-400 animate-spin" style={{ animationDirection: 'reverse', animationDuration: '0.8s' }} />
        </div>
        {text && <p className="text-secondary text-sm animate-pulse">{text}</p>}
      </div>
    )
  }

  return (
    <span className="inline-flex items-center gap-2">
      <Loader2 size={size} className="animate-spin text-purple-400" />
      {text && <span className="text-secondary text-sm">{text}</span>}
    </span>
  )
}

export const SkeletonBlock: React.FC<{ className?: string }> = ({ className = '' }) => (
  <div className={`skeleton h-4 ${className}`} />
)

export const ListingSkeleton: React.FC = () => (
  <div className="space-y-4 animate-fade-in">
    {[1, 2, 3].map(i => (
      <div key={i} className="card p-4 space-y-3">
        <SkeletonBlock className="w-3/4 h-5" />
        <SkeletonBlock className="w-full h-3" />
        <SkeletonBlock className="w-5/6 h-3" />
        <SkeletonBlock className="w-2/3 h-3" />
      </div>
    ))}
  </div>
)

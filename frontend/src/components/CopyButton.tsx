import React from 'react'
import { Copy, Check } from 'lucide-react'
import { useCopy } from '../hooks/useCopy'

interface CopyButtonProps {
  text: string
  copyKey?: string
  size?: 'sm' | 'md'
  className?: string
}

export const CopyButton: React.FC<CopyButtonProps> = ({ text, copyKey = 'default', size = 'sm', className = '' }) => {
  const { copied, copy } = useCopy()
  const isCopied = copied === copyKey

  return (
    <button
      onClick={() => copy(text, copyKey)}
      className={`btn-ghost transition-all ${size === 'sm' ? 'p-1.5' : 'p-2'} ${className}`}
      title={isCopied ? 'Copied!' : 'Copy to clipboard'}
    >
      {isCopied
        ? <Check size={size === 'sm' ? 13 : 15} className="text-green-400" />
        : <Copy size={size === 'sm' ? 13 : 15} />
      }
    </button>
  )
}

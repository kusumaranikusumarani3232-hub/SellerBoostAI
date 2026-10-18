import { useState, useCallback } from 'react'
import { copyToClipboard } from '../lib/utils'

export function useCopy(timeout = 1500) {
  const [copied, setCopied] = useState<string | null>(null)

  const copy = useCallback(async (text: string, key = 'default') => {
    try {
      await copyToClipboard(text)
      setCopied(key)
      setTimeout(() => setCopied(null), timeout)
    } catch {
      // silently fail
    }
  }, [timeout])

  return { copied, copy }
}

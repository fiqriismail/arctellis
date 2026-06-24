'use client'

import { useEffect, useState } from 'react'
import { checkAccess } from '@/features/auth/api/checkAccess'
import { useToken } from './useToken'

type GroupAccessStatus = 'loading' | 'authorized' | 'unauthorized'

export function useGroupAccess(enabled: boolean): { status: GroupAccessStatus } {
  const { getToken } = useToken()
  const [status, setStatus] = useState<GroupAccessStatus>('loading')

  useEffect(() => {
    if (!enabled) return
    let cancelled = false

    async function check() {
      try {
        const result = await checkAccess(getToken)
        if (!cancelled) setStatus(result ? 'authorized' : 'unauthorized')
      } catch {
        try {
          const result = await checkAccess(getToken)
          if (!cancelled) setStatus(result ? 'authorized' : 'unauthorized')
        } catch {
          if (!cancelled) setStatus('unauthorized')
        }
      }
    }

    check()
    return () => { cancelled = true }
  }, [enabled]) // eslint-disable-line react-hooks/exhaustive-deps

  return { status }
}

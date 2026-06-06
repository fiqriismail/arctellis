import { Badge } from '@/components/ui/badge'
import type { BadgeVariant } from '@/components/ui/badge'

const STATUS_MAP: Record<string, BadgeVariant> = {
  'draft':                'secondary',
  'submitted':            'default',
  'under sme review':     'warning',
  'budget confirmation':  'warning',
  'exception required':   'warning',
  'sourcing in progress': 'default',
  'approved for po':      'success',
  'approved':             'success',
  'closed':               'secondary',
  'rejected':             'destructive',
  'active':               'success',
}

interface StatusBadgeProps {
  value: string
}

export function StatusBadge({ value }: StatusBadgeProps) {
  const variant = STATUS_MAP[value.toLowerCase()]
  if (!variant) {
    return <span>{value}</span>
  }
  return <Badge variant={variant}>{value}</Badge>
}

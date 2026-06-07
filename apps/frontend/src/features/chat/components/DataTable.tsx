'use client'

import { useMemo, useState } from 'react'
import { ChevronDown, ChevronsUpDown, ChevronUp } from 'lucide-react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { StatusBadge } from './StatusBadge'
import {
  formatCellValue,
  parseDate,
  parseNumeric,
  type ColumnKind,
} from '../lib/formatCell'
import type { ParsedTable } from '../lib/parseMarkdownTable'

type SortDir = 'asc' | 'desc'

function compareCells(a: string, b: string, kind: ColumnKind): number {
  if (kind === 'currency' || kind === 'number') {
    return (parseNumeric(a) ?? -Infinity) - (parseNumeric(b) ?? -Infinity)
  }
  if (kind === 'date') {
    return (
      (parseDate(a)?.getTime() ?? -Infinity) -
      (parseDate(b)?.getTime() ?? -Infinity)
    )
  }
  return a.localeCompare(b)
}

const CONTAINER_CLASS = [
  'my-3 w-full overflow-hidden rounded-lg border',
  '[&>div]:overflow-x-auto',
  '[&>div::-webkit-scrollbar]:h-1.5',
  '[&>div::-webkit-scrollbar-track]:bg-transparent',
  '[&>div::-webkit-scrollbar-thumb]:rounded-full',
  '[&>div::-webkit-scrollbar-thumb]:bg-border',
  'hover:[&>div::-webkit-scrollbar-thumb]:bg-muted-foreground/40',
].join(' ')

/**
 * Data-driven table rendered from a ParsedTable: client-side column sorting,
 * currency/date formatting, status badges, and right-aligned numbers.
 */
export function DataTable({ table }: { table: ParsedTable }) {
  const [sort, setSort] = useState<{ col: number; dir: SortDir } | null>(null)

  const rows = useMemo(() => {
    if (!sort) return table.rows
    const { col, dir } = sort
    const kind = table.columns[col].kind
    const sorted = [...table.rows].sort((ra, rb) =>
      compareCells(ra[col] ?? '', rb[col] ?? '', kind),
    )
    return dir === 'asc' ? sorted : sorted.reverse()
  }, [table, sort])

  function toggleSort(col: number) {
    setSort((prev) =>
      prev && prev.col === col
        ? { col, dir: prev.dir === 'asc' ? 'desc' : 'asc' }
        : { col, dir: 'asc' },
    )
  }

  return (
    <div className={CONTAINER_CLASS}>
      <Table>
        <TableHeader>
          <TableRow>
            {table.columns.map((c, i) => {
              const active = sort?.col === i
              const Icon = active
                ? sort!.dir === 'asc'
                  ? ChevronUp
                  : ChevronDown
                : ChevronsUpDown
              return (
                <TableHead
                  key={i}
                  aria-sort={
                    active
                      ? sort!.dir === 'asc'
                        ? 'ascending'
                        : 'descending'
                      : 'none'
                  }
                  className="border-r border-border bg-muted p-0 last:border-r-0"
                >
                  <button
                    type="button"
                    onClick={() => toggleSort(i)}
                    className={`flex w-full items-center gap-1 px-4 py-3 text-[13px] font-semibold hover:bg-muted-foreground/10 ${
                      c.numeric ? 'justify-end' : ''
                    }`}
                  >
                    <span>{c.name}</span>
                    <Icon
                      className={`h-3.5 w-3.5 shrink-0 ${
                        active ? 'text-foreground' : 'text-muted-foreground/60'
                      }`}
                    />
                  </button>
                </TableHead>
              )
            })}
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((row, ri) => (
            <TableRow key={ri}>
              {table.columns.map((c, ci) => {
                const cell = row[ci] ?? ''
                return (
                  <TableCell
                    key={ci}
                    className={`border-r border-border text-[13px] last:border-r-0 ${
                      c.numeric ? 'text-right tabular-nums' : ''
                    }`}
                  >
                    {c.kind === 'text' ? (
                      <StatusBadge value={cell} />
                    ) : (
                      formatCellValue(cell, c.kind)
                    )}
                  </TableCell>
                )
              })}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}

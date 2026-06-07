'use client'

import { useState, type ReactNode } from 'react'
import { Button } from '@/components/ui/button'
import { ChartView } from './ChartView'
import type { ChartType } from '../lib/chartData'
import type { ParsedTable } from '../lib/parseMarkdownTable'

interface TableChartToggleProps {
  table: ParsedTable
  /** The original styled table, shown in the table view. */
  children: ReactNode
}

const CHART_TYPES: { type: ChartType; label: string }[] = [
  { type: 'bar', label: 'Bar' },
  { type: 'pie', label: 'Pie' },
  { type: 'donut', label: 'Donut' },
]

/**
 * Wraps a chartable Markdown table with a Table/Chart toggle. Aggregation
 * tables (one label + one numeric column) default to a pie chart; other
 * chartable tables default to the table view.
 */
export function TableChartToggle({ table, children }: TableChartToggleProps) {
  const [view, setView] = useState<'table' | 'chart'>(
    table.isAggregation ? 'chart' : 'table',
  )
  const [chartType, setChartType] = useState<ChartType>(
    table.isAggregation ? 'pie' : 'bar',
  )
  const [valueIndex, setValueIndex] = useState(table.numericIndexes[0])

  const multipleValues = table.numericIndexes.length > 1

  return (
    <div className="my-3">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <ToggleGroup>
          <ToggleButton
            active={view === 'table'}
            onClick={() => setView('table')}
          >
            Table
          </ToggleButton>
          <ToggleButton
            active={view === 'chart'}
            onClick={() => setView('chart')}
          >
            Chart
          </ToggleButton>
        </ToggleGroup>

        {view === 'chart' && (
          <>
            <ToggleGroup>
              {CHART_TYPES.map(({ type, label }) => (
                <ToggleButton
                  key={type}
                  active={chartType === type}
                  onClick={() => setChartType(type)}
                >
                  {label}
                </ToggleButton>
              ))}
            </ToggleGroup>

            {multipleValues && (
              <ToggleGroup>
                {table.numericIndexes.map((i) => (
                  <ToggleButton
                    key={i}
                    active={valueIndex === i}
                    onClick={() => setValueIndex(i)}
                  >
                    {table.columns[i].name}
                  </ToggleButton>
                ))}
              </ToggleGroup>
            )}
          </>
        )}
      </div>

      {view === 'table' ? (
        children
      ) : (
        <ChartView table={table} chartType={chartType} valueIndex={valueIndex} />
      )}
    </div>
  )
}

function ToggleGroup({ children }: { children: ReactNode }) {
  return (
    <div className="inline-flex overflow-hidden rounded-md border border-border">
      {children}
    </div>
  )
}

function ToggleButton({
  active,
  onClick,
  children,
}: {
  active: boolean
  onClick: () => void
  children: ReactNode
}) {
  return (
    <Button
      type="button"
      variant={active ? 'secondary' : 'ghost'}
      size="sm"
      aria-pressed={active}
      onClick={onClick}
      className="rounded-none border-0 text-xs"
    >
      {children}
    </Button>
  )
}

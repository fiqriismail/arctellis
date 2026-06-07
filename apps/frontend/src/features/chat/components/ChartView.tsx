'use client'

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  XAxis,
  YAxis,
} from 'recharts'
import {
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from '@/components/ui/chart'
import {
  buildChartConfig,
  buildChartData,
  CHART_PALETTE,
  type ChartType,
} from '../lib/chartData'
import type { ParsedTable } from '../lib/parseMarkdownTable'

interface ChartViewProps {
  table: ParsedTable
  chartType: ChartType
  valueIndex: number
}

export function ChartView({ table, chartType, valueIndex }: ChartViewProps) {
  const data = buildChartData(table, { valueIndex, chartType })
  const valueLabel = table.columns[valueIndex]?.name ?? 'Value'
  const config: ChartConfig = {
    value: { label: valueLabel, color: 'var(--chart-1)' },
  }

  if (chartType === 'bar') {
    return (
      <ChartContainer config={config} className="max-h-[280px] w-full">
        <BarChart data={data} accessibilityLayer>
          <CartesianGrid vertical={false} />
          <XAxis
            dataKey="name"
            tickLine={false}
            axisLine={false}
            tickMargin={8}
          />
          <YAxis tickLine={false} axisLine={false} width={48} />
          <ChartTooltip content={<ChartTooltipContent />} />
          <Bar dataKey="value" fill="var(--chart-1)" radius={4} />
        </BarChart>
      </ChartContainer>
    )
  }

  // Pie / donut: one colour + legend entry per category.
  const sliceConfig = buildChartConfig(data)
  const innerRadius = chartType === 'donut' ? 60 : 0
  return (
    <ChartContainer
      config={sliceConfig as ChartConfig}
      className="mx-auto max-h-[300px]"
    >
      <PieChart>
        <ChartTooltip content={<ChartTooltipContent nameKey="name" />} />
        <Pie data={data} dataKey="value" nameKey="name" innerRadius={innerRadius}>
          {data.map((d, i) => (
            <Cell key={d.name} fill={CHART_PALETTE[i % CHART_PALETTE.length]} />
          ))}
        </Pie>
        <ChartLegend
          content={<ChartLegendContent nameKey="name" />}
          className="flex-wrap"
        />
      </PieChart>
    </ChartContainer>
  )
}

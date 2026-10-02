import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { WeightEntry } from '../../api/types'
import { formatDate } from '../../utils/format'

type WeightChartProps = {
  weights: WeightEntry[]
  height?: number
}

export function WeightChart({ weights, height = 320 }: WeightChartProps) {
  return (
    <div className="chart-container" style={{ minHeight: height }}>
      <ResponsiveContainer width="100%" height={height}>
        <LineChart
          data={weights}
          margin={{
            top: 10,
            right: 15,
            left: 0,
            bottom: 10,
          }}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="#27324a"
          />

          <XAxis
            dataKey="measurement_date"
            stroke="#7f8ba3"
            tickFormatter={(value) => {
              const [, month, day] =
                value.split('-')
              return `${month}/${day}`
            }}
          />

          <YAxis
            stroke="#7f8ba3"
            domain={['dataMin - 5', 'dataMax + 5']}
          />

          <Tooltip
            labelFormatter={(value) =>
              formatDate(String(value))
            }
            formatter={(value) => [
              `${value} lbs`,
              'Weight',
            ]}
            contentStyle={{
              background: '#0d1425',
              border: '1px solid #34405b',
              borderRadius: '10px',
            }}
          />

          <Line
            type="monotone"
            dataKey="weight"
            stroke="#818cf8"
            strokeWidth={3}
            dot={{
              r: 4,
              fill: '#818cf8',
            }}
            activeDot={{
              r: 6,
            }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

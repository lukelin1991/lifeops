import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import { formatMoney, titleCase } from '../utils/format'

const COLORS: Record<string, string> = {
  stock: '#818cf8',
  crypto: '#f59e0b',
}

type AllocationChartProps = {
  allocation: { asset_type: string; market_value: number; percent: number }[]
  height?: number
}

export function AllocationChart({ allocation, height = 240 }: AllocationChartProps) {
  const data = allocation
    .filter((slice) => slice.market_value > 0)
    .map((slice) => ({
      name: titleCase(slice.asset_type),
      key: slice.asset_type,
      value: slice.market_value,
      percent: slice.percent,
    }))

  if (data.length === 0) {
    return <p className="empty-state">No priced holdings to chart yet.</p>
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie
          data={data}
          dataKey="value"
          nameKey="name"
          innerRadius="55%"
          outerRadius="85%"
          paddingAngle={2}
          stroke="none"
        >
          {data.map((slice) => (
            <Cell key={slice.key} fill={COLORS[slice.key] ?? '#34d399'} />
          ))}
        </Pie>
        <Tooltip
          formatter={(value, name, item) => [
            `${formatMoney(Number(value))} (${item.payload.percent}%)`,
            name,
          ]}
          contentStyle={{
            background: '#0d1425',
            border: '1px solid #34405b',
            borderRadius: '10px',
          }}
          itemStyle={{ color: '#e8edf7' }}
        />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  )
}

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { CategorySpending } from '../api/types'
import { formatMoney } from '../utils/format'

export function SpendingChart({ rows }: { rows: CategorySpending[] }) {
  const data = rows.map((row) => ({
    name: row.category_name,
    Spent: row.spent,
    Budget: row.budget ?? 0,
  }))

  if (data.length === 0) {
    return <p className="empty-state">No spending or budgets this month.</p>
  }

  return (
    <div className="chart-container">
      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={data} margin={{ top: 10, right: 15, left: 0, bottom: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#27324a" />
          <XAxis dataKey="name" stroke="#7f8ba3" interval={0} tick={{ fontSize: 12 }} />
          <YAxis stroke="#7f8ba3" />
          <Tooltip
            formatter={(value) => formatMoney(Number(value))}
            contentStyle={{
              background: '#0d1425',
              border: '1px solid #34405b',
              borderRadius: '10px',
            }}
            cursor={{ fill: 'rgba(129, 140, 248, 0.08)' }}
          />
          <Legend />
          <Bar dataKey="Budget" fill="#34405b" radius={[4, 4, 0, 0]} />
          <Bar dataKey="Spent" fill="#818cf8" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

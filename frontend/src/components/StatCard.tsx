import type { ReactNode } from 'react'

type StatCardProps = {
  label: string
  value: ReactNode
  hint?: ReactNode
  tone?: 'good' | 'bad' | 'neutral'
}

export function StatCard({ label, value, hint, tone = 'neutral' }: StatCardProps) {
  return (
    <div className={`stat-card tone-${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      {hint && <small>{hint}</small>}
    </div>
  )
}

import { useCallback, useState } from 'react'
import { describeError } from '../../api/client'
import { moneyApi } from '../../api/money'
import type { Debt, DebtPayoff } from '../../api/types'
import { Alert } from '../../components/Alert'
import { ResourceManager } from '../../components/ResourceManager'
import { StatCard } from '../../components/StatCard'
import { useApiData } from '../../hooks/useApiData'
import { formatMoney } from '../../utils/format'
import type { FieldDef } from '../../utils/forms'

const FIELDS: FieldDef[] = [
  { name: 'name', label: 'Name', required: true },
  { name: 'balance', label: 'Balance', type: 'number', step: '0.01', required: true },
  { name: 'apr', label: 'APR %', type: 'number', step: '0.001', required: true },
  { name: 'minimum_payment', label: 'Minimum payment', type: 'number', step: '0.01', required: true },
  { name: 'notes', label: 'Notes', type: 'textarea' },
]

function months(value: number | null) {
  if (value === null) return 'Never'
  const years = Math.floor(value / 12)
  const rest = value % 12
  if (years === 0) return `${value} mo`
  return rest === 0 ? `${years} yr` : `${years} yr ${rest} mo`
}

export function DebtsTab() {
  const loader = useCallback(() => moneyApi.debts.list(), [])
  const { data, error, reload } = useApiData(loader)

  const [extra, setExtra] = useState('200')
  const [strategy, setStrategy] = useState<'avalanche' | 'snowball'>('avalanche')
  const [plan, setPlan] = useState<DebtPayoff | null>(null)
  const [planError, setPlanError] = useState('')

  async function calculate() {
    setPlanError('')
    try {
      setPlan(await moneyApi.payoff(Number(extra) || 0, strategy))
    } catch (err) {
      setPlanError(describeError(err))
    }
  }

  return (
    <>
      <Alert message={error} />
      <ResourceManager<Debt>
        eyebrow="DEBTS"
        title="Balances"
        addLabel="Add debt"
        items={data ?? []}
        fields={FIELDS}
        onCreate={moneyApi.debts.create}
        onUpdate={moneyApi.debts.update}
        onDelete={moneyApi.debts.remove}
        onChanged={() => {
          reload()
          setPlan(null)
        }}
        emptyText="No debts. 🎉"
        columns={[
          { label: 'Name', render: (d) => d.name },
          { label: 'Balance', className: 'num', render: (d) => formatMoney(d.balance) },
          { label: 'APR', className: 'num', render: (d) => `${d.apr}%` },
          { label: 'Minimum', className: 'num', render: (d) => formatMoney(d.minimum_payment) },
        ]}
      />

      <section className="card">
        <div className="card-heading">
          <div>
            <p className="eyebrow">PAYOFF PLAN</p>
            <h3>How fast can I be debt-free?</h3>
          </div>
        </div>

        <div className="filters">
          <label className="inline-label">
            Extra per month
            <input
              type="number"
              step="1"
              min="0"
              value={extra}
              onChange={(e) => setExtra(e.target.value)}
            />
          </label>
          <label className="inline-label">
            Strategy
            <select
              value={strategy}
              onChange={(e) => setStrategy(e.target.value as 'avalanche' | 'snowball')}
            >
              <option value="avalanche">Avalanche (highest APR first)</option>
              <option value="snowball">Snowball (smallest balance first)</option>
            </select>
          </label>
          <button className="primary-button" onClick={calculate}>
            Calculate
          </button>
        </div>

        <Alert message={planError} />

        {plan && (
          <div className="spaced-top">
            {plan.message && <Alert message={plan.message} />}

            <section className="stats four-stats">
              <StatCard
                label="Debt-free in"
                value={months(plan.months_to_payoff)}
                hint={plan.payoff_month ?? undefined}
                tone="good"
              />
              <StatCard label="Monthly payment" value={formatMoney(plan.monthly_payment)} />
              <StatCard label="Total interest" value={formatMoney(plan.total_interest)} />
              <StatCard
                label="Interest saved"
                value={formatMoney(plan.interest_saved)}
                hint={`vs minimums only (${months(plan.baseline_months)})`}
                tone="good"
              />
            </section>

            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Order</th>
                    <th>Debt</th>
                    <th className="num">APR</th>
                    <th className="num">Balance</th>
                    <th className="num">Paid off in</th>
                    <th className="num">Interest</th>
                  </tr>
                </thead>
                <tbody>
                  {plan.debts.map((d) => (
                    <tr key={d.debt_id}>
                      <td>{d.order}</td>
                      <td>{d.name}</td>
                      <td className="num">{d.apr}%</td>
                      <td className="num">{formatMoney(d.starting_balance)}</td>
                      <td className="num">{months(d.months_to_payoff)}</td>
                      <td className="num">{formatMoney(d.interest_paid)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </section>
    </>
  )
}

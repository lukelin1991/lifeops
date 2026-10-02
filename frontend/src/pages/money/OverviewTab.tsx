import { useCallback, useState } from 'react'
import { moneyApi } from '../../api/money'
import { Alert } from '../../components/Alert'
import { SpendingChart } from '../../components/SpendingChart'
import { StatCard } from '../../components/StatCard'
import { useApiData } from '../../hooks/useApiData'
import { currentMonthString, formatDate, formatMoney, monthLabel } from '../../utils/format'

export function OverviewTab() {
  const [month, setMonth] = useState(currentMonthString())
  const [year, monthNumber] = month.split('-').map(Number)

  const loader = useCallback(
    () => moneyApi.summary(year, monthNumber),
    [year, monthNumber],
  )
  const { data: summary, error } = useApiData(loader)

  return (
    <>
      <div className="toolbar">
        <label className="inline-label">
          Month
          <input
            type="month"
            value={month}
            onChange={(event) => event.target.value && setMonth(event.target.value)}
          />
        </label>
      </div>

      <Alert message={error} />

      {summary && (
        <>
          <section className="stats four-stats">
            <StatCard label="Income" value={formatMoney(summary.income)} tone="good" />
            <StatCard label="Spending" value={formatMoney(summary.spending)} />
            <StatCard
              label="Net"
              value={formatMoney(summary.net)}
              tone={summary.net < 0 ? 'bad' : 'good'}
            />
            <StatCard
              label="Budget Remaining"
              value={formatMoney(summary.budget_remaining)}
              hint={`of ${formatMoney(summary.total_budget)} budgeted`}
              tone={summary.budget_remaining < 0 ? 'bad' : 'neutral'}
            />
          </section>

          <section className="card">
            <div className="card-heading">
              <div>
                <p className="eyebrow">SPENDING BY CATEGORY</p>
                <h3>{monthLabel(summary.year, summary.month)}</h3>
              </div>
            </div>

            <SpendingChart rows={summary.by_category} />

            {summary.by_category.length > 0 && (
              <div className="table-wrap spaced-top">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Category</th>
                      <th className="num">Spent</th>
                      <th className="num">Budget</th>
                      <th className="num">Remaining</th>
                    </tr>
                  </thead>
                  <tbody>
                    {summary.by_category.map((row) => (
                      <tr key={row.category_id ?? 'none'}>
                        <td>
                          {row.category_name}{' '}
                          {row.over_budget && (
                            <span className="badge over-badge">Over</span>
                          )}
                        </td>
                        <td className="num">{formatMoney(row.spent)}</td>
                        <td className="num">{formatMoney(row.budget)}</td>
                        <td className={row.over_budget ? 'num negative' : 'num'}>
                          {formatMoney(row.remaining)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="card">
            <div className="card-heading">
              <div>
                <p className="eyebrow">COMING UP</p>
                <h3>Bills due before {formatDate(summary.bills_before)}</h3>
              </div>
              <span className="entry-count">
                {formatMoney(summary.upcoming_bills_total)}
              </span>
            </div>

            {summary.upcoming_bills.length === 0 ? (
              <p className="empty-state">No bills due in the next 30 days.</p>
            ) : (
              <ul className="simple-list">
                {summary.upcoming_bills.map((bill) => (
                  <li key={`${bill.bill_id}-${bill.due_date}`}>
                    <span className="list-time">{formatDate(bill.due_date)}</span>
                    <span>{bill.name}</span>
                    <strong>{formatMoney(bill.amount)}</strong>
                    {bill.autopay && <span className="badge planned-badge">Autopay</span>}
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </>
  )
}

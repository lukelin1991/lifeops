import { useCallback } from 'react'
import { Link } from 'react-router'
import { dashboardApi } from '../api/dashboard'
import { healthApi } from '../api/health'
import type { Dashboard as DashboardData, WeightEntry } from '../api/types'
import { Alert } from '../components/Alert'
import { AllocationChart } from '../components/AllocationChart'
import { Badge } from '../components/Badge'
import { PageHeader } from '../components/PageHeader'
import { StatCard } from '../components/StatCard'
import { ProgressBar } from '../components/health/ActiveGoalSummary'
import { WeightChart } from '../components/health/WeightChart'
import { useApiData } from '../hooks/useApiData'
import {
  formatDate,
  formatDateTimeShort,
  formatMoney,
  formatPercent,
  formatTime,
  monthLabel,
  titleCase,
} from '../utils/format'

type Loaded = { dashboard: DashboardData; weights: WeightEntry[] }

export default function Dashboard() {
  const loader = useCallback(async (): Promise<Loaded> => {
    const [dashboard, weights] = await Promise.all([
      dashboardApi.get(),
      healthApi.listWeights(),
    ])
    return { dashboard, weights: weights.data }
  }, [])

  const { data, error, loading, reload } = useApiData(loader)

  return (
    <>
      <PageHeader
        eyebrow="DASHBOARD"
        title="Today at a glance"
        description="Health, money, schedule, investments and career in one place."
        actions={
          <button className="secondary-button" onClick={reload}>
            Refresh
          </button>
        }
      />

      <Alert message={error} />
      {loading && !data && <p className="empty-state">Loading…</p>}

      {data && <DashboardCards {...data} />}
    </>
  )
}

function DashboardCards({ dashboard, weights }: Loaded) {
  const { health, money, calendar, invest, career } = dashboard
  const recentWeights = weights.slice(-12)

  return (
    <>
      <section className="stats four-stats">
        <StatCard
          label="Current Weight"
          value={health.latest_weight !== null ? `${health.latest_weight} lbs` : '—'}
          hint={
            health.goal_progress
              ? `${health.goal_progress.progress_percentage}% to ${health.goal_progress.goal_weight} lbs`
              : 'No active goal'
          }
        />
        <StatCard
          label={`Spent in ${monthLabel(money.year, money.month)}`}
          value={formatMoney(money.spending)}
          hint={
            money.total_budget > 0
              ? `${formatMoney(money.budget_remaining)} left of ${formatMoney(money.total_budget)}`
              : 'No budgets set'
          }
          tone={money.total_budget > 0 && money.budget_remaining < 0 ? 'bad' : 'neutral'}
        />
        <StatCard
          label="Portfolio Value"
          value={invest.summary ? formatMoney(invest.summary.market_value) : '—'}
          hint={
            invest.summary
              ? `${formatPercent(invest.summary.gain_loss_pct)} overall`
              : 'Prices unavailable'
          }
          tone={
            invest.summary && invest.summary.gain_loss < 0 ? 'bad'
              : invest.summary && invest.summary.gain_loss > 0 ? 'good'
                : 'neutral'
          }
        />
        <StatCard
          label="Active Applications"
          value={career.active}
          hint={`${career.upcoming_interviews.length} interviews in the next 2 weeks`}
        />
      </section>

      <div className="two-column">
        <section className="card">
          <div className="card-heading">
            <div>
              <p className="eyebrow">HEALTH</p>
              <h3>Weight trend</h3>
            </div>
            <Link className="text-link" to="/health">Open Health →</Link>
          </div>

          {recentWeights.length === 0 ? (
            <p className="empty-state">No weights recorded yet.</p>
          ) : (
            <WeightChart weights={recentWeights} height={200} />
          )}

          {health.goal_progress && (
            <div className="spaced-top">
              <ProgressBar progress={health.goal_progress} />
            </div>
          )}
        </section>

        <section className="card">
          <div className="card-heading">
            <div>
              <p className="eyebrow">TODAY</p>
              <h3>{formatDate(calendar.date)}</h3>
            </div>
            <Link className="text-link" to="/calendar">Open Calendar →</Link>
          </div>

          {calendar.events.length === 0 &&
            calendar.tasks.length === 0 &&
            calendar.overdue_tasks.length === 0 && (
              <p className="empty-state">Nothing scheduled today.</p>
            )}

          <ul className="simple-list">
            {calendar.events.map((event) => (
              <li key={`e${event.id}`}>
                <span className="list-time">
                  {event.all_day ? 'All day' : formatTime(event.start_at)}
                </span>
                <span>{event.title}</span>
                {event.location && <small>{event.location}</small>}
              </li>
            ))}
            {calendar.overdue_tasks.map((task) => (
              <li key={`o${task.id}`}>
                <span className="list-time overdue">Overdue</span>
                <span>{task.title}</span>
                <Badge value={task.priority} group="priority" />
              </li>
            ))}
            {calendar.tasks.map((task) => (
              <li key={`t${task.id}`}>
                <span className="list-time">Task</span>
                <span>{task.title}</span>
                <Badge value={task.priority} group="priority" />
              </li>
            ))}
          </ul>
        </section>
      </div>

      <div className="two-column">
        <section className="card">
          <div className="card-heading">
            <div>
              <p className="eyebrow">MONEY</p>
              <h3>Upcoming bills (14 days)</h3>
            </div>
            <Link className="text-link" to="/money">Open Money →</Link>
          </div>

          {money.over_budget_categories.length > 0 && (
            <div className="alert error-alert">
              Over budget:{' '}
              {money.over_budget_categories
                .map((row) => `${row.category_name} (${formatMoney(row.remaining)})`)
                .join(', ')}
            </div>
          )}

          {money.upcoming_bills.length === 0 ? (
            <p className="empty-state">No bills due in the next two weeks.</p>
          ) : (
            <ul className="simple-list">
              {money.upcoming_bills.map((bill) => (
                <li key={`${bill.bill_id}-${bill.due_date}`}>
                  <span className="list-time">{formatDate(bill.due_date)}</span>
                  <span>{bill.name}</span>
                  <strong>{formatMoney(bill.amount)}</strong>
                  {bill.autopay && <span className="badge planned-badge">Autopay</span>}
                </li>
              ))}
              <li className="list-total">
                <span>Total</span>
                <strong>{formatMoney(money.upcoming_bills_total)}</strong>
              </li>
            </ul>
          )}
        </section>

        <section className="card">
          <div className="card-heading">
            <div>
              <p className="eyebrow">INVEST</p>
              <h3>Allocation</h3>
            </div>
            <Link className="text-link" to="/invest">Open Invest →</Link>
          </div>

          {invest.status !== 'ok' && (
            <p className="muted">
              {invest.status === 'partial'
                ? 'Some prices are missing (API key not set or provider unavailable). Totals only include priced holdings.'
                : 'Prices are unavailable right now.'}
            </p>
          )}

          {invest.summary && <AllocationChart allocation={invest.summary.allocation} />}
        </section>
      </div>

      <section className="card">
        <div className="card-heading">
          <div>
            <p className="eyebrow">CAREER</p>
            <h3>Job search pipeline</h3>
          </div>
          <Link className="text-link" to="/career">Open Career →</Link>
        </div>

        <div className="pipeline">
          {Object.entries(career.counts).map(([status, count]) => (
            <div key={status} className={`pipeline-step status-${status}`}>
              <strong>{count}</strong>
              <span>{titleCase(status)}</span>
            </div>
          ))}
        </div>

        {career.upcoming_interviews.length > 0 && (
          <ul className="simple-list spaced-top">
            {career.upcoming_interviews.map((interview) => (
              <li key={interview.id}>
                <span className="list-time">
                  {formatDateTimeShort(interview.scheduled_at)}
                </span>
                <span>
                  {interview.company} — {titleCase(interview.stage)}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </>
  )
}

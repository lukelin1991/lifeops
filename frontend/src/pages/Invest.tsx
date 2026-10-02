import { useCallback } from 'react'
import { investApi } from '../api/invest'
import type { PriceStatus, PricedHolding, WatchlistItem } from '../api/types'
import { Alert } from '../components/Alert'
import { AllocationChart } from '../components/AllocationChart'
import { PageHeader } from '../components/PageHeader'
import { ResourceManager } from '../components/ResourceManager'
import { StatCard } from '../components/StatCard'
import { useApiData } from '../hooks/useApiData'
import {
  formatMoney,
  formatNumber,
  formatPercent,
  formatPrice,
} from '../utils/format'
import { options, type FieldDef } from '../utils/forms'

const HOLDING_FIELDS: FieldDef[] = [
  { name: 'symbol', label: 'Symbol', required: true, placeholder: 'AAPL or BTC' },
  {
    name: 'asset_type', label: 'Type', type: 'select', required: true,
    options: options(['stock', 'crypto']), defaultValue: 'stock',
  },
  { name: 'name', label: 'Name' },
  { name: 'quantity', label: 'Quantity', type: 'number', required: true },
  { name: 'avg_cost', label: 'Average cost per unit', type: 'number', required: true },
  { name: 'notes', label: 'Notes', type: 'textarea' },
]

// Symbol and type identify a holding, so they can't be edited.
const HOLDING_EDIT_FIELDS = HOLDING_FIELDS.filter(
  (field) => field.name !== 'symbol' && field.name !== 'asset_type',
)

const WATCH_FIELDS: FieldDef[] = [
  { name: 'symbol', label: 'Symbol', required: true },
  {
    name: 'asset_type', label: 'Type', type: 'select', required: true,
    options: options(['stock', 'crypto']), defaultValue: 'stock',
  },
  { name: 'target_price', label: 'Target buy price', type: 'number' },
  { name: 'notes', label: 'Notes', type: 'textarea' },
]

const WATCH_EDIT_FIELDS = WATCH_FIELDS.filter(
  (field) => field.name !== 'symbol' && field.name !== 'asset_type',
)

const STATUS_TEXT: Record<PriceStatus, string> = {
  ok: 'Live',
  missing_api_key: 'No API key',
  not_found: 'Unknown symbol',
  unavailable: 'Unavailable',
}

function PriceCell({ price, status, message }: {
  price: number | null | undefined
  status?: PriceStatus
  message?: string | null
}) {
  if (price !== null && price !== undefined) return <>{formatPrice(price)}</>

  return (
    <span className="badge price-missing" title={message ?? undefined}>
      {status ? STATUS_TEXT[status] : '—'}
    </span>
  )
}

function gainClass(value: number | null) {
  if (value === null) return 'num'
  return value < 0 ? 'num negative' : 'num positive'
}

export default function Invest() {
  const portfolioLoader = useCallback(() => investApi.portfolio(), [])
  const portfolio = useApiData(portfolioLoader)

  const watchLoader = useCallback(() => investApi.watchlistWithPrices(), [])
  const watchlist = useApiData(watchLoader)

  const summary = portfolio.data?.summary
  const missingKeys = portfolio.data?.holdings.some(
    (h) => h.price_status === 'missing_api_key',
  )

  return (
    <>
      <PageHeader
        eyebrow="INVEST"
        title="Portfolio"
        description="Holdings, allocation and a watchlist. Prices come from Twelve Data (stocks) and CoinGecko (crypto) via the backend, cached for about a minute."
        actions={
          <button className="secondary-button" onClick={portfolio.reload}>
            Refresh prices
          </button>
        }
      />

      <Alert message={portfolio.error || watchlist.error} />
      {missingKeys && (
        <Alert
          kind="info"
          message="Some prices are missing because TWELVE_DATA_API_KEY or COINGECKO_API_KEY isn't set in backend/.env. Both have free tiers."
        />
      )}

      {summary && (
        <div className="two-column">
          <section className="stats two-stats">
            <StatCard label="Market value" value={formatMoney(summary.market_value)} />
            <StatCard label="Cost basis" value={formatMoney(summary.cost_basis)} />
            <StatCard
              label="Gain / loss"
              value={formatMoney(summary.gain_loss)}
              hint={formatPercent(summary.gain_loss_pct)}
              tone={summary.gain_loss < 0 ? 'bad' : summary.gain_loss > 0 ? 'good' : 'neutral'}
            />
            <StatCard
              label="Priced holdings"
              value={`${summary.priced_count} / ${summary.holdings_count}`}
              hint={summary.complete ? 'All prices loaded' : 'Totals exclude unpriced holdings'}
            />
          </section>

          <section className="card">
            <div className="card-heading">
              <div>
                <p className="eyebrow">ALLOCATION</p>
                <h3>Stocks vs crypto</h3>
              </div>
            </div>
            <AllocationChart allocation={summary.allocation} height={220} />
          </section>
        </div>
      )}

      <ResourceManager<PricedHolding>
        eyebrow="HOLDINGS"
        title="What I own"
        addLabel="Add holding"
        items={portfolio.data?.holdings ?? []}
        fields={HOLDING_FIELDS}
        editFields={HOLDING_EDIT_FIELDS}
        onCreate={investApi.holdings.create}
        onUpdate={investApi.holdings.update}
        onDelete={investApi.holdings.remove}
        onChanged={portfolio.reload}
        emptyText="No holdings yet."
        columns={[
          {
            label: 'Symbol',
            render: (h) => (
              <>
                <strong>{h.symbol}</strong>{' '}
                <small className="muted">{h.asset_type}</small>
              </>
            ),
          },
          { label: 'Qty', className: 'num', render: (h) => formatNumber(h.quantity) },
          { label: 'Avg cost', className: 'num', render: (h) => formatPrice(h.avg_cost) },
          {
            label: 'Price',
            className: 'num',
            render: (h) => (
              <PriceCell price={h.price} status={h.price_status} message={h.price_message} />
            ),
          },
          { label: 'Value', className: 'num', render: (h) => formatMoney(h.market_value) },
          {
            label: 'Gain',
            className: 'num',
            render: (h) => (
              <span className={gainClass(h.gain_loss)}>
                {formatMoney(h.gain_loss)} <small>{formatPercent(h.gain_loss_pct)}</small>
              </span>
            ),
          },
        ]}
      />

      <ResourceManager<WatchlistItem>
        eyebrow="WATCHLIST"
        title="Keeping an eye on"
        addLabel="Watch symbol"
        items={watchlist.data ?? []}
        fields={WATCH_FIELDS}
        editFields={WATCH_EDIT_FIELDS}
        onCreate={investApi.watchlist.create}
        onUpdate={investApi.watchlist.update}
        onDelete={investApi.watchlist.remove}
        onChanged={watchlist.reload}
        emptyText="Watchlist is empty."
        columns={[
          {
            label: 'Symbol',
            render: (w) => (
              <>
                <strong>{w.symbol}</strong>{' '}
                <small className="muted">{w.asset_type}</small>
              </>
            ),
          },
          {
            label: 'Price',
            className: 'num',
            render: (w) => (
              <PriceCell price={w.price} status={w.price_status} message={w.price_message} />
            ),
          },
          { label: 'Target', className: 'num', render: (w) => formatPrice(w.target_price) },
          {
            label: '',
            render: (w) =>
              w.below_target ? <span className="badge active-badge">At/below target</span> : null,
          },
        ]}
      />
    </>
  )
}

import { useCallback, useMemo, useState } from 'react'
import { moneyApi } from '../../api/money'
import type { Account, Category, Transaction } from '../../api/types'
import { Alert } from '../../components/Alert'
import { ResourceManager } from '../../components/ResourceManager'
import { useApiData } from '../../hooks/useApiData'
import { formatDate, formatMoney, todayString } from '../../utils/format'
import { options, type FieldDef } from '../../utils/forms'

type Props = { categories: Category[]; accounts: Account[] }

export function TransactionsTab({ categories, accounts }: Props) {
  const [filters, setFilters] = useState({
    start_date: '',
    end_date: '',
    category_id: '',
    transaction_type: '',
  })

  const loader = useCallback(
    () => moneyApi.transactions.list(filters),
    [filters],
  )
  const { data, error, reload } = useApiData(loader)

  const fields: FieldDef[] = useMemo(() => [
    {
      name: 'transaction_type', label: 'Type', type: 'select', required: true,
      options: options(['expense', 'income']), defaultValue: 'expense',
    },
    { name: 'amount', label: 'Amount', type: 'number', step: '0.01', required: true },
    {
      name: 'transaction_date', label: 'Date', type: 'date', required: true,
      defaultValue: todayString(),
    },
    { name: 'merchant', label: 'Merchant' },
    {
      name: 'category_id', label: 'Category', type: 'select',
      options: categories.map((c) => ({ value: String(c.id), label: c.name })),
    },
    {
      name: 'account_id', label: 'Account', type: 'select',
      options: accounts.map((a) => ({ value: String(a.id), label: a.name })),
    },
    { name: 'notes', label: 'Notes', type: 'textarea' },
  ], [categories, accounts])

  function setFilter(name: keyof typeof filters, value: string) {
    setFilters({ ...filters, [name]: value })
  }

  return (
    <>
      <Alert message={error} />
      <ResourceManager<Transaction>
        eyebrow="TRANSACTIONS"
        title="Income & Expenses"
        addLabel="Add transaction"
        items={data ?? []}
        fields={fields}
        onCreate={moneyApi.transactions.create}
        onUpdate={moneyApi.transactions.update}
        onDelete={moneyApi.transactions.remove}
        onChanged={reload}
        emptyText="No transactions match these filters."
        toolbar={
          <div className="filters">
            <label className="inline-label">
              From
              <input
                type="date"
                value={filters.start_date}
                onChange={(e) => setFilter('start_date', e.target.value)}
              />
            </label>
            <label className="inline-label">
              To
              <input
                type="date"
                value={filters.end_date}
                onChange={(e) => setFilter('end_date', e.target.value)}
              />
            </label>
            <label className="inline-label">
              Category
              <select
                value={filters.category_id}
                onChange={(e) => setFilter('category_id', e.target.value)}
              >
                <option value="">All</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </label>
            <label className="inline-label">
              Type
              <select
                value={filters.transaction_type}
                onChange={(e) => setFilter('transaction_type', e.target.value)}
              >
                <option value="">All</option>
                <option value="expense">Expense</option>
                <option value="income">Income</option>
              </select>
            </label>
          </div>
        }
        columns={[
          { label: 'Date', render: (t) => formatDate(t.transaction_date) },
          { label: 'Merchant', render: (t) => t.merchant ?? '—' },
          { label: 'Category', render: (t) => t.category_name ?? 'Uncategorized' },
          {
            label: 'Amount',
            className: 'num',
            render: (t) => (
              <span className={t.transaction_type === 'income' ? 'positive' : undefined}>
                {t.transaction_type === 'income' ? '+' : '−'}
                {formatMoney(t.amount)}
              </span>
            ),
          },
        ]}
      />
    </>
  )
}

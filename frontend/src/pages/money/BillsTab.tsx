import { useCallback, useMemo } from 'react'
import { moneyApi } from '../../api/money'
import type { Bill, Category } from '../../api/types'
import { Alert } from '../../components/Alert'
import { ResourceManager } from '../../components/ResourceManager'
import { useApiData } from '../../hooks/useApiData'
import { formatDate, formatMoney, titleCase, todayString } from '../../utils/format'
import { options, type FieldDef } from '../../utils/forms'

export function BillsTab({ categories }: { categories: Category[] }) {
  const loader = useCallback(() => moneyApi.bills.list(), [])
  const { data, error, reload } = useApiData(loader)

  const fields: FieldDef[] = useMemo(() => [
    { name: 'name', label: 'Name', required: true },
    { name: 'amount', label: 'Amount', type: 'number', step: '0.01', required: true },
    { name: 'due_day', label: 'Due day (1-31)', type: 'number', step: '1', required: true },
    {
      name: 'frequency', label: 'Frequency', type: 'select', required: true,
      options: options(['monthly', 'quarterly', 'yearly']), defaultValue: 'monthly',
    },
    {
      name: 'start_date', label: 'First due month', type: 'date',
      defaultValue: todayString(),
    },
    {
      name: 'category_id', label: 'Category', type: 'select',
      options: categories.map((c) => ({ value: String(c.id), label: c.name })),
    },
    { name: 'autopay', label: 'Autopay', type: 'checkbox' },
    { name: 'is_active', label: 'Active', type: 'checkbox', defaultValue: true },
    { name: 'notes', label: 'Notes', type: 'textarea' },
  ], [categories])

  return (
    <>
      <Alert message={error} />
      <ResourceManager<Bill>
        eyebrow="RECURRING"
        title="Bills"
        addLabel="Add bill"
        items={data ?? []}
        fields={fields}
        onCreate={moneyApi.bills.create}
        onUpdate={moneyApi.bills.update}
        onDelete={moneyApi.bills.remove}
        onChanged={reload}
        emptyText="No recurring bills yet."
        columns={[
          { label: 'Name', render: (b) => b.name },
          { label: 'Amount', className: 'num', render: (b) => formatMoney(b.amount) },
          { label: 'Schedule', render: (b) => `${titleCase(b.frequency)} on day ${b.due_day}` },
          {
            label: 'Next due',
            render: (b) => (b.is_active ? formatDate(b.next_due_date) : 'Inactive'),
          },
          {
            label: 'Autopay',
            render: (b) => (b.autopay ? <span className="badge active-badge">Yes</span> : 'No'),
          },
        ]}
      />
    </>
  )
}

import { useCallback, useMemo, useState } from 'react'
import { describeError } from '../../api/client'
import { moneyApi } from '../../api/money'
import type { Budget, Category } from '../../api/types'
import { Alert } from '../../components/Alert'
import { ResourceManager } from '../../components/ResourceManager'
import { useApiData } from '../../hooks/useApiData'
import { currentMonthString, formatMoney, monthLabel } from '../../utils/format'
import type { FieldDef } from '../../utils/forms'

export function BudgetsTab({ categories }: { categories: Category[] }) {
  const [month, setMonth] = useState(currentMonthString())
  const [year, monthNumber] = month.split('-').map(Number)
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')

  const loader = useCallback(
    () => moneyApi.budgets.list({ year, month: monthNumber }),
    [year, monthNumber],
  )
  const { data, error: loadError, reload } = useApiData(loader)

  const expenseCategories = useMemo(
    () => categories.filter((c) => c.kind === 'expense'),
    [categories],
  )

  const createFields: FieldDef[] = useMemo(() => [
    {
      name: 'category_id', label: 'Category', type: 'select', required: true,
      options: expenseCategories.map((c) => ({ value: String(c.id), label: c.name })),
      defaultValue: expenseCategories[0] ? String(expenseCategories[0].id) : '',
    },
    { name: 'amount', label: 'Monthly amount', type: 'number', step: '0.01', required: true },
  ], [expenseCategories])

  const editFields: FieldDef[] = [
    { name: 'amount', label: 'Monthly amount', type: 'number', step: '0.01', required: true },
  ]

  async function copyToNextMonth() {
    setNotice('')
    setError('')
    try {
      const result = await moneyApi.copyBudgets(year, monthNumber)
      setNotice(result.message ?? 'Copied.')
    } catch (err) {
      setError(describeError(err))
    }
  }

  return (
    <>
      <Alert message={loadError || error} />
      <Alert message={notice} kind="success" />

      <ResourceManager<Budget>
        eyebrow="BUDGETS"
        title={`Budgets for ${monthLabel(year, monthNumber)}`}
        addLabel="Add budget"
        items={data ?? []}
        fields={createFields}
        editFields={editFields}
        onCreate={(payload) =>
          moneyApi.budgets.create({ ...payload, year, month: monthNumber })
        }
        onUpdate={moneyApi.budgets.update}
        onDelete={moneyApi.budgets.remove}
        onChanged={reload}
        emptyText={
          categories.length === 0
            ? 'Create some categories first (Accounts & Categories tab).'
            : 'No budgets for this month yet.'
        }
        toolbar={
          <div className="filters">
            <label className="inline-label">
              Month
              <input
                type="month"
                value={month}
                onChange={(e) => e.target.value && setMonth(e.target.value)}
              />
            </label>
            <button className="secondary-button" onClick={copyToNextMonth}>
              Copy to next month
            </button>
          </div>
        }
        columns={[
          { label: 'Category', render: (b) => b.category_name ?? '—' },
          { label: 'Amount', className: 'num', render: (b) => formatMoney(b.amount) },
        ]}
      />
    </>
  )
}

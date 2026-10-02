import { useCallback, useState } from 'react'
import { moneyApi } from '../api/money'
import { Alert } from '../components/Alert'
import { PageHeader } from '../components/PageHeader'
import { Tabs } from '../components/Tabs'
import { useApiData } from '../hooks/useApiData'
import { BillsTab } from './money/BillsTab'
import { BudgetsTab } from './money/BudgetsTab'
import { DebtsTab } from './money/DebtsTab'
import { OverviewTab } from './money/OverviewTab'
import { SetupTab } from './money/SetupTab'
import { TransactionsTab } from './money/TransactionsTab'

type TabId = 'overview' | 'transactions' | 'budgets' | 'bills' | 'debts' | 'setup'

const TABS: { id: TabId; label: string }[] = [
  { id: 'overview', label: 'Overview' },
  { id: 'transactions', label: 'Transactions' },
  { id: 'budgets', label: 'Budgets' },
  { id: 'bills', label: 'Bills' },
  { id: 'debts', label: 'Debts' },
  { id: 'setup', label: 'Accounts & Categories' },
]

export default function Money() {
  const [tab, setTab] = useState<TabId>('overview')

  // Categories and accounts feed the dropdowns on several tabs.
  const loader = useCallback(async () => {
    const [categories, accounts] = await Promise.all([
      moneyApi.categories.list(),
      moneyApi.accounts.list(),
    ])
    return { categories, accounts }
  }, [])

  const { data, error, reload } = useApiData(loader)
  const categories = data?.categories ?? []
  const accounts = data?.accounts ?? []

  return (
    <>
      <PageHeader
        eyebrow="MONEY"
        title="Budget & Bills"
        description="Track spending against monthly budgets, stay ahead of bills and plan your debt payoff."
      />

      <Tabs tabs={TABS} active={tab} onChange={setTab} />
      <Alert message={error} />

      {tab === 'overview' && <OverviewTab />}
      {tab === 'transactions' && (
        <TransactionsTab categories={categories} accounts={accounts} />
      )}
      {tab === 'budgets' && <BudgetsTab categories={categories} />}
      {tab === 'bills' && <BillsTab categories={categories} />}
      {tab === 'debts' && <DebtsTab />}
      {tab === 'setup' && (
        <SetupTab categories={categories} accounts={accounts} onChanged={reload} />
      )}
    </>
  )
}

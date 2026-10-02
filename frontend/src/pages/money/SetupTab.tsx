import { moneyApi } from '../../api/money'
import type { Account, Category } from '../../api/types'
import { ResourceManager } from '../../components/ResourceManager'
import { formatMoney, titleCase } from '../../utils/format'
import { options, type FieldDef } from '../../utils/forms'

const CATEGORY_FIELDS: FieldDef[] = [
  { name: 'name', label: 'Name', required: true },
  {
    name: 'kind', label: 'Kind', type: 'select', required: true,
    options: options(['expense', 'income']), defaultValue: 'expense',
  },
]

const ACCOUNT_FIELDS: FieldDef[] = [
  { name: 'name', label: 'Name', required: true },
  {
    name: 'account_type', label: 'Type', type: 'select', required: true,
    options: options(['checking', 'savings', 'credit_card', 'cash', 'investment', 'other']),
    defaultValue: 'checking',
  },
  { name: 'institution', label: 'Institution' },
  { name: 'balance', label: 'Balance', type: 'number', step: '0.01', defaultValue: '0' },
]

type Props = {
  categories: Category[]
  accounts: Account[]
  onChanged: () => void
}

export function SetupTab({ categories, accounts, onChanged }: Props) {
  return (
    <div className="two-column">
      <ResourceManager<Category>
        eyebrow="CATEGORIES"
        title="Categories"
        items={categories}
        fields={CATEGORY_FIELDS}
        onCreate={moneyApi.categories.create}
        onUpdate={moneyApi.categories.update}
        onDelete={moneyApi.categories.remove}
        onChanged={onChanged}
        deleteConfirm={(c) =>
          `Delete "${c.name}"? Its transactions are kept (uncategorized) and its budgets are removed.`
        }
        columns={[
          { label: 'Name', render: (c) => c.name },
          { label: 'Kind', render: (c) => titleCase(c.kind) },
        ]}
      />

      <ResourceManager<Account>
        eyebrow="ACCOUNTS"
        title="Accounts"
        items={accounts}
        fields={ACCOUNT_FIELDS}
        onCreate={moneyApi.accounts.create}
        onUpdate={moneyApi.accounts.update}
        onDelete={moneyApi.accounts.remove}
        onChanged={onChanged}
        columns={[
          { label: 'Name', render: (a) => a.name },
          { label: 'Type', render: (a) => titleCase(a.account_type) },
          { label: 'Balance', className: 'num', render: (a) => formatMoney(a.balance) },
        ]}
      />
    </div>
  )
}

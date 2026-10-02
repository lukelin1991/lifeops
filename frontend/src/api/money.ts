import { api, type Envelope } from './client'
import { crudApi } from './crud'
import type {
  Account,
  Bill,
  Budget,
  Category,
  Debt,
  DebtPayoff,
  MonthlySummary,
  Transaction,
} from './types'

export const moneyApi = {
  accounts: crudApi<Account>('/money/accounts'),
  categories: crudApi<Category>('/money/categories'),
  transactions: crudApi<Transaction>('/money/transactions'),
  budgets: crudApi<Budget>('/money/budgets'),
  bills: crudApi<Bill>('/money/bills'),
  debts: crudApi<Debt>('/money/debts'),

  copyBudgets: (fromYear: number, fromMonth: number) =>
    api.post<Envelope<Budget[]>>('/money/budgets/copy', undefined, {
      from_year: fromYear,
      from_month: fromMonth,
    }),

  payoff: (extraPayment: number, strategy: 'avalanche' | 'snowball') =>
    api.get<DebtPayoff>('/money/debts/payoff', {
      extra_payment: extraPayment,
      strategy,
    }),

  summary: (year: number, month: number) =>
    api.get<MonthlySummary>('/money/summary', { year, month }),
}

// Shapes returned by the LifeOps API. Money values are JSON numbers.

// ---------- Health ----------
export type WeightEntry = {
  id: number
  weight: number
  measurement_date: string
  created_at: string
}

export type WeightGoal = {
  id: number
  starting_weight: number
  goal_weight: number
  status: 'planned' | 'active' | 'completed'
  created_at: string
  activated_at: string | null
  completed_at: string | null
}

export type WeightProgress = {
  goal_id: number
  starting_weight: number
  current_weight: number
  goal_weight: number
  change_from_start: number
  weight_remaining: number
  progress_percentage: number
  status: 'starting' | 'progress' | 'above_start' | 'goal_reached'
  goal_activated_at: string
  latest_measurement_date: string
}

// ---------- Money ----------
export type Account = {
  id: number
  name: string
  account_type: string
  institution: string | null
  balance: number
  created_at: string
}

export type Category = {
  id: number
  name: string
  kind: 'expense' | 'income'
  created_at: string
}

export type Transaction = {
  id: number
  transaction_type: 'income' | 'expense'
  amount: number
  transaction_date: string
  merchant: string | null
  category_id: number | null
  category_name: string | null
  account_id: number | null
  notes: string | null
  created_at: string
}

export type Budget = {
  id: number
  category_id: number
  category_name: string | null
  year: number
  month: number
  amount: number
  created_at: string
}

export type Bill = {
  id: number
  name: string
  amount: number
  due_day: number
  frequency: 'monthly' | 'quarterly' | 'yearly'
  start_date: string
  autopay: boolean
  is_active: boolean
  category_id: number | null
  notes: string | null
  created_at: string
  next_due_date: string | null
}

export type Debt = {
  id: number
  name: string
  balance: number
  apr: number
  minimum_payment: number
  notes: string | null
  created_at: string
}

export type DebtPayoff = {
  strategy: 'avalanche' | 'snowball'
  extra_payment: number
  monthly_payment: number
  feasible: boolean
  months_to_payoff: number | null
  payoff_month: string | null
  total_interest: number
  total_paid: number
  debts: {
    debt_id: number
    name: string
    order: number
    starting_balance: number
    apr: number
    months_to_payoff: number | null
    interest_paid: number
  }[]
  baseline_months: number | null
  baseline_total_interest: number | null
  interest_saved: number | null
  message: string | null
}

export type CategorySpending = {
  category_id: number | null
  category_name: string
  spent: number
  budget: number | null
  remaining: number | null
  over_budget: boolean
}

export type UpcomingBill = {
  bill_id: number
  name: string
  amount: number
  due_date: string
  autopay: boolean
}

export type MonthlySummary = {
  year: number
  month: number
  income: number
  spending: number
  net: number
  total_budget: number
  budget_remaining: number
  by_category: CategorySpending[]
  upcoming_bills: UpcomingBill[]
  upcoming_bills_total: number
  bills_before: string
}

// ---------- Calendar ----------
export type CalendarEvent = {
  id: number
  title: string
  start_at: string
  end_at: string | null
  all_day: boolean
  location: string | null
  notes: string | null
  created_at: string
}

export type Task = {
  id: number
  title: string
  due_date: string | null
  priority: 'low' | 'medium' | 'high'
  status: 'todo' | 'in_progress' | 'done'
  recurrence: 'none' | 'daily' | 'weekly' | 'monthly'
  notes: string | null
  completed_at: string | null
  created_at: string
}

export type Agenda = {
  start_date: string
  end_date: string
  events: CalendarEvent[]
  tasks: Task[]
  overdue_tasks: Task[]
}

// ---------- Invest ----------
export type PriceStatus =
  | 'ok'
  | 'missing_api_key'
  | 'not_found'
  | 'unavailable'

export type Holding = {
  id: number
  symbol: string
  asset_type: 'stock' | 'crypto'
  name: string | null
  quantity: number
  avg_cost: number
  notes: string | null
  created_at: string
}

export type PricedHolding = Holding & {
  price: number | null
  price_status: PriceStatus
  price_message: string | null
  cost_basis: number
  market_value: number | null
  gain_loss: number | null
  gain_loss_pct: number | null
}

export type PortfolioSummary = {
  market_value: number
  cost_basis: number
  priced_cost_basis: number
  gain_loss: number
  gain_loss_pct: number | null
  allocation: {
    asset_type: string
    market_value: number
    percent: number
  }[]
  holdings_count: number
  priced_count: number
  unpriced_count: number
  complete: boolean
}

export type Portfolio = {
  holdings: PricedHolding[]
  summary: PortfolioSummary
}

export type WatchlistItem = {
  id: number
  symbol: string
  asset_type: 'stock' | 'crypto'
  target_price: number | null
  notes: string | null
  created_at: string
  price?: number | null
  price_status?: PriceStatus
  price_message?: string | null
  below_target?: boolean | null
}

// ---------- Career ----------
export type ApplicationStatus =
  | 'applied'
  | 'screen'
  | 'interview'
  | 'offer'
  | 'rejected'
  | 'withdrawn'

export type JobApplication = {
  id: number
  company: string
  title: string
  url: string | null
  salary_min: number | null
  salary_max: number | null
  location: string | null
  work_mode: 'remote' | 'hybrid' | 'onsite'
  status: ApplicationStatus
  applied_date: string
  notes: string | null
  created_at: string
}

export type Interview = {
  id: number
  application_id: number
  scheduled_at: string
  stage: string
  outcome: 'pending' | 'passed' | 'failed'
  notes: string | null
  created_at: string
  company: string | null
  title: string | null
}

export type Contact = {
  id: number
  name: string
  company: string | null
  role: string | null
  email: string | null
  phone: string | null
  linkedin_url: string | null
  application_id: number | null
  notes: string | null
  created_at: string
}

export type Certification = {
  id: number
  name: string
  provider: string | null
  target_date: string | null
  status: 'planned' | 'in_progress' | 'completed'
  completed_date: string | null
  notes: string | null
  created_at: string
}

export type Pipeline = {
  counts: Record<ApplicationStatus, number>
  total: number
  active: number
  response_rate: number | null
  upcoming_interviews: Interview[]
}

// ---------- Dashboard ----------
export type Dashboard = {
  date: string
  health: {
    latest_weight: number | null
    latest_measurement_date: string | null
    goal_progress: WeightProgress | null
  }
  money: {
    year: number
    month: number
    income: number
    spending: number
    total_budget: number
    budget_remaining: number
    over_budget_categories: CategorySpending[]
    upcoming_bills: UpcomingBill[]
    upcoming_bills_total: number
  }
  calendar: {
    date: string
    events: CalendarEvent[]
    tasks: Task[]
    overdue_tasks: Task[]
  }
  invest: {
    status: 'ok' | 'partial' | 'unavailable'
    summary: PortfolioSummary | null
  }
  career: Pipeline
}

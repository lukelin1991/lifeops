import type { WeightGoal } from '../../api/types'
import { GoalRow, type GoalRowProps } from './GoalRow'

type GoalListProps = Omit<GoalRowProps, 'goal'> & {
  goals: WeightGoal[]
}

// Active goal first, then planned, then completed (same as before).
export function GoalList({ goals, ...rowProps }: GoalListProps) {
  const activeGoal =
    goals.find((goal) => goal.status === 'active') ?? null

  const plannedGoals = goals.filter(
    (goal) => goal.status === 'planned',
  )

  const completedGoals = goals.filter(
    (goal) => goal.status === 'completed',
  )

  return (
    <section className="card">
      <div className="card-heading">
        <div>
          <p className="eyebrow">GOALS</p>
          <h3>Goal Management</h3>
        </div>

        <span className="entry-count">
          {goals.length} goals
        </span>
      </div>

      {goals.length === 0 ? (
        <p className="empty-state">
          No goals created yet.
        </p>
      ) : (
        <div className="goal-list">
          {activeGoal && (
            <GoalRow goal={activeGoal} {...rowProps} />
          )}

          {plannedGoals.map((goal) => (
            <GoalRow key={goal.id} goal={goal} {...rowProps} />
          ))}

          {completedGoals.map((goal) => (
            <GoalRow key={goal.id} goal={goal} {...rowProps} />
          ))}
        </div>
      )}
    </section>
  )
}

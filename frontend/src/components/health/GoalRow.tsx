import type { WeightGoal } from '../../api/types'
import { formatDateTime } from '../../utils/format'

export type GoalRowProps = {
  goal: WeightGoal
  editingGoalId: number | null
  editStartingWeight: string
  editGoalWeight: string
  setEditStartingWeight: (value: string) => void
  setEditGoalWeight: (value: string) => void
  startEditingGoal: (goal: WeightGoal) => void
  cancelEditingGoal: () => void
  updateGoal: (id: number) => Promise<void>
  deleteGoal: (id: number) => Promise<void>
  activateGoal: (id: number) => Promise<void>
}

export function GoalRow({
  goal,
  editingGoalId,
  editStartingWeight,
  editGoalWeight,
  setEditStartingWeight,
  setEditGoalWeight,
  startEditingGoal,
  cancelEditingGoal,
  updateGoal,
  deleteGoal,
  activateGoal,
}: GoalRowProps) {
  return (
    <div className="goal-row">
      {editingGoalId === goal.id ? (
        <>
          <div className="edit-fields">
            <input
              type="number"
              step="0.1"
              value={editStartingWeight}
              onChange={(event) =>
                setEditStartingWeight(event.target.value)
              }
            />

            <input
              type="number"
              step="0.1"
              value={editGoalWeight}
              onChange={(event) =>
                setEditGoalWeight(event.target.value)
              }
            />
          </div>

          <div className="actions">
            <button
              className="save-button"
              onClick={() => updateGoal(goal.id)}
            >
              Save
            </button>

            <button
              className="secondary-button"
              onClick={cancelEditingGoal}
            >
              Cancel
            </button>
          </div>
        </>
      ) : (
        <>
          <div className="goal-info">
            <div className="goal-title-row">
              <strong>
                {goal.starting_weight} → {goal.goal_weight}{' '}
                lbs
              </strong>

              <span
                className={`badge ${goal.status}-badge`}
              >
                {goal.status}
              </span>
            </div>

            <p>
              Created {formatDateTime(goal.created_at)}
              {goal.completed_at &&
                ` • Completed ${formatDateTime(
                  goal.completed_at,
                )}`}
            </p>
          </div>

          <div className="actions">
            {goal.status === 'planned' && (
              <button
                className="activate-button"
                onClick={() => activateGoal(goal.id)}
              >
                Activate
              </button>
            )}

            {goal.status !== 'completed' && (
              <button
                className="secondary-button"
                onClick={() => startEditingGoal(goal)}
              >
                Edit
              </button>
            )}

            <button
              className="delete-button"
              onClick={() => deleteGoal(goal.id)}
            >
              Delete
            </button>
          </div>
        </>
      )}
    </div>
  )
}

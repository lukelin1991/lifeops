import type { WeightGoal, WeightProgress } from '../../api/types'
import { formatDate } from '../../utils/format'

type ActiveGoalSummaryProps = {
  activeGoal: WeightGoal | null
  progress: WeightProgress | null
  completeGoal: (id: number) => Promise<void>
}

function progressChangeText(progress: WeightProgress | null) {
  if (!progress) return '—'

  if (progress.change_from_start < 0) {
    return `${Math.abs(progress.change_from_start)} lbs lost`
  }

  if (progress.change_from_start > 0) {
    return `${progress.change_from_start} lbs above start`
  }

  return 'No change yet'
}

// Goal banner, the four stat cards and the progress bar
// (or the "No active weight goal" card).
export function ActiveGoalSummary({
  activeGoal,
  progress,
  completeGoal,
}: ActiveGoalSummaryProps) {
  if (!activeGoal || !progress) {
    return (
      <section className="card no-goal-card">
        <p className="eyebrow">CURRENT GOAL</p>
        <h3>No active weight goal</h3>
        <p>
          Create a goal below or activate one of your
          planned goals.
        </p>
      </section>
    )
  }

  return (
    <>
      <section className="goal-banner">
        <div>
          <div className="goal-title-row">
            <p className="eyebrow">ACTIVE GOAL</p>
            <span className="badge active-badge">
              Active
            </span>
          </div>

          <h3>
            {progress.starting_weight} lbs
            <span> → </span>
            {progress.goal_weight} lbs
          </h3>

          <p>
            Latest measurement:{' '}
            {formatDate(
              progress.latest_measurement_date,
            )}
          </p>
        </div>

        {progress.status === 'goal_reached' && (
          <button
            className="complete-button"
            onClick={() =>
              completeGoal(activeGoal.id)
            }
          >
            Complete Goal 🎉
          </button>
        )}
      </section>

      <section className="stats four-stats">
        <div className="stat-card">
          <span>Current Weight</span>
          <strong>
            {progress.current_weight} lbs
          </strong>
        </div>

        <div className="stat-card">
          <span>Change From Start</span>
          <strong>{progressChangeText(progress)}</strong>
        </div>

        <div className="stat-card">
          <span>Remaining</span>
          <strong>
            {progress.weight_remaining} lbs
          </strong>
        </div>

        <div className="stat-card">
          <span>Progress</span>
          <strong>
            {progress.progress_percentage}%
          </strong>
        </div>
      </section>

      <section className="card">
        <ProgressBar progress={progress} />
      </section>
    </>
  )
}

export function ProgressBar({ progress }: { progress: WeightProgress }) {
  return (
    <>
      <div className="progress-heading">
        <span>
          {progress.starting_weight} lbs
        </span>
        <strong>
          {progress.progress_percentage}%
        </strong>
        <span>{progress.goal_weight} lbs</span>
      </div>

      <div className="progress-track">
        <div
          className="progress-fill"
          style={{
            width: `${progress.progress_percentage}%`,
          }}
        />
      </div>

      {progress.status === 'goal_reached' && (
        <p className="goal-reached">
          🎉 You reached your goal weight!
        </p>
      )}
    </>
  )
}

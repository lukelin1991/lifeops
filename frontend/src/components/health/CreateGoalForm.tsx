type CreateGoalFormProps = {
  startingWeight: string
  goalWeight: string
  setStartingWeight: (value: string) => void
  setGoalWeight: (value: string) => void
  createGoal: () => Promise<void>
}

export function CreateGoalForm({
  startingWeight,
  goalWeight,
  setStartingWeight,
  setGoalWeight,
  createGoal,
}: CreateGoalFormProps) {
  return (
    <section className="card">
      <div className="card-heading">
        <div>
          <p className="eyebrow">NEW GOAL</p>
          <h3>Create Weight Goal</h3>
        </div>
      </div>

      <div className="stack-form">
        <label>
          Starting Weight
          <input
            type="number"
            step="0.1"
            placeholder="260"
            value={startingWeight}
            onChange={(event) =>
              setStartingWeight(
                event.target.value,
              )
            }
          />
        </label>

        <label>
          Goal Weight
          <input
            type="number"
            step="0.1"
            placeholder="180"
            value={goalWeight}
            onChange={(event) =>
              setGoalWeight(event.target.value)
            }
          />
        </label>

        <button
          className="primary-button"
          onClick={createGoal}
        >
          Create Goal
        </button>
      </div>
    </section>
  )
}

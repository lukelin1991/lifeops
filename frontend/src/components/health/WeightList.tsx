import type { WeightEntry } from '../../api/types'
import { formatDate } from '../../utils/format'

type WeightListProps = {
  weights: WeightEntry[]
  editingWeightId: number | null
  editWeight: string
  editMeasurementDate: string
  setEditWeight: (value: string) => void
  setEditMeasurementDate: (value: string) => void
  startEditingWeight: (entry: WeightEntry) => void
  cancelEditingWeight: () => void
  updateWeight: (id: number) => Promise<void>
  deleteWeight: (id: number) => Promise<void>
}

// Newest measurement first, each row editable in place.
export function WeightList({
  weights,
  editingWeightId,
  editWeight,
  editMeasurementDate,
  setEditWeight,
  setEditMeasurementDate,
  startEditingWeight,
  cancelEditingWeight,
  updateWeight,
  deleteWeight,
}: WeightListProps) {
  return (
    <section className="card">
      <div className="card-heading">
        <div>
          <p className="eyebrow">MEASUREMENTS</p>
          <h3>Weight Entries</h3>
        </div>

        <span className="entry-count">
          {weights.length} entries
        </span>
      </div>

      {weights.length === 0 ? (
        <p className="empty-state">
          No weight measurements yet.
        </p>
      ) : (
        <div className="weight-list">
          {[...weights]
            .reverse()
            .map((entry) => (
              <div
                className="weight-row"
                key={entry.id}
              >
                {editingWeightId === entry.id ? (
                  <>
                    <div className="edit-fields">
                      <input
                        type="number"
                        step="0.1"
                        value={editWeight}
                        onChange={(event) =>
                          setEditWeight(
                            event.target.value,
                          )
                        }
                      />

                      <input
                        type="date"
                        value={editMeasurementDate}
                        onChange={(event) =>
                          setEditMeasurementDate(
                            event.target.value,
                          )
                        }
                      />
                    </div>

                    <div className="actions">
                      <button
                        className="save-button"
                        onClick={() =>
                          updateWeight(entry.id)
                        }
                      >
                        Save
                      </button>

                      <button
                        className="secondary-button"
                        onClick={
                          cancelEditingWeight
                        }
                      >
                        Cancel
                      </button>
                    </div>
                  </>
                ) : (
                  <>
                    <div>
                      <strong className="weight-value">
                        {entry.weight} lbs
                      </strong>

                      <p className="weight-date">
                        {formatDate(
                          entry.measurement_date,
                        )}
                      </p>
                    </div>

                    <div className="actions">
                      <button
                        className="secondary-button"
                        onClick={() =>
                          startEditingWeight(entry)
                        }
                      >
                        Edit
                      </button>

                      <button
                        className="delete-button"
                        onClick={() =>
                          deleteWeight(entry.id)
                        }
                      >
                        Delete
                      </button>
                    </div>
                  </>
                )}
              </div>
            ))}
        </div>
      )}
    </section>
  )
}

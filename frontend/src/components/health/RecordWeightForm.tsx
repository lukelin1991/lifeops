type RecordWeightFormProps = {
  weight: string
  measurementDate: string
  setWeight: (value: string) => void
  setMeasurementDate: (value: string) => void
  addWeight: () => Promise<void>
}

export function RecordWeightForm({
  weight,
  measurementDate,
  setWeight,
  setMeasurementDate,
  addWeight,
}: RecordWeightFormProps) {
  return (
    <section className="card">
      <div className="card-heading">
        <div>
          <p className="eyebrow">NEW ENTRY</p>
          <h3>Record Weight</h3>
        </div>
      </div>

      <div className="stack-form">
        <label>
          Weight
          <input
            type="number"
            step="0.1"
            placeholder="253.2"
            value={weight}
            onChange={(event) =>
              setWeight(event.target.value)
            }
          />
        </label>

        <label>
          Measurement Date
          <input
            type="date"
            value={measurementDate}
            onChange={(event) =>
              setMeasurementDate(
                event.target.value,
              )
            }
          />
        </label>

        <button
          className="primary-button"
          onClick={addWeight}
        >
          Record Weight
        </button>
      </div>
    </section>
  )
}

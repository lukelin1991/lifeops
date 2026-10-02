// Luke's original Health UI, moved here from App.tsx and split into
// components. Same endpoints, same messages, same behaviour.
import { useCallback, useEffect, useState } from 'react'
import { describeError } from '../api/client'
import { healthApi } from '../api/health'
import type { WeightEntry, WeightGoal, WeightProgress } from '../api/types'
import { Alert } from '../components/Alert'
import { ActiveGoalSummary } from '../components/health/ActiveGoalSummary'
import { CreateGoalForm } from '../components/health/CreateGoalForm'
import { GoalList } from '../components/health/GoalList'
import { RecordWeightForm } from '../components/health/RecordWeightForm'
import { WeightChart } from '../components/health/WeightChart'
import { WeightList } from '../components/health/WeightList'
import { todayString } from '../utils/format'

type HealthData = {
  weights: WeightEntry[]
  goals: WeightGoal[]
  progress: WeightProgress | null
}

async function fetchHealthData(): Promise<HealthData> {
  const [weightsData, goalsData] = await Promise.all([
    healthApi.listWeights(),
    healthApi.listGoals(),
  ])

  const hasActiveGoal = goalsData.data.some(
    (goal) => goal.status === 'active',
  )

  let progress: WeightProgress | null = null

  if (hasActiveGoal && weightsData.data.length > 0) {
    try {
      progress = await healthApi.getProgress()
    } catch {
      progress = null
    }
  }

  return {
    weights: weightsData.data,
    goals: goalsData.data,
    progress,
  }
}

export default function Health() {
  const [weights, setWeights] = useState<WeightEntry[]>([])
  const [goals, setGoals] = useState<WeightGoal[]>([])
  const [progress, setProgress] =
    useState<WeightProgress | null>(null)

  const [weight, setWeight] = useState('')
  const [measurementDate, setMeasurementDate] =
    useState(todayString())

  const [startingWeight, setStartingWeight] = useState('')
  const [goalWeight, setGoalWeight] = useState('')

  const [editingWeightId, setEditingWeightId] =
    useState<number | null>(null)
  const [editWeight, setEditWeight] = useState('')
  const [editMeasurementDate, setEditMeasurementDate] =
    useState('')

  const [editingGoalId, setEditingGoalId] =
    useState<number | null>(null)
  const [editStartingWeight, setEditStartingWeight] =
    useState('')
  const [editGoalWeight, setEditGoalWeight] = useState('')

  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const activeGoal =
    goals.find((goal) => goal.status === 'active') ?? null

  const latestWeight =
    weights.length > 0
      ? weights[weights.length - 1]
      : null

  function clearAlerts() {
    setMessage('')
    setError('')
  }

  const applyData = useCallback((data: HealthData) => {
    setWeights(data.weights)
    setGoals(data.goals)
    setProgress(data.progress)
  }, [])

  const loadData = useCallback(async () => {
    try {
      applyData(await fetchHealthData())
    } catch (err) {
      console.error(err)
      setError('Could not connect to the LifeOps API.')
    }
  }, [applyData])

  useEffect(() => {
    let active = true

    fetchHealthData()
      .then((data) => {
        if (active) applyData(data)
      })
      .catch((err) => {
        console.error(err)
        if (active) setError('Could not connect to the LifeOps API.')
      })

    return () => {
      active = false
    }
  }, [applyData])

  // Runs an API call; on failure shows the API's error message.
  async function attempt(action: () => Promise<unknown>) {
    try {
      await action()
      return true
    } catch (err) {
      setError(describeError(err))
      return false
    }
  }

  async function addWeight() {
    clearAlerts()

    if (!weight || !measurementDate) {
      setError('Enter a weight and measurement date.')
      return
    }

    const ok = await attempt(() =>
      healthApi.createWeight({
        weight: Number(weight),
        measurement_date: measurementDate,
      }),
    )
    if (!ok) return

    setWeight('')
    setMeasurementDate(todayString())
    setMessage('Weight recorded.')
    await loadData()
  }

  function startEditingWeight(entry: WeightEntry) {
    clearAlerts()
    setEditingWeightId(entry.id)
    setEditWeight(String(entry.weight))
    setEditMeasurementDate(entry.measurement_date)
  }

  function cancelEditingWeight() {
    setEditingWeightId(null)
    setEditWeight('')
    setEditMeasurementDate('')
  }

  async function updateWeight(id: number) {
    clearAlerts()

    const ok = await attempt(() =>
      healthApi.updateWeight(id, {
        weight: Number(editWeight),
        measurement_date: editMeasurementDate,
      }),
    )
    if (!ok) return

    cancelEditingWeight()
    setMessage('Weight updated.')
    await loadData()
  }

  async function deleteWeight(id: number) {
    const confirmed = window.confirm(
      'Delete this weight measurement?',
    )

    if (!confirmed) return

    clearAlerts()

    const ok = await attempt(() => healthApi.deleteWeight(id))
    if (!ok) return

    setMessage('Weight deleted.')
    await loadData()
  }

  async function createGoal() {
    clearAlerts()

    if (!startingWeight || !goalWeight) {
      setError('Enter a starting weight and goal weight.')
      return
    }

    const ok = await attempt(() =>
      healthApi.createGoal({
        starting_weight: Number(startingWeight),
        goal_weight: Number(goalWeight),
      }),
    )
    if (!ok) return

    setStartingWeight('')
    setGoalWeight('')
    setMessage('Goal created. Activate it when you are ready.')
    await loadData()
  }

  async function activateGoal(id: number) {
    clearAlerts()

    const ok = await attempt(() => healthApi.activateGoal(id))
    if (!ok) return

    setMessage('Goal activated.')
    await loadData()
  }

  function startEditingGoal(goal: WeightGoal) {
    clearAlerts()
    setEditingGoalId(goal.id)
    setEditStartingWeight(String(goal.starting_weight))
    setEditGoalWeight(String(goal.goal_weight))
  }

  function cancelEditingGoal() {
    setEditingGoalId(null)
    setEditStartingWeight('')
    setEditGoalWeight('')
  }

  async function updateGoal(id: number) {
    clearAlerts()

    const ok = await attempt(() =>
      healthApi.updateGoal(id, {
        starting_weight: Number(editStartingWeight),
        goal_weight: Number(editGoalWeight),
      }),
    )
    if (!ok) return

    cancelEditingGoal()
    setMessage('Goal updated.')
    await loadData()
  }

  async function deleteGoal(id: number) {
    const confirmed = window.confirm(
      'Delete this goal permanently?',
    )

    if (!confirmed) return

    clearAlerts()

    const ok = await attempt(() => healthApi.deleteGoal(id))
    if (!ok) return

    setMessage('Goal deleted.')
    await loadData()
  }

  async function completeGoal(id: number) {
    const confirmed = window.confirm(
      'Mark this weight goal as completed?',
    )

    if (!confirmed) return

    clearAlerts()

    const ok = await attempt(() => healthApi.completeGoal(id))
    if (!ok) return

    setMessage('Goal completed! 🎉')
    await loadData()
  }

  return (
    <>
      <section className="hero">
        <p className="eyebrow">HEALTH</p>
        <h2>Weight Management</h2>
        <p>
          Track measurements, manage goals, and see your
          progress over time.
        </p>
      </section>

      <Alert message={message} kind="success" />
      <Alert message={error} />

      <ActiveGoalSummary
        activeGoal={activeGoal}
        progress={progress}
        completeGoal={completeGoal}
      />

      <section className="card">
        <div className="card-heading">
          <div>
            <p className="eyebrow">TREND</p>
            <h3>Weight History</h3>
          </div>

          {latestWeight && (
            <span className="entry-count">
              Latest: {latestWeight.weight} lbs
            </span>
          )}
        </div>

        {weights.length === 0 ? (
          <p className="empty-state">
            Record your first weight to start the chart.
          </p>
        ) : (
          <WeightChart weights={weights} />
        )}
      </section>

      <div className="two-column">
        <RecordWeightForm
          weight={weight}
          measurementDate={measurementDate}
          setWeight={setWeight}
          setMeasurementDate={setMeasurementDate}
          addWeight={addWeight}
        />

        <CreateGoalForm
          startingWeight={startingWeight}
          goalWeight={goalWeight}
          setStartingWeight={setStartingWeight}
          setGoalWeight={setGoalWeight}
          createGoal={createGoal}
        />
      </div>

      <GoalList
        goals={goals}
        editingGoalId={editingGoalId}
        editStartingWeight={editStartingWeight}
        editGoalWeight={editGoalWeight}
        setEditStartingWeight={setEditStartingWeight}
        setEditGoalWeight={setEditGoalWeight}
        startEditingGoal={startEditingGoal}
        cancelEditingGoal={cancelEditingGoal}
        updateGoal={updateGoal}
        deleteGoal={deleteGoal}
        activateGoal={activateGoal}
      />

      <WeightList
        weights={weights}
        editingWeightId={editingWeightId}
        editWeight={editWeight}
        editMeasurementDate={editMeasurementDate}
        setEditWeight={setEditWeight}
        setEditMeasurementDate={setEditMeasurementDate}
        startEditingWeight={startEditingWeight}
        cancelEditingWeight={cancelEditingWeight}
        updateWeight={updateWeight}
        deleteWeight={deleteWeight}
      />
    </>
  )
}

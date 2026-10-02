// Luke's original Health endpoints (paths unchanged).
import { api, type Envelope } from './client'
import type { WeightEntry, WeightGoal, WeightProgress } from './types'

export const healthApi = {
  listWeights: () => api.get<Envelope<WeightEntry[]>>('/weights'),
  createWeight: (body: { weight: number; measurement_date: string }) =>
    api.post<Envelope<WeightEntry>>('/weights', body),
  updateWeight: (
    id: number,
    body: { weight?: number; measurement_date?: string },
  ) => api.patch<Envelope<WeightEntry>>(`/weights/${id}`, body),
  deleteWeight: (id: number) => api.delete(`/weights/${id}`),

  listGoals: () => api.get<Envelope<WeightGoal[]>>('/weight-goals'),
  createGoal: (body: { starting_weight: number; goal_weight: number }) =>
    api.post<Envelope<WeightGoal>>('/weight-goals', body),
  updateGoal: (
    id: number,
    body: { starting_weight?: number; goal_weight?: number },
  ) => api.patch<Envelope<WeightGoal>>(`/weight-goals/${id}`, body),
  deleteGoal: (id: number) => api.delete(`/weight-goals/${id}`),
  activateGoal: (id: number) =>
    api.post<Envelope<WeightGoal>>(`/weight-goals/${id}/activate`),
  completeGoal: (id: number) =>
    api.post<Envelope<WeightGoal>>(`/weight-goals/${id}/complete`),

  getProgress: () => api.get<WeightProgress>('/weight-progress'),
}

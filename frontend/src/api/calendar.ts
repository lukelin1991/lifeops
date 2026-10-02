import { api, type Envelope } from './client'
import { crudApi } from './crud'
import type { Agenda, CalendarEvent, Task } from './types'

export const calendarApi = {
  events: crudApi<CalendarEvent>('/calendar/events'),
  tasks: crudApi<Task>('/calendar/tasks'),

  completeTask: (id: number) =>
    api.post<Envelope<Task> & { next_task: Task | null }>(
      `/calendar/tasks/${id}/complete`,
    ),

  today: () => api.get<Agenda>('/calendar/agenda/today'),
  week: () => api.get<Agenda>('/calendar/agenda/week'),
  upcoming: (days = 14) => api.get<Agenda>('/calendar/upcoming', { days }),
}

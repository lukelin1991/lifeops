import { useCallback, useState } from 'react'
import { calendarApi } from '../api/calendar'
import { describeError } from '../api/client'
import type { Agenda, CalendarEvent, Task } from '../api/types'
import { Alert } from '../components/Alert'
import { Badge } from '../components/Badge'
import { PageHeader } from '../components/PageHeader'
import { ResourceManager } from '../components/ResourceManager'
import { Tabs } from '../components/Tabs'
import { useApiData } from '../hooks/useApiData'
import {
  formatDate,
  formatDateTimeShort,
  formatTime,
  titleCase,
  todayString,
} from '../utils/format'
import { options, type FieldDef } from '../utils/forms'

type View = 'today' | 'week' | 'upcoming'

const EVENT_FIELDS: FieldDef[] = [
  { name: 'title', label: 'Title', required: true },
  { name: 'start_at', label: 'Starts', type: 'datetime-local', required: true },
  { name: 'end_at', label: 'Ends', type: 'datetime-local' },
  { name: 'all_day', label: 'All day', type: 'checkbox' },
  { name: 'location', label: 'Location' },
  { name: 'notes', label: 'Notes', type: 'textarea' },
]

const TASK_FIELDS: FieldDef[] = [
  { name: 'title', label: 'Title', required: true },
  { name: 'due_date', label: 'Due date', type: 'date', defaultValue: todayString() },
  {
    name: 'priority', label: 'Priority', type: 'select', required: true,
    options: options(['low', 'medium', 'high']), defaultValue: 'medium',
  },
  {
    name: 'status', label: 'Status', type: 'select', required: true,
    options: options(['todo', 'in_progress', 'done']), defaultValue: 'todo',
  },
  {
    name: 'recurrence', label: 'Repeats', type: 'select', required: true,
    options: options(['none', 'daily', 'weekly', 'monthly']), defaultValue: 'none',
  },
  { name: 'notes', label: 'Notes', type: 'textarea' },
]

const AGENDA_LOADERS: Record<View, () => Promise<Agenda>> = {
  today: () => calendarApi.today(),
  week: () => calendarApi.week(),
  upcoming: () => calendarApi.upcoming(14),
}

export default function Calendar() {
  const [view, setView] = useState<View>('today')
  const [notice, setNotice] = useState('')
  const [actionError, setActionError] = useState('')

  const agendaLoader = useCallback(() => AGENDA_LOADERS[view](), [view])
  const agenda = useApiData(agendaLoader)

  const listLoader = useCallback(async () => {
    const [events, tasks] = await Promise.all([
      calendarApi.events.list(),
      calendarApi.tasks.list({ include_done: true }),
    ])
    return { events, tasks }
  }, [])
  const lists = useApiData(listLoader)

  const reloadAgenda = agenda.reload
  const reloadLists = lists.reload
  const reloadAll = useCallback(() => {
    reloadAgenda()
    reloadLists()
  }, [reloadAgenda, reloadLists])

  async function completeTask(task: Task) {
    setNotice('')
    setActionError('')
    try {
      const result = await calendarApi.completeTask(task.id)
      setNotice(
        result.next_task
          ? `Done! Next "${task.title}" is due ${formatDate(result.next_task.due_date)}.`
          : 'Task completed.',
      )
      reloadAll()
    } catch (err) {
      setActionError(describeError(err))
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="CALENDAR"
        title="Schedule & Tasks"
        description="Events, to-dos and recurring chores in one agenda."
      />

      <Alert message={agenda.error || lists.error || actionError} />
      <Alert message={notice} kind="success" />

      <section className="card">
        <div className="card-heading">
          <div>
            <p className="eyebrow">AGENDA</p>
            <h3>
              {agenda.data
                ? agenda.data.start_date === agenda.data.end_date
                  ? formatDate(agenda.data.start_date)
                  : `${formatDate(agenda.data.start_date)} – ${formatDate(agenda.data.end_date)}`
                : '…'}
            </h3>
          </div>
          <Tabs
            tabs={[
              { id: 'today', label: 'Today' },
              { id: 'week', label: 'This week' },
              { id: 'upcoming', label: 'Next 14 days' },
            ]}
            active={view}
            onChange={setView}
          />
        </div>

        {agenda.data && (
          <AgendaView agenda={agenda.data} showDates={view !== 'today'} onComplete={completeTask} />
        )}
      </section>

      <div className="two-column">
        <ResourceManager<CalendarEvent>
          eyebrow="EVENTS"
          title="Events"
          addLabel="Add event"
          items={lists.data?.events ?? []}
          fields={EVENT_FIELDS}
          onCreate={calendarApi.events.create}
          onUpdate={calendarApi.events.update}
          onDelete={calendarApi.events.remove}
          onChanged={reloadAll}
          emptyText="No events yet."
          columns={[
            { label: 'When', render: (e) => (e.all_day ? formatDate(e.start_at) : formatDateTimeShort(e.start_at)) },
            { label: 'Title', render: (e) => e.title },
          ]}
        />

        <ResourceManager<Task>
          eyebrow="TASKS"
          title="Tasks"
          addLabel="Add task"
          items={lists.data?.tasks ?? []}
          fields={TASK_FIELDS}
          onCreate={calendarApi.tasks.create}
          onUpdate={calendarApi.tasks.update}
          onDelete={calendarApi.tasks.remove}
          onChanged={reloadAll}
          emptyText="No tasks yet."
          rowActions={(task) =>
            task.status !== 'done' && (
              <button className="save-button small" onClick={() => completeTask(task)}>
                Done
              </button>
            )
          }
          columns={[
            { label: 'Due', render: (t) => formatDate(t.due_date) },
            {
              label: 'Task',
              render: (t) => (
                <span className={t.status === 'done' ? 'done-text' : undefined}>
                  {t.title}
                  {t.recurrence !== 'none' && (
                    <small className="muted"> ↻ {titleCase(t.recurrence)}</small>
                  )}
                </span>
              ),
            },
            { label: 'Priority', render: (t) => <Badge value={t.priority} group="priority" /> },
          ]}
        />
      </div>
    </>
  )
}

type AgendaViewProps = {
  agenda: Agenda
  showDates: boolean
  onComplete: (task: Task) => void
}

function AgendaView({ agenda, showDates, onComplete }: AgendaViewProps) {
  const nothing =
    agenda.events.length === 0 &&
    agenda.tasks.length === 0 &&
    agenda.overdue_tasks.length === 0

  if (nothing) {
    return <p className="empty-state">Nothing on the agenda. Enjoy it.</p>
  }

  return (
    <ul className="simple-list">
      {agenda.overdue_tasks.map((task) => (
        <li key={`o${task.id}`}>
          <span className="list-time overdue">Overdue · {formatDate(task.due_date)}</span>
          <span>{task.title}</span>
          <Badge value={task.priority} group="priority" />
          <button className="save-button small" onClick={() => onComplete(task)}>
            Done
          </button>
        </li>
      ))}

      {agenda.events.map((event) => (
        <li key={`e${event.id}`}>
          <span className="list-time">
            {showDates ? formatDateTimeShort(event.start_at) : event.all_day ? 'All day' : formatTime(event.start_at)}
          </span>
          <span>{event.title}</span>
          {event.location && <small className="muted">{event.location}</small>}
        </li>
      ))}

      {agenda.tasks.map((task) => (
        <li key={`t${task.id}`}>
          <span className="list-time">{showDates ? formatDate(task.due_date) : 'Task'}</span>
          <span>{task.title}</span>
          <Badge value={task.priority} group="priority" />
          <button className="save-button small" onClick={() => onComplete(task)}>
            Done
          </button>
        </li>
      ))}
    </ul>
  )
}

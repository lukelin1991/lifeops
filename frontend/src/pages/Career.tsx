import { useCallback, useMemo, useState } from 'react'
import { careerApi } from '../api/career'
import type {
  Certification,
  Contact,
  Interview,
  JobApplication,
} from '../api/types'
import { Alert } from '../components/Alert'
import { Badge } from '../components/Badge'
import { PageHeader } from '../components/PageHeader'
import { ResourceManager } from '../components/ResourceManager'
import { Tabs } from '../components/Tabs'
import { useApiData } from '../hooks/useApiData'
import {
  formatDate,
  formatDateTimeShort,
  titleCase,
  todayString,
} from '../utils/format'
import { options, type FieldDef } from '../utils/forms'

type TabId = 'applications' | 'interviews' | 'contacts' | 'certifications'

const STATUSES = ['applied', 'screen', 'interview', 'offer', 'rejected', 'withdrawn']

const APPLICATION_FIELDS: FieldDef[] = [
  { name: 'company', label: 'Company', required: true },
  { name: 'title', label: 'Job title', required: true },
  { name: 'status', label: 'Status', type: 'select', required: true, options: options(STATUSES), defaultValue: 'applied' },
  {
    name: 'work_mode', label: 'Work mode', type: 'select', required: true,
    options: options(['remote', 'hybrid', 'onsite']), defaultValue: 'remote',
  },
  { name: 'location', label: 'Location' },
  { name: 'applied_date', label: 'Applied on', type: 'date', defaultValue: todayString() },
  { name: 'salary_min', label: 'Salary min', type: 'number', step: '1000' },
  { name: 'salary_max', label: 'Salary max', type: 'number', step: '1000' },
  { name: 'url', label: 'Job posting URL', type: 'url', wide: true },
  { name: 'notes', label: 'Notes', type: 'textarea' },
]

const CERT_FIELDS: FieldDef[] = [
  { name: 'name', label: 'Certification / study goal', required: true },
  { name: 'provider', label: 'Provider' },
  { name: 'target_date', label: 'Target date', type: 'date' },
  {
    name: 'status', label: 'Status', type: 'select', required: true,
    options: options(['planned', 'in_progress', 'completed']), defaultValue: 'planned',
  },
  { name: 'completed_date', label: 'Completed on', type: 'date' },
  { name: 'notes', label: 'Notes', type: 'textarea' },
]

function salary(app: JobApplication) {
  const k = (value: number) => `$${Math.round(value / 1000)}k`
  if (app.salary_min && app.salary_max) return `${k(app.salary_min)}–${k(app.salary_max)}`
  if (app.salary_min) return `${k(app.salary_min)}+`
  if (app.salary_max) return `up to ${k(app.salary_max)}`
  return '—'
}

export default function Career() {
  const [tab, setTab] = useState<TabId>('applications')
  const [statusFilter, setStatusFilter] = useState('')

  const loader = useCallback(async () => {
    const [applications, interviews, contacts, certifications, pipeline] =
      await Promise.all([
        careerApi.applications.list(),
        careerApi.interviews.list(),
        careerApi.contacts.list(),
        careerApi.certifications.list(),
        careerApi.pipeline(),
      ])
    return { applications, interviews, contacts, certifications, pipeline }
  }, [])

  const { data, error, reload } = useApiData(loader)
  const applications = useMemo(() => data?.applications ?? [], [data])

  const applicationOptions = useMemo(
    () => applications.map((a) => ({ value: String(a.id), label: `${a.company} — ${a.title}` })),
    [applications],
  )

  const interviewFields: FieldDef[] = useMemo(() => [
    {
      name: 'application_id', label: 'Application', type: 'select', required: true,
      options: applicationOptions, defaultValue: applicationOptions[0]?.value ?? '',
    },
    { name: 'scheduled_at', label: 'When', type: 'datetime-local', required: true },
    { name: 'stage', label: 'Stage', required: true, placeholder: 'technical, system_design…' },
    {
      name: 'outcome', label: 'Outcome', type: 'select', required: true,
      options: options(['pending', 'passed', 'failed']), defaultValue: 'pending',
    },
    { name: 'notes', label: 'Notes', type: 'textarea' },
  ], [applicationOptions])

  const contactFields: FieldDef[] = useMemo(() => [
    { name: 'name', label: 'Name', required: true },
    { name: 'company', label: 'Company' },
    { name: 'role', label: 'Role' },
    { name: 'email', label: 'Email', type: 'email' },
    { name: 'phone', label: 'Phone' },
    { name: 'linkedin_url', label: 'LinkedIn URL', type: 'url' },
    { name: 'application_id', label: 'Linked application', type: 'select', options: applicationOptions },
    { name: 'notes', label: 'Notes', type: 'textarea' },
  ], [applicationOptions])

  const visibleApplications = statusFilter
    ? applications.filter((a) => a.status === statusFilter)
    : applications

  const companyFor = (applicationId: number | null) =>
    applications.find((a) => a.id === applicationId)?.company ?? '—'

  return (
    <>
      <PageHeader
        eyebrow="CAREER"
        title="Job Search & Growth"
        description="Track applications, interviews, people you meet and the certifications you're working toward."
      />

      <Alert message={error} />

      {data && (
        <section className="card">
          <div className="card-heading">
            <div>
              <p className="eyebrow">PIPELINE</p>
              <h3>{data.pipeline.total} applications · {data.pipeline.active} active</h3>
            </div>
            {data.pipeline.response_rate !== null && (
              <span className="entry-count">{data.pipeline.response_rate}% response rate</span>
            )}
          </div>
          <div className="pipeline">
            {STATUSES.map((status) => (
              <button
                key={status}
                className={`pipeline-step status-${status} ${statusFilter === status ? 'selected' : ''}`}
                onClick={() => {
                  setTab('applications')
                  setStatusFilter(statusFilter === status ? '' : status)
                }}
              >
                <strong>{data.pipeline.counts[status as keyof typeof data.pipeline.counts]}</strong>
                <span>{titleCase(status)}</span>
              </button>
            ))}
          </div>
        </section>
      )}

      <Tabs
        tabs={[
          { id: 'applications', label: 'Applications' },
          { id: 'interviews', label: 'Interviews' },
          { id: 'contacts', label: 'Contacts' },
          { id: 'certifications', label: 'Certifications' },
        ]}
        active={tab}
        onChange={setTab}
      />

      {tab === 'applications' && (
        <ResourceManager<JobApplication>
          eyebrow="APPLICATIONS"
          title={statusFilter ? `${titleCase(statusFilter)} applications` : 'All applications'}
          addLabel="Add application"
          items={visibleApplications}
          fields={APPLICATION_FIELDS}
          onCreate={careerApi.applications.create}
          onUpdate={careerApi.applications.update}
          onDelete={careerApi.applications.remove}
          onChanged={reload}
          emptyText="No applications here."
          deleteConfirm={(a) => `Delete ${a.company}? Its interviews are deleted too.`}
          toolbar={
            statusFilter && (
              <button className="secondary-button small" onClick={() => setStatusFilter('')}>
                Clear filter
              </button>
            )
          }
          columns={[
            {
              label: 'Company',
              render: (a) =>
                a.url ? (
                  <a className="text-link" href={a.url} target="_blank" rel="noreferrer">
                    {a.company}
                  </a>
                ) : (
                  a.company
                ),
            },
            { label: 'Role', render: (a) => a.title },
            { label: 'Status', render: (a) => <Badge value={a.status} group="status" /> },
            { label: 'Mode', render: (a) => titleCase(a.work_mode) },
            { label: 'Salary', render: salary },
            { label: 'Applied', render: (a) => formatDate(a.applied_date) },
          ]}
        />
      )}

      {tab === 'interviews' && (
        <ResourceManager<Interview>
          eyebrow="INTERVIEWS"
          title="Interviews"
          addLabel="Schedule interview"
          items={data?.interviews ?? []}
          fields={interviewFields}
          editFields={interviewFields.filter((f) => f.name !== 'application_id')}
          onCreate={careerApi.interviews.create}
          onUpdate={careerApi.interviews.update}
          onDelete={careerApi.interviews.remove}
          onChanged={reload}
          emptyText={applications.length ? 'No interviews yet.' : 'Add an application first.'}
          columns={[
            { label: 'When', render: (i) => formatDateTimeShort(i.scheduled_at) },
            { label: 'Company', render: (i) => `${i.company ?? '—'} · ${i.title ?? ''}` },
            { label: 'Stage', render: (i) => titleCase(i.stage) },
            { label: 'Outcome', render: (i) => <Badge value={i.outcome} group="outcome" /> },
          ]}
        />
      )}

      {tab === 'contacts' && (
        <ResourceManager<Contact>
          eyebrow="NETWORK"
          title="Contacts"
          addLabel="Add contact"
          items={data?.contacts ?? []}
          fields={contactFields}
          onCreate={careerApi.contacts.create}
          onUpdate={careerApi.contacts.update}
          onDelete={careerApi.contacts.remove}
          onChanged={reload}
          emptyText="No contacts yet."
          columns={[
            { label: 'Name', render: (c) => c.name },
            { label: 'Company / role', render: (c) => [c.company, c.role].filter(Boolean).join(' · ') || '—' },
            { label: 'Email', render: (c) => c.email ?? '—' },
            { label: 'Application', render: (c) => companyFor(c.application_id) },
          ]}
        />
      )}

      {tab === 'certifications' && (
        <ResourceManager<Certification>
          eyebrow="LEARNING"
          title="Certifications & study goals"
          addLabel="Add goal"
          items={data?.certifications ?? []}
          fields={CERT_FIELDS}
          onCreate={careerApi.certifications.create}
          onUpdate={careerApi.certifications.update}
          onDelete={careerApi.certifications.remove}
          onChanged={reload}
          emptyText="No study goals yet."
          columns={[
            { label: 'Name', render: (c) => c.name },
            { label: 'Provider', render: (c) => c.provider ?? '—' },
            { label: 'Target', render: (c) => formatDate(c.target_date) },
            { label: 'Status', render: (c) => <Badge value={c.status} group="cert" /> },
          ]}
        />
      )}
    </>
  )
}

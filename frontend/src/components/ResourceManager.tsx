import { useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import { describeError } from '../api/client'
import {
  emptyValues,
  toFormValues,
  toPayload,
  type FieldDef,
  type FormValues,
} from '../utils/forms'
import { Alert } from './Alert'
import { FormFields } from './FormFields'

export type Column<T> = {
  label: string
  render: (item: T) => ReactNode
  className?: string
}

type ResourceManagerProps<T extends { id: number }> = {
  eyebrow: string
  title: string
  items: T[]
  // Fields for the "add" form (and edit form unless editFields is given)
  fields: FieldDef[]
  editFields?: FieldDef[]
  columns: Column<T>[]
  onCreate: (payload: Record<string, unknown>) => Promise<unknown>
  onUpdate: (id: number, payload: Record<string, unknown>) => Promise<unknown>
  onDelete: (id: number) => Promise<unknown>
  // Called after any successful change so the page can reload data
  onChanged: () => void
  emptyText?: string
  addLabel?: string
  toolbar?: ReactNode
  rowActions?: (item: T) => ReactNode
  deleteConfirm?: (item: T) => string
}

// A reusable card that lists items and lets you add, edit and delete them.
// Every module page uses it, so each resource only declares its fields
// and columns.
export function ResourceManager<T extends { id: number }>({
  eyebrow,
  title,
  items,
  fields,
  editFields,
  columns,
  onCreate,
  onUpdate,
  onDelete,
  onChanged,
  emptyText = 'Nothing here yet.',
  addLabel = 'Add',
  toolbar,
  rowActions,
  deleteConfirm,
}: ResourceManagerProps<T>) {
  const formFieldsForEdit = editFields ?? fields

  const [showCreate, setShowCreate] = useState(false)
  const [createValues, setCreateValues] = useState<FormValues>(() =>
    emptyValues(fields),
  )
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editValues, setEditValues] = useState<FormValues>({})
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  function clearAlerts() {
    setError('')
    setMessage('')
  }

  async function run(action: () => Promise<unknown>, success: string) {
    clearAlerts()
    setBusy(true)

    try {
      await action()
      setMessage(success)
      onChanged()
      return true
    } catch (err) {
      setError(describeError(err))
      return false
    } finally {
      setBusy(false)
    }
  }

  async function handleCreate(event: FormEvent) {
    event.preventDefault()

    const ok = await run(
      () => onCreate(toPayload(fields, createValues)),
      'Saved.',
    )

    if (ok) {
      setCreateValues(emptyValues(fields))
      setShowCreate(false)
    }
  }

  function startEditing(item: T) {
    clearAlerts()
    setEditingId(item.id)
    setEditValues(toFormValues(formFieldsForEdit, item))
  }

  async function handleUpdate(event: FormEvent, id: number) {
    event.preventDefault()

    const ok = await run(
      () => onUpdate(id, toPayload(formFieldsForEdit, editValues)),
      'Updated.',
    )

    if (ok) setEditingId(null)
  }

  async function handleDelete(item: T) {
    const text = deleteConfirm?.(item) ?? 'Delete this item?'
    if (!window.confirm(text)) return

    await run(() => onDelete(item.id), 'Deleted.')
  }

  return (
    <section className="card">
      <div className="card-heading">
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <h3>{title}</h3>
        </div>

        <div className="actions">
          <span className="entry-count">{items.length}</span>
          <button
            className={showCreate ? 'secondary-button' : 'primary-button'}
            onClick={() => {
              clearAlerts()
              // Fresh defaults each time (dropdown options may have loaded since)
              if (!showCreate) setCreateValues(emptyValues(fields))
              setShowCreate(!showCreate)
            }}
          >
            {showCreate ? 'Close' : addLabel}
          </button>
        </div>
      </div>

      {toolbar && <div className="toolbar">{toolbar}</div>}

      <Alert message={error} />
      <Alert message={message} kind="success" />

      {showCreate && (
        <form className="inline-form" onSubmit={handleCreate}>
          <FormFields
            fields={fields}
            values={createValues}
            onChange={setCreateValues}
          />
          <div className="actions">
            <button className="primary-button" disabled={busy}>
              Save
            </button>
          </div>
        </form>
      )}

      {items.length === 0 ? (
        <p className="empty-state">{emptyText}</p>
      ) : (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                {columns.map((column) => (
                  <th key={column.label} className={column.className}>
                    {column.label}
                  </th>
                ))}
                <th className="actions-col" />
              </tr>
            </thead>
            <tbody>
              {items.map((item) =>
                editingId === item.id ? (
                  <tr key={item.id} className="editing-row">
                    <td colSpan={columns.length + 1}>
                      <form
                        className="inline-form"
                        onSubmit={(event) => handleUpdate(event, item.id)}
                      >
                        <FormFields
                          fields={formFieldsForEdit}
                          values={editValues}
                          onChange={setEditValues}
                        />
                        <div className="actions">
                          <button className="save-button" disabled={busy}>
                            Save
                          </button>
                          <button
                            type="button"
                            className="secondary-button"
                            onClick={() => setEditingId(null)}
                          >
                            Cancel
                          </button>
                        </div>
                      </form>
                    </td>
                  </tr>
                ) : (
                  <tr key={item.id}>
                    {columns.map((column) => (
                      <td key={column.label} className={column.className}>
                        {column.render(item)}
                      </td>
                    ))}
                    <td className="actions-col">
                      <div className="actions">
                        {rowActions?.(item)}
                        <button
                          className="secondary-button small"
                          onClick={() => startEditing(item)}
                        >
                          Edit
                        </button>
                        <button
                          className="delete-button small"
                          onClick={() => handleDelete(item)}
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ),
              )}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

// Form helpers used by ResourceManager and the module pages.

export type FieldType =
  | 'text'
  | 'number'
  | 'date'
  | 'datetime-local'
  | 'select'
  | 'checkbox'
  | 'textarea'
  | 'url'
  | 'email'

export type Option = { value: string; label: string }

export type FieldDef = {
  name: string
  label: string
  type?: FieldType
  options?: Option[]
  required?: boolean
  step?: string
  placeholder?: string
  // Value used when the "add" form opens
  defaultValue?: string | boolean
  // Make the field span the full form width
  wide?: boolean
}

export type FormValues = Record<string, string | boolean>

export function emptyValues(fields: FieldDef[]): FormValues {
  const values: FormValues = {}

  for (const field of fields) {
    values[field.name] =
      field.defaultValue ?? (field.type === 'checkbox' ? false : '')
  }

  return values
}

// Turn an API object into form values (null -> '').
export function toFormValues(
  fields: FieldDef[],
  item: object,
): FormValues {
  const record = item as Record<string, unknown>
  const values: FormValues = {}

  for (const field of fields) {
    const value = record[field.name]

    if (field.type === 'checkbox') {
      values[field.name] = Boolean(value)
    } else if (field.type === 'datetime-local' && typeof value === 'string') {
      values[field.name] = value.slice(0, 16)
    } else {
      values[field.name] =
        value === null || value === undefined ? '' : String(value)
    }
  }

  return values
}

// Turn form values into a JSON body. Empty inputs become null, numbers are
// sent as strings so the API's Decimal fields keep exact cents.
export function toPayload(
  fields: FieldDef[],
  values: FormValues,
): Record<string, unknown> {
  const payload: Record<string, unknown> = {}

  for (const field of fields) {
    const value = values[field.name]

    if (field.type === 'checkbox') {
      payload[field.name] = Boolean(value)
    } else if (value === '' || value === undefined) {
      payload[field.name] = null
    } else {
      payload[field.name] = typeof value === 'string' ? value.trim() : value
    }
  }

  return payload
}

export function options(values: string[]): Option[] {
  return values.map((value) => ({
    value,
    label: value
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' '),
  }))
}

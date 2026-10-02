import type { FieldDef, FormValues } from '../utils/forms'

type FormFieldsProps = {
  fields: FieldDef[]
  values: FormValues
  onChange: (values: FormValues) => void
}

// Renders a grid of labelled inputs from a list of field definitions.
export function FormFields({ fields, values, onChange }: FormFieldsProps) {
  function update(name: string, value: string | boolean) {
    onChange({ ...values, [name]: value })
  }

  return (
    <div className="form-grid">
      {fields.map((field) => {
        const value = values[field.name]
        const className = field.wide ? 'wide' : undefined

        if (field.type === 'checkbox') {
          return (
            <label key={field.name} className={`checkbox-label ${className ?? ''}`}>
              <input
                type="checkbox"
                checked={Boolean(value)}
                onChange={(event) => update(field.name, event.target.checked)}
              />
              {field.label}
            </label>
          )
        }

        if (field.type === 'select') {
          return (
            <label key={field.name} className={className}>
              {field.label}
              <select
                value={String(value ?? '')}
                required={field.required}
                onChange={(event) => update(field.name, event.target.value)}
              >
                {!field.required && <option value="">—</option>}
                {field.options?.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
          )
        }

        if (field.type === 'textarea') {
          return (
            <label key={field.name} className={className ?? 'wide'}>
              {field.label}
              <textarea
                rows={2}
                value={String(value ?? '')}
                placeholder={field.placeholder}
                onChange={(event) => update(field.name, event.target.value)}
              />
            </label>
          )
        }

        return (
          <label key={field.name} className={className}>
            {field.label}
            <input
              type={field.type ?? 'text'}
              step={field.step ?? (field.type === 'number' ? 'any' : undefined)}
              value={String(value ?? '')}
              required={field.required}
              placeholder={field.placeholder}
              onChange={(event) => update(field.name, event.target.value)}
            />
          </label>
        )
      })}
    </div>
  )
}

import { titleCase } from '../utils/format'

// Colored pill. The CSS class is derived from the value,
// e.g. "badge status-interview" or "badge priority-high".
export function Badge({ value, group }: { value: string; group: string }) {
  return <span className={`badge ${group}-${value}`}>{titleCase(value)}</span>
}

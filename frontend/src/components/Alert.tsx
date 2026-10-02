type AlertProps = {
  message: string
  kind?: 'success' | 'error' | 'info'
}

export function Alert({ message, kind = 'error' }: AlertProps) {
  if (!message) return null

  return <div className={`alert ${kind}-alert`}>{message}</div>
}

import { useCallback, useEffect, useState } from 'react'
import { describeError } from '../api/client'

// Load data from the API when a component mounts (and whenever
// `reload()` is called or a dependency of `loader` changes).
//
//   const { data, error, reload } = useApiData(() => moneyApi.summary(y, m))
export function useApiData<T>(loader: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [version, setVersion] = useState(0)

  useEffect(() => {
    let active = true

    loader()
      .then((result) => {
        if (!active) return
        setData(result)
        setError('')
      })
      .catch((err: unknown) => {
        if (active) setError(describeError(err))
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [loader, version])

  const reload = useCallback(() => setVersion((v) => v + 1), [])

  return { data, error, loading, reload }
}

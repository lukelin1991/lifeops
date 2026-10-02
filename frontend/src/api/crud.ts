import { api, type Envelope } from './client'

// The same five calls exist for every resource in the new modules.
export function crudApi<T>(basePath: string) {
  return {
    list: (query?: Record<string, string | number | boolean | undefined>) =>
      api.get<Envelope<T[]>>(basePath, query).then((r) => r.data),
    create: (body: unknown) =>
      api.post<Envelope<T>>(basePath, body).then((r) => r.data),
    update: (id: number, body: unknown) =>
      api.patch<Envelope<T>>(`${basePath}/${id}`, body).then((r) => r.data),
    remove: (id: number) => api.delete(`${basePath}/${id}`),
  }
}

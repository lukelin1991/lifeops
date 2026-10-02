import { api } from './client'

export const authApi = {
  config: () => api.get<{ auth_enabled: boolean }>('/auth/config'),
  login: (username: string, password: string) =>
    api.post<{ access_token: string; token_type: string; expires_in: number }>(
      '/auth/login',
      { username, password },
    ),
  ready: () => api.get<{ status: string }>('/readyz'),
}

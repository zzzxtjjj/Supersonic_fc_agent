import { apiRequest } from './api'


export const adminAuth = {
  getSession(signal?: AbortSignal) {
    return apiRequest<{ authenticated: boolean }>('/admin/me', { signal })
  },

  login(username: string, password: string) {
    return apiRequest<{ authenticated: boolean; username: string }>(
      '/admin/login',
      {
        method: 'POST',
        body: JSON.stringify({ username, password }),
      },
    )
  },

  logout() {
    return apiRequest<{ authenticated: boolean }>('/admin/logout', {
      method: 'POST',
    })
  },
}

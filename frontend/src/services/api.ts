const configuredBaseUrl =
  import.meta.env.VITE_API_BASE_URL ?? '/api'

export const API_BASE_URL = configuredBaseUrl.replace(/\/$/, '')

export function apiUrl(path: string): string {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return `${API_BASE_URL}${normalizedPath}`
}

export function resolveMediaUrl(url: string | null): string | null {
  if (!url || /^(?:https?:|data:|blob:)/.test(url)) return url
  if (!url.startsWith('/media') || !/^https?:/.test(API_BASE_URL)) return url
  return `${new URL(API_BASE_URL).origin}${url}`
}

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers)
  headers.set('Accept', 'application/json')

  if (
    init.body &&
    !(init.body instanceof FormData) &&
    !headers.has('Content-Type')
  ) {
    headers.set('Content-Type', 'application/json')
  }

  const response = await fetch(apiUrl(path), {
    ...init,
    headers,
    credentials: 'include',
  })

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as {
      detail?: string
    } | null
    throw new ApiError(
      payload?.detail ?? `API request failed (${response.status})`,
      response.status,
    )
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

export function uploadFormData<T>(
  path: string,
  formData: FormData,
  onProgress?: (percent: number) => void,
): Promise<T> {
  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest()
    request.open('POST', apiUrl(path))
    request.withCredentials = true
    request.setRequestHeader('Accept', 'application/json')
    request.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable) {
        onProgress?.(Math.round((event.loaded / event.total) * 100))
      }
    })
    request.addEventListener('load', () => {
      let payload: unknown = null
      try {
        payload = request.responseText ? JSON.parse(request.responseText) : null
      } catch {
        payload = null
      }
      if (request.status >= 200 && request.status < 300) {
        resolve(payload as T)
        return
      }
      const detail = (payload as { detail?: string } | null)?.detail
      reject(new ApiError(detail ?? `API request failed (${request.status})`, request.status))
    })
    request.addEventListener('error', () => {
      reject(new ApiError('无法连接上传服务。', 0))
    })
    request.send(formData)
  })
}

import axios from 'axios'

/**
 * Axios client pre-configured for the SOC CoPilot API.
 *
 * Base URL: /api/v1 (proxied by Vite dev server to FastAPI backend)
 *
 * Interceptors:
 *   Request  → Injects the Bearer token from localStorage automatically.
 *   Response → On 401, clears tokens and redirects to /login.
 */
const apiClient = axios.create({
  baseURL: '/api/v1',
  timeout: 30_000,
  headers: { 'Content-Type': 'application/json' },
})

// ---- Request interceptor: inject auth token ----
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// ---- Response interceptor: handle 401 globally ----
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear stale tokens and redirect to login
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default apiClient

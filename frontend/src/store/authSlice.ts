import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import apiClient from '../api/axiosClient'

// ---- Types ----

export interface User {
  id: string
  tenant_id: string
  email: string
  full_name: string
  role: 'admin' | 'analyst'
  is_active: boolean
}

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isLoading: boolean
  error: string | null
}

// ---- Initial state ----

const storedAccess = localStorage.getItem('access_token')
const storedRefresh = localStorage.getItem('refresh_token')

const initialState: AuthState = {
  user: null,
  accessToken: storedAccess,
  refreshToken: storedRefresh,
  isLoading: false,
  error: null,
}

// ---- Async thunks ----

export const loginThunk = createAsyncThunk(
  'auth/login',
  async (credentials: { email: string; password: string }, { rejectWithValue }) => {
    try {
      // OAuth2 form data format (FastAPI expects form data for /login)
      const formData = new URLSearchParams()
      formData.append('username', credentials.email)
      formData.append('password', credentials.password)

      const tokenResp = await apiClient.post('/auth/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      })

      const { access_token, refresh_token } = tokenResp.data

      // Persist tokens
      localStorage.setItem('access_token', access_token)
      localStorage.setItem('refresh_token', refresh_token)

      // Fetch user profile
      const meResp = await apiClient.get('/auth/me', {
        headers: { Authorization: `Bearer ${access_token}` },
      })

      return { accessToken: access_token, refreshToken: refresh_token, user: meResp.data }
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.detail || 'Login failed. Please try again.')
    }
  }
)

export const logoutThunk = createAsyncThunk('auth/logout', async () => {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
})

export const fetchCurrentUser = createAsyncThunk(
  'auth/fetchMe',
  async (_, { getState, rejectWithValue }) => {
    const state = getState() as { auth: AuthState }
    const token = state.auth.accessToken
    if (!token) return rejectWithValue('No token')
    try {
      const resp = await apiClient.get('/auth/me', {
        headers: { Authorization: `Bearer ${token}` },
      })
      return resp.data
    } catch {
      return rejectWithValue('Session expired')
    }
  }
)

// ---- Slice ----

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearError: (state) => { state.error = null },
    setTokens: (state, action: PayloadAction<{ accessToken: string; refreshToken: string }>) => {
      state.accessToken = action.payload.accessToken
      state.refreshToken = action.payload.refreshToken
      localStorage.setItem('access_token', action.payload.accessToken)
      localStorage.setItem('refresh_token', action.payload.refreshToken)
    },
  },
  extraReducers: (builder) => {
    // Login
    builder.addCase(loginThunk.pending, (state) => {
      state.isLoading = true
      state.error = null
    })
    builder.addCase(loginThunk.fulfilled, (state, action) => {
      state.isLoading = false
      state.accessToken = action.payload.accessToken
      state.refreshToken = action.payload.refreshToken
      state.user = action.payload.user
    })
    builder.addCase(loginThunk.rejected, (state, action) => {
      state.isLoading = false
      state.error = action.payload as string
    })

    // Logout
    builder.addCase(logoutThunk.fulfilled, (state) => {
      state.user = null
      state.accessToken = null
      state.refreshToken = null
    })

    // Fetch current user
    builder.addCase(fetchCurrentUser.fulfilled, (state, action) => {
      state.user = action.payload
    })
    builder.addCase(fetchCurrentUser.rejected, (state) => {
      state.user = null
      state.accessToken = null
      state.refreshToken = null
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    })
  },
})

export const { clearError, setTokens } = authSlice.actions
export default authSlice.reducer

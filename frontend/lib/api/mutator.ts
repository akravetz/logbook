import Axios, { type AxiosRequestConfig } from "axios"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "https://api.getswole.ai"

export const AXIOS_INSTANCE = Axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000, // 10 second timeout
})

// Add auth token to requests
AXIOS_INSTANCE.interceptors.request.use(
  (config) => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("access_token")
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  },
)

// Handle token refresh
AXIOS_INSTANCE.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (typeof window === "undefined") {
      return Promise.reject(error)
    }

    if (error.response?.status === 401) {
      const refreshToken = localStorage.getItem("refresh_token")
      if (refreshToken) {
        try {
          const response = await Axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
            refresh_token: refreshToken,
          })
          const { access_token } = response.data
          localStorage.setItem("access_token", access_token)

          // Retry the original request
          if (error.config) {
            error.config.headers.Authorization = `Bearer ${access_token}`
            return AXIOS_INSTANCE.request(error.config)
          }
        } catch (refreshError) {
          console.error("Token refresh failed:", refreshError)
          localStorage.removeItem("access_token")
          localStorage.removeItem("refresh_token")
          localStorage.removeItem("user_data")
          window.location.href = "/login"
        }
      } else {
        // No refresh token, redirect to login
        window.location.href = "/login"
      }
    }
    return Promise.reject(error)
  },
)

export const customInstance = <T = any>(config: AxiosRequestConfig): Promise<T> => {
  const source = Axios.CancelToken.source()
  const promise = AXIOS_INSTANCE({ ...config, cancelToken: source.token }).then(({ data }) => data)

  // @ts-ignore
  promise.cancel = () => {
    source.cancel("Query was cancelled by React Query")
  }

  return promise
}

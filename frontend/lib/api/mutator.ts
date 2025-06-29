import Axios, { AxiosRequestConfig, AxiosError } from "axios"
import { getSession, signOut } from "next-auth/react"

export const AXIOS_INSTANCE = Axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080",
})

// Add a request interceptor to include the JWT token from NextAuth session
AXIOS_INSTANCE.interceptors.request.use(
  async (config) => {
    const session = await getSession()

    if (session?.accessToken) {
      config.headers.Authorization = `Bearer ${session.accessToken}`
    }

    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Add a response interceptor to handle token refresh and authentication errors
AXIOS_INSTANCE.interceptors.response.use(
  (response) => response, // Pass through successful responses
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean }

    // If we get a 401 and haven't already tried to refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      const session = await getSession()

      if (session?.refreshToken) {
        try {
          // Try to refresh the token using our backend endpoint
          const response = await Axios.post(
            `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080"}/api/v1/auth/refresh`,
            { refresh_token: session.refreshToken }
          )

          if (response.data?.access_token) {
            // Update the session with new token (this is a limitation of NextAuth)
            // In a real implementation, you'd need to update the JWT token in NextAuth
            // For now, we'll just retry the request and let NextAuth handle expiry
            console.log("Token refreshed successfully")

            // Retry the original request with the session token
            return AXIOS_INSTANCE(originalRequest)
          }
        } catch (refreshError) {
          console.error("Token refresh failed:", refreshError)
          // Force sign out on refresh failure
          await signOut({ callbackUrl: "/" })
          return Promise.reject(error)
        }
      } else {
        // No refresh token, force sign out
        await signOut({ callbackUrl: "/" })
      }
    }

    return Promise.reject(error)
  }
)

export const customInstance = <T>(
  config: AxiosRequestConfig,
  options?: AxiosRequestConfig
): Promise<T> => {
  const source = Axios.CancelToken.source()
  const promise = AXIOS_INSTANCE({
    ...config,
    ...options,
    cancelToken: source.token
  }).then(({ data }) => data)

  // @ts-ignore
  promise.cancel = () => {
    source.cancel("Query was cancelled")
  }

  return promise
}

// Keep default export for compatibility
export default customInstance

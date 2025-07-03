import Axios, { AxiosError, AxiosRequestConfig } from "axios"
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

// Add a response interceptor to handle authentication errors
AXIOS_INSTANCE.interceptors.response.use(
  (response) => response, // Pass through successful responses
  async (error: AxiosError) => {
    // If we get a 401, the token is invalid/expired
    // NextAuth JWT callback should have already tried to refresh
    if (error.response?.status === 401) {
      const session = await getSession()

      // If we have a refresh error, force sign out
      if (session?.error === "RefreshTokenError") {
        console.error("Refresh token expired, forcing sign out")
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
    cancelToken: source.token,
  }).then(({ data }) => data)

  // @ts-ignore
  promise.cancel = () => {
    source.cancel("Query was cancelled")
  }

  return promise
}

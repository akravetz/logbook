import Axios, { AxiosError, AxiosRequestConfig } from "axios"
import { getSession, signOut } from "next-auth/react"

export const AXIOS_INSTANCE = Axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080",
})

// Add a request interceptor to include the session token from NextAuth
AXIOS_INSTANCE.interceptors.request.use(
  async (config) => {
    const session = await getSession()

    if (session?.sessionToken) {
      config.headers.Authorization = `Bearer ${session.sessionToken}`
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
    // If we get a 401, the session has expired - force sign out
    if (error.response?.status === 401) {
      // Log error for debugging in development
      if (process.env.NODE_ENV === 'development') {
        console.error("Session expired, forcing sign out")
      }
      await signOut({ callbackUrl: "/" })
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

import Axios, { AxiosError, AxiosRequestConfig } from "axios"
import { getSession, signOut } from "next-auth/react"
import { logger } from "@/lib/logger"

const baseURL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080"
logger.debug("🌐 API Client Configuration:", {
  baseURL,
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  NODE_ENV: process.env.NODE_ENV,
})

export const AXIOS_INSTANCE = Axios.create({
  baseURL,
})

// Add a request interceptor to include the session token from NextAuth
AXIOS_INSTANCE.interceptors.request.use(
  async (config) => {
    const session = await getSession()

    logger.debug("📤 API Request Interceptor:", {
      url: config.url,
      method: config.method,
      baseURL: config.baseURL,
      hasSession: !!session,
      hasSessionToken: !!session?.sessionToken,
    })

    if (session?.sessionToken) {
      config.headers.Authorization = `Bearer ${session.sessionToken}`
      logger.debug("🔑 Added Authorization header to request")
    }

    return config
  },
  (error) => {
    logger.error("❌ Request interceptor error:", error)
    return Promise.reject(error)
  }
)

// Add a response interceptor to handle authentication errors
AXIOS_INSTANCE.interceptors.response.use(
  (response) => {
    logger.debug("📥 API Response Success:", {
      url: response.config.url,
      status: response.status,
      statusText: response.statusText,
    })
    return response
  }, // Pass through successful responses
  async (error: AxiosError) => {
    logger.error("📥 API Response Error:", {
      url: error.config?.url,
      status: error.response?.status,
      statusText: error.response?.statusText,
      message: error.message,
      code: error.code,
    })

    // If we get a 401, the session has expired - force sign out
    if (error.response?.status === 401) {
      logger.error("🔒 Session expired, forcing sign out")
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

import Axios, { AxiosError, AxiosRequestConfig } from "axios"
import { getSession, signOut } from "next-auth/react"

export const AXIOS_INSTANCE = Axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080",
})

// Simple token store to bypass NextAuth caching issues
let freshTokenStore: { accessToken: string | null, refreshToken: string | null } = {
  accessToken: null,
  refreshToken: null
}

// Add a request interceptor to include the JWT token from NextAuth session
AXIOS_INSTANCE.interceptors.request.use(
  async (config) => {
    // Try to get fresh token from store first, then fall back to session
    let accessToken = freshTokenStore.accessToken
    let refreshToken = freshTokenStore.refreshToken

    if (!accessToken) {
      const session = await getSession()
      accessToken = session?.accessToken || null
      refreshToken = session?.refreshToken || null

      // Update store with session tokens
      freshTokenStore.accessToken = accessToken
      freshTokenStore.refreshToken = refreshToken
    }

    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`
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
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean }

    // If we get a 401 and haven't already retried
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        console.log("401 detected, attempting manual token refresh...")

        // Get refresh token from store or session
        const refreshToken = freshTokenStore.refreshToken || (await getSession())?.refreshToken

        if (refreshToken) {
          console.log("Found refresh token, calling backend refresh endpoint...")

          // Call our backend refresh endpoint directly
          const refreshResponse = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080"}/api/v1/auth/refresh`,
            {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify({
                refresh_token: refreshToken,
              }),
            }
          )

          if (refreshResponse.ok) {
            const refreshedTokens = await refreshResponse.json()
            console.log("Token refresh successful, updating token store...")

            // Update our token store immediately
            freshTokenStore.accessToken = refreshedTokens.access_token
            freshTokenStore.refreshToken = refreshedTokens.refresh_token

            // Update the authorization header with the fresh token
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${refreshedTokens.access_token}`
              console.log("Using fresh token from token store")
            }

            console.log("Retrying request with fresh token...")
            return AXIOS_INSTANCE(originalRequest)
          } else {
            console.error("Token refresh failed:", refreshResponse.status)
            throw new Error(`Refresh failed: ${refreshResponse.status}`)
          }
        } else {
          console.error("No refresh token available")
          throw new Error("No refresh token available")
        }
      } catch (refreshError) {
        console.error("Failed to refresh token:", refreshError)
        console.log("Forcing sign out due to token refresh failure")
        // Clear token store
        freshTokenStore.accessToken = null
        freshTokenStore.refreshToken = null
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

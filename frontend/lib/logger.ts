/**
 * Custom logger utility that handles client/server context appropriately.
 *
 * Logging behavior:
 * - Server-side: Always logs (for debugging and monitoring)
 * - Client-side: Only logs in development mode
 * - Production client: No console output to keep browser clean
 */

const createLogger = () => {
  const isServer = typeof window === 'undefined'
  const isDevelopment = process.env.NODE_ENV === 'development'

  // Determine if we should log based on context
  const shouldLog = isServer || isDevelopment

  return {
    /**
     * Log informational messages
     * Server: Always logs | Client: Development only
     */
    info: (message: string, ...args: any[]) => {
      if (shouldLog) {
        console.log(message, ...args)
      }
    },

    /**
     * Log error messages
     * Server: Always logs | Client: Development only
     */
    error: (message: string, ...args: any[]) => {
      if (shouldLog) {
        console.error(message, ...args)
      }
    },

    /**
     * Log warning messages
     * Server: Always logs | Client: Development only
     */
    warn: (message: string, ...args: any[]) => {
      if (shouldLog) {
        console.warn(message, ...args)
      }
    },

    /**
     * Log debug messages (development only, even on server)
     * Useful for verbose debugging that shouldn't appear in production logs
     */
    debug: (message: string, ...args: any[]) => {
      if (isDevelopment) {
        console.debug(message, ...args)
      }
    }
  }
}

export const logger = createLogger()

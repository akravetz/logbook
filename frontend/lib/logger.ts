import pino from 'pino'
import { randomUUID } from 'crypto'

// Get request ID for correlation
const getRequestId = () => randomUUID()

// Logger configuration
const createLogger = () => {
  const isProduction = process.env.NODE_ENV === 'production'

  return pino({
    level: isProduction ? 'info' : 'debug',

    // Production: JSON format for parsing
    // Development: Pretty printing
    transport: !isProduction ? {
      target: 'pino-pretty',
      options: {
        colorize: true,
        ignore: 'pid,hostname',
        translateTime: 'SYS:yyyy-mm-dd HH:MM:ss'
      }
    } : undefined,

    // Add service identification
    base: {
      service: 'workout-tracker-frontend',
      environment: process.env.NODE_ENV,
      version: process.env.npm_package_version || '1.0.0'
    },

    // Redact sensitive data
    redact: [
      'access_token',
      'refresh_token',
      'id_token',
      'password',
      'authorization',
      'cookie',
      'req.headers.authorization',
      'req.headers.cookie',
      'body.access_token',
      'account.access_token',
      'account.refresh_token',
      'account.id_token'
    ],

    // Custom formatters
    formatters: {
      level: (label) => ({ level: label }),
    },

    // Timestamp in ISO format
    timestamp: pino.stdTimeFunctions.isoTime
  })
}

export const logger = createLogger()

// Create child logger with correlation ID
export const createRequestLogger = (requestId?: string) => {
  return logger.child({
    requestId: requestId || getRequestId(),
    source: 'server'
  })
}

// OAuth-specific logger
export const createOAuthLogger = (provider: string, requestId?: string) => {
  return logger.child({
    requestId: requestId || getRequestId(),
    source: 'oauth',
    provider,
    component: 'auth'
  })
}

// Environment configuration logger
export const createConfigLogger = () => {
  return logger.child({
    source: 'config',
    component: 'environment'
  })
}

// API client logger
export const createApiLogger = (requestId?: string) => {
  return logger.child({
    requestId: requestId || getRequestId(),
    source: 'api-client',
    component: 'http'
  })
}

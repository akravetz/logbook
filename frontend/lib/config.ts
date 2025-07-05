export const config = {
  logging: {
    level: process.env.LOG_LEVEL || (process.env.NODE_ENV === 'production' ? 'info' : 'debug'),
    enableConsole: process.env.ENABLE_CONSOLE_LOGS !== 'false',
    enableRemote: process.env.NODE_ENV === 'production',
    service: 'workout-tracker-frontend'
  },
  oauth: {
    debug: process.env.NODE_ENV === 'development',
    logSensitiveData: process.env.LOG_SENSITIVE_DATA === 'true', // Never enable in production
    enableDetailedLogging: process.env.OAUTH_DETAILED_LOGGING === 'true'
  },
  api: {
    baseUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080",
    timeout: parseInt(process.env.API_TIMEOUT || '30000'),
    enableRequestLogging: process.env.API_REQUEST_LOGGING !== 'false'
  }
}

// Validate critical environment variables
export const validateEnvironment = () => {
  const required = {
    GOOGLE_CLIENT_ID: process.env.GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET: process.env.GOOGLE_CLIENT_SECRET,
    NEXTAUTH_SECRET: process.env.NEXTAUTH_SECRET,
    NEXTAUTH_URL: process.env.NEXTAUTH_URL
  }

  const missing = Object.entries(required)
    .filter(([_, value]) => !value)
    .map(([key]) => key)

  if (missing.length > 0) {
    throw new Error(`Missing required environment variables: ${missing.join(', ')}`)
  }

  return required
}

import NextAuth from 'next-auth'
import { authOptions } from '@/lib/auth'
import { createRequestLogger } from '@/lib/logger'
import { NextRequest } from 'next/server'

// Wrap the handler to add request logging
const handler = async (req: NextRequest, context: any) => {
  const requestId = crypto.randomUUID()
  const logger = createRequestLogger(requestId)

  const url = new URL(req.url)

  // Log incoming request details
  logger.info({
    event: 'auth_request',
    method: req.method,
    pathname: url.pathname,
    search: url.search,
    userAgent: req.headers.get('user-agent'),
    referer: req.headers.get('referer'),
    origin: req.headers.get('origin'),
    host: req.headers.get('host'),
    // URL search params (safe ones - no tokens)
    searchParams: {
      state: url.searchParams.get('state') ? '[PRESENT]' : null,
      code: url.searchParams.get('code') ? '[PRESENT]' : null,
      error: url.searchParams.get('error'),
      error_description: url.searchParams.get('error_description'),
      callbackUrl: url.searchParams.get('callbackUrl'),
      provider: url.searchParams.get('provider')
    },
    environment: process.env.NODE_ENV,
    timestamp: new Date().toISOString()
  }, 'NextAuth API request received')

  try {
    const response = await NextAuth(authOptions)(req, context)

    logger.info({
      event: 'auth_response',
      requestId,
      statusCode: response.status,
      statusText: response.statusText,
      hasLocation: !!response.headers.get('location'),
      location: response.headers.get('location'), // Safe to log redirect locations
      responseHeaders: {
        'content-type': response.headers.get('content-type'),
        'set-cookie': response.headers.get('set-cookie') ? '[PRESENT]' : null,
        'cache-control': response.headers.get('cache-control')
      }
    }, 'NextAuth API response sent')

    return response
  } catch (error) {
    logger.error({
      event: 'auth_error',
      requestId,
      error: error instanceof Error ? {
        name: error.name,
        message: error.message,
        stack: process.env.NODE_ENV === 'development' ? error.stack : undefined
      } : String(error)
    }, 'NextAuth API error occurred')
    throw error
  }
}

export { handler as GET, handler as POST }

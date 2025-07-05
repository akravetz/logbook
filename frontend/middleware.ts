import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const requestId = crypto.randomUUID()

  // Only log auth-related routes to avoid noise
  if (request.nextUrl.pathname.startsWith('/api/auth')) {
    // Use console.log for middleware since Pino isn't available here
    console.log(JSON.stringify({
      timestamp: new Date().toISOString(),
      level: 'info',
      service: 'workout-tracker-frontend',
      source: 'middleware',
      event: 'auth_middleware',
      requestId,
      method: request.method,
      pathname: request.nextUrl.pathname,
      search: request.nextUrl.search,
      userAgent: request.headers.get('user-agent'),
      origin: request.headers.get('origin'),
      referer: request.headers.get('referer'),
      host: request.headers.get('host'),
             ip: request.headers.get('x-forwarded-for') || request.headers.get('x-real-ip'),
      // Safe URL params (no tokens)
      hasState: request.nextUrl.searchParams.has('state'),
      hasCode: request.nextUrl.searchParams.has('code'),
      hasError: request.nextUrl.searchParams.has('error'),
      provider: request.nextUrl.searchParams.get('provider'),
      callbackUrl: request.nextUrl.searchParams.get('callbackUrl'),
      environment: process.env.NODE_ENV
    }))
  }

  const response = NextResponse.next()

  // Add request ID to response headers for correlation
  response.headers.set('x-request-id', requestId)

  return response
}

export const config = {
  matcher: '/api/auth/:path*'
}

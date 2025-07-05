import { getSession, signOut } from "next-auth/react";
import { createApiLogger } from '../logger';
import { config } from '../config';

const logger = createApiLogger();

export const mutator = (url: string, options: RequestInit = {}) => {
  const requestId = crypto.randomUUID();
  const requestLogger = createApiLogger(requestId);

     return getSession().then(async (session) => {
     const headers: Record<string, string> = {
       'Content-Type': 'application/json',
       'x-request-id': requestId,
     };

     // Add existing headers
     if (options.headers) {
       Object.assign(headers, options.headers);
     }

     if (session?.sessionToken) {
       headers['Authorization'] = `Bearer ${session.sessionToken}`;
     }

    const startTime = Date.now();

    // Log request start
    if (config.api.enableRequestLogging) {
      requestLogger.info({
        event: 'api_request_start',
        method: options.method || 'GET',
        url: url.replace(/\/\d+/g, '/:id'), // Sanitize IDs in URLs
        hasAuth: !!session?.sessionToken,
        userId: session?.userId,
        bodySize: options.body ? JSON.stringify(options.body).length : 0,
        environment: process.env.NODE_ENV
      }, 'API request started');
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      const duration = Date.now() - startTime;
      const success = response.ok;

      // Log response
      if (config.api.enableRequestLogging) {
        requestLogger.info({
          event: 'api_request_complete',
          method: options.method || 'GET',
          url: url.replace(/\/\d+/g, '/:id'),
          statusCode: response.status,
          statusText: response.statusText,
          duration,
          success,
          responseSize: response.headers.get('content-length'),
          contentType: response.headers.get('content-type'),
          rateLimitRemaining: response.headers.get('x-ratelimit-remaining'),
          backendRequestId: response.headers.get('x-request-id')
        }, success ? 'API request completed successfully' : 'API request failed');
      }

      // Log errors with more detail
      if (!response.ok) {
        // Handle 401 Unauthorized - sign out user
        if (response.status === 401) {
          requestLogger.warn({
            event: 'api_request_unauthorized',
            method: options.method || 'GET',
            url: url.replace(/\/\d+/g, '/:id'),
            statusCode: response.status,
            duration,
            hasAuth: !!session?.sessionToken,
            userId: session?.userId
          }, 'API request returned 401 - signing out user');

          // Sign out the user automatically
          await signOut({ callbackUrl: '/auth/login' });
          return response; // Return early to prevent further processing
        }

        let errorBody = '';
        try {
          const clonedResponse = response.clone();
          errorBody = await clonedResponse.text();
        } catch (e) {
          requestLogger.warn({
            requestId,
            parseError: String(e)
          }, 'Failed to parse error response body');
        }

        requestLogger.error({
          event: 'api_request_error',
          method: options.method || 'GET',
          url: url.replace(/\/\d+/g, '/:id'),
          statusCode: response.status,
          statusText: response.statusText,
          duration,
          errorBody: errorBody.substring(0, 500), // Limit error body size
          hasAuth: !!session?.sessionToken,
          userId: session?.userId
        }, 'API request returned error status');
      }

      return response;
    } catch (error) {
      const duration = Date.now() - startTime;

      requestLogger.error({
        event: 'api_request_exception',
        method: options.method || 'GET',
        url: url.replace(/\/\d+/g, '/:id'),
        duration,
        error: error instanceof Error ? {
          name: error.name,
          message: error.message,
          stack: config.oauth.debug ? error.stack : undefined
        } : String(error),
        hasAuth: !!session?.sessionToken,
        userId: session?.userId
      }, 'API request threw exception');

      throw error;
    }
  });
};

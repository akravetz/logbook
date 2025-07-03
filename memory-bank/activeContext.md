# Active Context

## Current Focus
**Token Rotation Implementation COMPLETE**: Successfully implemented proper JWT token rotation following Auth.js best practices. This resolves token expiration issues by automatically refreshing tokens before they expire and implementing one-time refresh token usage for enhanced security.

## Recent Work Completed

### **Token Rotation Implementation (LATEST) ✅**

#### **Backend Token Rotation**
- **Enhanced Refresh Endpoint**: Updated `/api/v1/auth/refresh` to return token pairs
  - Returns both new access AND refresh tokens (following Auth.js guide)
  - Implements one-time refresh token usage pattern
  - Includes `expires_at` timestamp in response for frontend tracking
  - Updated `TokenRefreshResponse` schema with new fields

- **JWT Manager Updates**: Added `refresh_token_pair()` method
  - Creates new token pair from valid refresh token
  - Returns expiration timestamp for frontend usage
  - Maintains existing token validation logic
  - Comprehensive test coverage added

#### **Frontend Token Rotation**
- **NextAuth JWT Callback Enhancement**: Automatic token refresh logic
  - Checks token expiration on each session request
  - Refreshes if token expires in < 5 minutes (proactive refresh)
  - Stores new token pair in NextAuth session
  - Sets `RefreshTokenError` on refresh failure

- **Error Handling Implementation**: Graceful handling of expired tokens
  - Custom `useAuthErrorHandler` hook monitors session errors
  - Automatic logout on `RefreshTokenError`
  - Integrated into `AuthProvider` for app-wide coverage
  - Simplified axios interceptor (removed manual refresh logic)

- **TypeScript Updates**: Extended NextAuth types
  - Added `tokenExpiresAt` to track expiration
  - Added `error` field for refresh failures
  - Maintains type safety throughout auth flow

#### **Security Improvements**
- **One-Time Refresh Tokens**: Old refresh tokens invalidated after use
- **Proactive Refresh**: Tokens refreshed before expiration to prevent auth interruptions
- **Secure Storage**: Tokens stored in encrypted NextAuth JWT cookies
- **Race Condition Awareness**: Documentation notes potential concurrent refresh issues

#### **Testing & Verification**
- **Backend Tests**: Updated refresh token tests for new response format
- **JWT Tests**: Added `test_refresh_token_pair` for new functionality
- **Manual Test Script**: Created `test-token-rotation.ts` for verification
- **All tests passing**: Backend auth tests continue to pass

### **Development Login Implementation (LATEST) ✅**

#### **Backend Development Authentication**
- **Dev Login Endpoint**: Added `/api/v1/auth/dev-login` POST endpoint
  - Environment-restricted: Only available when `ENVIRONMENT=development`
  - Email prefix system: Automatically adds "dev:" prefix to prevent conflicts
  - User creation: Creates users with display names like "Dev User (email)"
  - JWT integration: Uses same token generation as Google OAuth
  - Comprehensive error handling with proper HTTP status codes

- **Service Layer Integration**: Enhanced `AuthService` with development authentication
  - `authenticate_with_dev_login()` method for dev user creation/login
  - Reuses existing JWT infrastructure for consistency
  - Proper error handling for duplicate users and authentication failures

- **Schema Integration**: Added `DevLoginRequest` and `DevLoginResponse` schemas
  - Type-safe email input validation
  - Consistent response format with existing auth endpoints
  - Full OpenAPI documentation generation

#### **Frontend Development Login**
- **NextAuth.js Integration**: Added `CredentialsProvider` for development
  - Environment-controlled: Only appears when `NODE_ENV === "development"`
  - Seamless integration with existing Google OAuth provider
  - Uses same NextAuth flow for consistent user experience

- **Enhanced Login Screen**: Added development login form
  - Clean UI with "Development Mode" indicator
  - Email input with proper validation
  - Proper loading states and error handling
  - Maintains existing Google OAuth option

- **Complete Auth Flow**: Full integration with existing authentication system
  - NextAuth `signIn('dev-login')` integration
  - Backend token exchange via `/api/v1/auth/dev-login`
  - Automatic JWT token management
  - Same session handling as Google OAuth

#### **Comprehensive Testing**
- **Backend Testing**: 93+ authentication tests passing
  - Service layer tests for user creation, login, error scenarios
  - Router tests for success cases, production blocking, validation
  - FastAPI dependency injection patterns (no patching)
  - Environment-based availability testing

- **API Integration Testing**: Complete endpoint verification
  - New user creation with proper "dev:" prefix
  - Existing user login with token refresh
  - Production environment blocking
  - Error handling for invalid inputs

#### **Development Benefits Achieved**
- ✅ **Simplified Workflow**: Login with any email, no Google OAuth setup required
- ✅ **Production Security**: Completely disabled in production environments
- ✅ **No Code Duplication**: Reuses all existing NextAuth and JWT infrastructure
- ✅ **Consistent UX**: Same authentication flow as production Google OAuth
- ✅ **Environment Isolation**: "dev:" prefix prevents conflicts with real users

### **OpenAPI Workflow Optimization (LATEST) ✅**

#### **Eliminated Duplication**
- **Single Source of Truth**: OpenAPI spec now generated directly to `frontend/openapi.json`
- **Backend Taskfile Updates**: Modified `generate-openapi` task to output to frontend
- **Frontend Integration**: Updated `orval.config.ts` to read from local file
- **Cleanup**: Removed duplicate `backend/openapi.json` and added to `.gitignore`

#### **Streamlined Workflow**
```bash
# Before: Generate → Copy → Generate Types
task generate-openapi        # → backend/openapi.json
cp openapi.json ../frontend/ # → frontend/openapi.json
npm run generate-api         # → TypeScript types

# After: Generate → Generate Types
task generate-openapi        # → frontend/openapi.json
npm run generate-api         # → TypeScript types
```

#### **Improved Maintainability**
- **No File Duplication**: Single `openapi.json` file where it's actually used
- **Simplified Tasks**: Removed unnecessary copy steps
- **Clean Structure**: Backend focuses on generation, frontend handles consumption
- **Version Control**: Prevent accidental commits of local OpenAPI copies

### **Previous Major Work**
- **NextAuth.js OAuth Migration**: Complete migration from backend OAuth to NextAuth.js client-side OAuth
- **Test Infrastructure Optimization**: Consolidated duplicated test fixtures across test suite
- **Frontend OAuth Integration**: Successfully integrated frontend with backend authentication

## Next Steps

### **Immediate**
1. **Google OAuth Configuration**: Set up actual Google OAuth app and configure credentials
   - Create Google Cloud project and OAuth 2.0 credentials
   - Update `.env.local` with real `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
   - Test complete end-to-end OAuth flow alongside dev login

2. **Production Deployment**: Configure authentication for production environment
   - Set up proper `NEXTAUTH_SECRET` for production
   - Configure production OAuth redirect URLs
   - Verify dev login is properly blocked in production

### **Future Development**
- **Workout Module Integration**: Connect authenticated users to workout tracking
- **User Profile Enhancement**: Complete user settings and preferences
- **Mobile App Foundation**: Leverage JWT tokens for future mobile authentication

## Technical Decisions Made

### **Development Authentication Strategy**
- **Decision**: Implement parallel development login alongside Google OAuth
- **Rationale**:
  - Eliminates Google OAuth setup friction for developers
  - Maintains identical authentication flow and token management
  - Environment-based availability prevents production exposure
  - Reuses existing infrastructure for consistency

### **OpenAPI Generation Strategy**
- **Decision**: Generate OpenAPI spec directly to frontend directory
- **Rationale**:
  - Eliminates unnecessary file duplication
  - Simplifies development workflow
  - Reduces potential for sync issues
  - Frontend is the primary consumer of the OpenAPI spec

### **Authentication Architecture**
- **Decision**: Hybrid approach - NextAuth for OAuth/dev login, backend JWT for API access
- **Rationale**:
  - Leverages NextAuth's authentication expertise
  - Maintains existing JWT-based API authentication
  - Allows backend to remain stateless
  - Enables consistent token management across auth methods

### **Token Rotation Strategy**
- **Decision**: Implement Auth.js-style token rotation in NextAuth JWT callback
- **Rationale**:
  - Follows established best practices from Auth.js documentation
  - Automatic refresh prevents user disruption
  - Maintains security with one-time refresh tokens
  - Integrates seamlessly with existing NextAuth setup

### **Refresh Timing**
- **Decision**: Refresh tokens when < 5 minutes remain before expiration
- **Rationale**:
  - Prevents edge cases where token expires during request
  - Provides buffer for network latency
  - Balances security with user experience
  - Allows time for retry on transient failures

### **Error Handling Approach**
- **Decision**: Force re-authentication on refresh failure
- **Rationale**:
  - Clear security boundary - no invalid tokens
  - Simple user experience - just login again
  - Prevents infinite refresh loops
  - Matches common web application patterns

## Risk Mitigation
- **Development/Production Isolation**: Environment checks prevent dev login in production
- **Token Security**: Same JWT validation and refresh logic as Google OAuth
- **User Conflicts**: "dev:" email prefix prevents conflicts with real users
- **Workflow Consistency**: Development and production use identical authentication flows

# Development Authentication Guide

## Overview

This application now supports **dual-mode authentication** that dramatically simplifies the development workflow while maintaining production security.

- **Production Mode**: Uses Google OAuth (unchanged)
- **Development Mode**: Simple email-based login that bypasses Google OAuth

## Quick Start (5 minutes)

### 1. Backend Setup

```bash
cd backend
cp .env.example .env
# Edit .env and ensure:
ENVIRONMENT=development
```

### 2. Frontend Setup

```bash
cd frontend
cp .env.local.example .env.local
# Edit .env.local and ensure:
NEXT_PUBLIC_ENABLE_DEV_AUTH=true
```

### 3. Start Services

```bash
# Terminal 1: Backend
cd backend && uv run python -m workout_api.core.main

# Terminal 2: Frontend
cd frontend && npm run dev
```

### 4. Login with Development Mode

1. Go to http://localhost:3000
2. You'll see a **Development Mode** section below the Google login
3. Enter any email address (e.g., `test@example.com`)
4. Click "Dev Login" or use quick buttons (Admin, User, Test)
5. You're instantly logged in with full API access!

## Features

### 🚀 **Instant Login**
- Enter any email address to create/login as that user
- No Google OAuth configuration needed
- Creates users instantly with proper JWT tokens

### 🔒 **Production Safe**
- Automatically disabled when `ENVIRONMENT=production`
- Multiple security guards prevent accidental production use
- Zero impact on production Google OAuth flow

### 🎯 **Identical Experience**
- Same JWT tokens as Google OAuth
- Same API access and permissions
- Same session management
- Same user dashboard experience

### 👥 **Quick Test Users**
- **Admin Button**: Logs in as `admin@example.com`
- **User Button**: Logs in as `user@example.com`
- **Test Button**: Logs in as `test@example.com`
- **Custom Email**: Enter any email for specific testing

## Benefits

| Aspect | Before (Google OAuth) | After (Dev Mode) |
|--------|----------------------|------------------|
| Setup Time | 30+ minutes | <5 minutes |
| Google Config | Required | Not needed |
| User Creation | Manual OAuth flow | Instant email entry |
| Team Onboarding | Complex setup docs | Clone, install, run |
| Testing Speed | Minutes per user | Seconds per user |
| Offline Development | Impossible | Full functionality |

## Technical Details

### Backend Implementation

**Development Endpoint**: `POST /api/v1/auth/dev-login`
```json
{
  "email": "developer@example.com",
  "name": "Developer User"
}
```

**Response** (identical to Google OAuth):
```json
{
  "user": {
    "id": 1,
    "email_address": "developer@example.com",
    "google_id": "dev:developer@example.com",
    "name": "Developer User",
    "is_active": true,
    "is_admin": false
  },
  "tokens": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "Bearer",
    "expires_in": 1800
  },
  "dev_mode": true
}
```

### Frontend Implementation

**NextAuth.js Integration**: Uses `CredentialsProvider` that:
- Only loads when `NODE_ENV=development` AND `NEXT_PUBLIC_ENABLE_DEV_AUTH=true`
- Calls backend `/dev-login` endpoint
- Returns tokens compatible with existing session management
- Integrates seamlessly with existing Google OAuth provider

### User Identification

Development users are identified by:
- `google_id` starts with `"dev:"` (e.g., `"dev:test@example.com"`)
- Easy to filter in database queries
- Clear identification in logs and admin interfaces
- No impact on production user data

## Environment Configuration

### Development Mode (Enabled)

**Backend** (`.env`):
```bash
ENVIRONMENT=development  # Enables dev-login endpoint
```

**Frontend** (`.env.local`):
```bash
NEXT_PUBLIC_ENABLE_DEV_AUTH=true  # Shows dev UI
```

### Production Mode (Disabled)

**Backend** (`.env`):
```bash
ENVIRONMENT=production  # Disables dev-login endpoint
```

**Frontend** (`.env.local`):
```bash
NEXT_PUBLIC_ENABLE_DEV_AUTH=false  # or remove entirely
```

## Security

### Production Protection
- **Environment Guards**: Dev endpoint only works when `ENVIRONMENT=development`
- **Router Guards**: Endpoint not registered in production builds
- **UI Guards**: Development UI not shown in production
- **Documentation**: Dev endpoint hidden from OpenAPI docs in production

### Token Security
- **Same Validation**: Identical JWT validation as Google OAuth
- **Same Expiration**: Same token expiration policies
- **Same Refresh**: Same refresh token logic
- **Same Permissions**: Same user permission system

## Troubleshooting

### Development Mode Not Showing
1. Check `NODE_ENV=development` (should be automatic in dev)
2. Check `NEXT_PUBLIC_ENABLE_DEV_AUTH=true` in `.env.local`
3. Restart frontend dev server

### Backend Endpoint Not Working
1. Check `ENVIRONMENT=development` in backend `.env`
2. Check backend server is running on port 8080
3. Try: `curl -X POST http://localhost:8080/api/v1/auth/dev-login -H "Content-Type: application/json" -d '{"email":"test@example.com"}'`

### Authentication Failing
1. Check browser dev tools for error messages
2. Check backend logs for authentication errors
3. Verify API URL: `NEXT_PUBLIC_API_URL=http://localhost:8080`

## Switching Between Modes

### Use Google OAuth (Traditional)
1. Set up Google OAuth credentials in `.env.local`
2. Use the "Sign in with Google" button
3. Development mode will still be available as fallback

### Use Development Mode Only
1. Don't configure Google OAuth credentials
2. Only the Development Mode section will work
3. Perfect for pure API development

### Disable Development Mode
1. Set `NEXT_PUBLIC_ENABLE_DEV_AUTH=false` or remove it
2. Restart frontend - development UI disappears
3. Only Google OAuth will be available

## Team Usage Patterns

### New Developer Onboarding
```bash
git clone <repo>
cd backend && cp .env.example .env
cd ../frontend && cp .env.local.example .env.local
# Start both services and you're ready!
```

### API Testing
```bash
# Create test users instantly
POST /api/v1/auth/dev-login {"email": "admin@test.com"}
POST /api/v1/auth/dev-login {"email": "user@test.com"}
POST /api/v1/auth/dev-login {"email": "customer@test.com"}
```

### Feature Development
1. Use development mode for rapid iteration
2. Test with multiple user types using quick buttons
3. Switch to Google OAuth for final integration testing

## FAQ

**Q: Is this secure for production?**
A: Yes, multiple guards prevent development features in production environments.

**Q: Can I still use Google OAuth in development?**
A: Yes, both modes work simultaneously. You can choose which to use.

**Q: Do development users affect production data?**
A: No, development users are clearly marked with `"dev:"` prefix and only exist in development databases.

**Q: Can I customize the development user experience?**
A: Yes, you can modify the quick login buttons or add custom user creation logic in the backend.

**Q: How do I identify development users?**
A: All development users have `google_id` starting with `"dev:"`, making them easy to filter.

**Q: Will this work for mobile apps?**
A: The backend `/dev-login` endpoint works for any client. You'd need to implement the UI in your mobile app.

## Migration Notes

### From Google OAuth Setup
- **No breaking changes**: Existing Google OAuth continues to work
- **Gradual adoption**: Teams can migrate at their own pace
- **Rollback**: Simply remove development environment flags

### Database Considerations
- **No schema changes**: Uses existing user table structure
- **Clear identification**: Development users marked with `"dev:"` prefix
- **Easy cleanup**: Can filter and remove development users if needed

## Support

If you encounter issues:
1. Check this guide's troubleshooting section
2. Verify environment configuration
3. Check browser dev tools and server logs
4. Ask team for configuration help

---

**Happy coding with 5-minute setup! 🚀**

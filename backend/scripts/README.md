# OAuth Authentication Testing Guide

This directory contains scripts for testing the OAuth authentication flow from the command line, including approaches that don't require a browser.

## 🎯 Quick Start

**Easiest approach - Test with mock tokens:**
```bash
# Create and test with JWT tokens (no OAuth needed)
./test_auth_curl.sh create_tokens
./test_auth_curl.sh validate_token
./test_auth_curl.sh refresh_token
```

**Full testing:**
```bash
# Run all auth tests
./test_auth_curl.sh all
```

## 📁 Available Scripts

### 1. `test_auth_curl.sh` - Bash/curl Testing
Comprehensive testing using curl commands and bash scripting.

**Features:**
- ✅ OAuth initiation testing
- ✅ JWT token creation and validation
- ✅ Token refresh testing
- ✅ Session management testing
- ✅ Real OAuth callback testing
- ✅ JSON output formatting

**Usage:**
```bash
./test_auth_curl.sh help                    # Show all commands
./test_auth_curl.sh all                     # Run all tests
./test_auth_curl.sh create_tokens           # Create test tokens
./test_auth_curl.sh validate_token          # Test token validation
./test_auth_curl.sh oauth_callback <code>   # Test with real auth code
```

### 2. `test_oauth.py` - Python Testing Script
Advanced testing with async HTTP clients and Google OAuth simulation.

**Features:**
- ✅ Mock OAuth flow simulation
- ✅ Manual OAuth flow with browser integration
- ✅ Comprehensive error handling
- ✅ Token lifecycle testing
- ✅ Pretty printed output

**Usage:**
```bash
uv run scripts/test_oauth.py mock       # Mock OAuth test (no browser)
uv run scripts/test_oauth.py manual     # Manual OAuth test (requires browser)
uv run scripts/test_oauth.py tokens     # Just create test tokens
```

### 3. `quick_curl_examples.sh` - Quick Reference
Raw curl commands for manual testing.

**Usage:**
```bash
./quick_curl_examples.sh                # Show curl examples
```

## 🔧 Testing Approaches

### Approach 1: Mock Token Testing (No OAuth)
**Best for:** Development, CI/CD, unit testing

```bash
# 1. Create test JWT tokens
./test_auth_curl.sh create_tokens

# 2. Test protected endpoints
./test_auth_curl.sh validate_token
./test_auth_curl.sh session_info
./test_auth_curl.sh refresh_token
```

**Advantages:**
- ✅ No browser required
- ✅ Fast execution
- ✅ Consistent results
- ✅ Good for automation

### Approach 2: Real OAuth Flow Testing
**Best for:** Integration testing, debugging OAuth issues

**Step 1: Get OAuth URL**
```bash
./test_auth_curl.sh oauth_init
# Returns Google OAuth URL
```

**Step 2: Complete OAuth in browser**
1. Open the OAuth URL in your browser
2. Complete Google login
3. Copy the `code` parameter from the callback URL

**Step 3: Test callback**
```bash
./test_auth_curl.sh oauth_callback "YOUR_AUTH_CODE_HERE"
```

**Advantages:**
- ✅ Tests real Google integration
- ✅ Validates complete OAuth flow
- ✅ Catches integration issues

### Approach 3: Python Async Testing
**Best for:** Complex testing scenarios, debugging

```bash
# Mock testing (recommended for development)
uv run scripts/test_oauth.py mock

# Manual testing (requires browser interaction)
uv run scripts/test_oauth.py manual
```

**Advantages:**
- ✅ Async HTTP client simulation
- ✅ Comprehensive error handling
- ✅ Structured output
- ✅ Easy to extend

## 🌐 Server Requirements

**Start the development server:**
```bash
uv run hypercorn workout_api.core.main:app --reload --bind 0.0.0.0:8080
```

**Verify server is running:**
```bash
curl http://localhost:8080/docs  # Should return OpenAPI docs
```

## 🧪 Example Testing Workflows

### Development Workflow
```bash
# 1. Start server
uv run hypercorn workout_api.core.main:app --reload --bind 0.0.0.0:8080

# 2. Test auth system
./test_auth_curl.sh all

# 3. Create token for manual testing
ACCESS_TOKEN=$(./test_auth_curl.sh create_tokens | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

# 4. Test protected endpoints
curl -H "Authorization: Bearer $ACCESS_TOKEN" http://localhost:8080/api/v1/auth/validate
```

### CI/CD Testing
```bash
# Fast automated testing (no browser)
uv run scripts/test_oauth.py mock
```

### Manual Integration Testing
```bash
# Full OAuth flow testing
uv run scripts/test_oauth.py manual
```

## 🐛 Troubleshooting

### Common Issues

**1. "Connection refused" errors**
```bash
# Make sure server is running
curl http://localhost:8080/api/v1/health/  # Should return 200
```

**2. "Invalid token" errors**
```bash
# Tokens expire - create fresh ones
./test_auth_curl.sh create_tokens
```

**3. OAuth callback fails**
```bash
# Check your .env file has correct Google OAuth settings
grep GOOGLE_ .env

# Verify callback URL matches Google Console settings
```

**4. JSON parsing errors**
```bash
# Install jq for JSON formatting
brew install jq  # macOS
apt-get install jq  # Ubuntu
```

**5. Google Discovery Document 404 Errors**
If you see errors like:
```
Failed to generate authorization redirect: Client error '404 Not Found' for url 'https://accounts.google.com/.well-known/openid_configuration'
```

**Root Cause**: Google's OpenID Connect discovery endpoint returns 404 when accessed by Python HTTP libraries (httpx, requests) but works fine with curl. This is a known compatibility issue.

**Solution**: Our backend now uses explicit OAuth endpoint URLs instead of discovery. The `AuthlibGoogleManager` is configured with hardcoded endpoints:
- Authorization: `https://accounts.google.com/o/oauth2/v2/auth`
- Token: `https://oauth2.googleapis.com/token`
- UserInfo: `https://openidconnect.googleapis.com/v1/userinfo`

This eliminates the need for discovery document fetching and ensures reliable OAuth functionality.

### Debug Mode

**Enable verbose curl output:**
```bash
# Add -v to curl commands for detailed output
curl -v -H "Authorization: Bearer $TOKEN" http://localhost:8080/api/v1/auth/validate
```

**Check server logs:**
```bash
# Server logs will show detailed error information
uv run hypercorn workout_api.core.main:app --reload --bind 0.0.0.0:8080 --access-log
```

## 🔐 Security Notes

1. **Test tokens are for development only**
   - Don't use in production
   - Tokens have user_id=999 (non-existent user)

2. **Real OAuth codes expire quickly**
   - Use OAuth codes immediately after getting them
   - Codes are single-use only

3. **Environment variables**
   - Keep your `.env` file secure
   - Never commit real OAuth credentials

## 📚 Additional Resources

- **API Documentation:** http://localhost:8080/docs
- **Auth Endpoints:** http://localhost:8080/api/v1/auth/
- **Test Coverage:** `uv run pytest tests/auth/ -v`
- **Google OAuth Setup:** [Google Cloud Console](https://console.cloud.google.com/)

## 🤝 Contributing

When adding new auth endpoints, please:

1. **Add tests to existing scripts:**
   ```bash
   # Add new curl test to test_auth_curl.sh
   # Add new Python test to test_oauth.py
   ```

2. **Update this documentation**

3. **Test both mock and real OAuth flows**

4. **Verify error handling scenarios**

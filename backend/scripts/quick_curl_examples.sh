#!/bin/bash

echo "🚀 Quick curl examples for OAuth testing"
echo

# 1. Test OAuth initiation
echo "1. OAuth Initiation:"
echo "curl -I http://localhost:8080/api/v1/auth/google"
echo

# 2. Create test token
echo "2. Create test token (run this first):"
echo 'ACCESS_TOKEN=$(uv run python -c "
from workout_api.auth.jwt import JWTManager
from workout_api.core.config import get_settings
jwt_manager = JWTManager(get_settings())
print(jwt_manager.create_access_token(999, \"test@example.com\"))
")'
echo

# 3. Test token validation
echo "3. Test token validation:"
echo 'curl -H "Authorization: Bearer $ACCESS_TOKEN" http://localhost:8080/api/v1/auth/validate'
echo

# 4. Test OAuth callback (requires real auth code)
echo "4. Test OAuth callback:"
echo "curl 'http://localhost:8080/api/v1/auth/google/callback?code=YOUR_CODE&state=test'"
echo

# 5. Test token refresh
echo "5. Test token refresh:"
echo 'curl -X POST -H "Content-Type: application/json" \'
echo '     -d "{\"refresh_token\": \"YOUR_REFRESH_TOKEN\"}" \'
echo '     http://localhost:8080/api/v1/auth/refresh'

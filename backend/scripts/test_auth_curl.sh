#!/bin/bash

# OAuth Authentication Testing with curl
# This script provides command-line testing for auth endpoints

set -e

BASE_URL="http://localhost:8080/api/v1"
TEMP_FILE="/tmp/workout_auth_test.json"

echo "🚀 OAuth Authentication Testing with curl"
echo "=========================================="

# Function to test OAuth initiation
test_oauth_initiation() {
    echo "🔍 Testing OAuth initiation..."

    response=$(curl -s -w "%{http_code}" "$BASE_URL/auth/google")
    status_code=${response: -3}

    if [ "$status_code" = "302" ]; then
        echo "✅ OAuth initiation successful! (Status: $status_code)"
        # For redirects, we need to use -I to get headers
        redirect_url=$(curl -s -I "$BASE_URL/auth/google" 2>/dev/null | grep -i location | cut -d' ' -f2- | tr -d '\r')
        echo "📍 Redirect URL: $redirect_url"
    elif [ "$status_code" = "500" ]; then
        echo "⚠️  OAuth initiation endpoint accessible but configuration may be missing (Status: $status_code)"
        body=${response%???}
        echo "$body" | jq . 2>/dev/null || echo "$body"
    else
        echo "❌ OAuth initiation failed! (Status: $status_code)"
        body=${response%???}
        echo "$body" | jq . 2>/dev/null || echo "$body"
    fi
}

# Function to create test JWT tokens
create_test_tokens() {
    echo "🔍 Creating test JWT tokens..."

    # Use Python to create tokens
    tokens=$(uv run python -c "
from workout_api.auth.jwt import JWTManager
from workout_api.core.config import get_settings
import json

settings = get_settings()
jwt_manager = JWTManager(settings)

access_token = jwt_manager.create_access_token(user_id=999, email='test-cli@example.com')
refresh_token = jwt_manager.create_refresh_token(user_id=999, email='test-cli@example.com')

print(json.dumps({
    'access_token': access_token,
    'refresh_token': refresh_token
}))
" 2>/dev/null)

    echo "$tokens" > "$TEMP_FILE"
    echo "✅ Test tokens created and saved to $TEMP_FILE"
}

# Function to test token validation
test_token_validation() {
    echo "🔍 Testing token validation..."

    if [ ! -f "$TEMP_FILE" ]; then
        echo "❌ No tokens found. Run 'create_test_tokens' first."
        return 1
    fi

    access_token=$(jq -r '.access_token' "$TEMP_FILE")

    response=$(curl -s -w "%{http_code}" \
        -H "Authorization: Bearer $access_token" \
        "$BASE_URL/auth/validate")

    status_code=${response: -3}
    body=${response%???}

    if [ "$status_code" = "200" ]; then
        echo "✅ Token validation successful!"
        echo "$body" | jq . 2>/dev/null || echo "$body"
    else
        echo "❌ Token validation failed! (Status: $status_code)"
        echo "$body"
    fi
}

# Function to test token refresh
test_token_refresh() {
    echo "🔍 Testing token refresh..."

    if [ ! -f "$TEMP_FILE" ]; then
        echo "❌ No tokens found. Run 'create_test_tokens' first."
        return 1
    fi

    refresh_token=$(jq -r '.refresh_token' "$TEMP_FILE")

    response=$(curl -s -w "%{http_code}" \
        -X POST \
        -H "Content-Type: application/json" \
        -d "{\"refresh_token\": \"$refresh_token\"}" \
        "$BASE_URL/auth/refresh")

    status_code=${response: -3}
    body=${response%???}

    if [ "$status_code" = "200" ]; then
        echo "✅ Token refresh successful!"
        echo "$body" | jq . 2>/dev/null || echo "$body"
    else
        echo "❌ Token refresh failed! (Status: $status_code)"
        echo "$body"
    fi
}

# Function to test session info
test_session_info() {
    echo "🔍 Testing session info..."

    if [ ! -f "$TEMP_FILE" ]; then
        echo "❌ No tokens found. Run 'create_test_tokens' first."
        return 1
    fi

    access_token=$(jq -r '.access_token' "$TEMP_FILE")

    response=$(curl -s -w "%{http_code}" \
        -H "Authorization: Bearer $access_token" \
        "$BASE_URL/auth/me")

    status_code=${response: -3}
    body=${response%???}

    if [ "$status_code" = "200" ]; then
        echo "✅ Session info successful!"
        echo "$body" | jq . 2>/dev/null || echo "$body"
    else
        echo "❌ Session info failed! (Status: $status_code)"
        echo "$body"
    fi
}

# Function to simulate OAuth callback
test_oauth_callback() {
    local auth_code="$1"
    local state="${2:-test_state}"

    if [ -z "$auth_code" ]; then
        echo "❌ Authorization code required"
        echo "Usage: test_oauth_callback <auth_code> [state]"
        return 1
    fi

    echo "🔍 Testing OAuth callback with code: ${auth_code:0:20}..."

    response=$(curl -s -w "%{http_code}" \
        "$BASE_URL/auth/google/callback?code=$auth_code&state=$state")

    status_code=${response: -3}
    body=${response%???}

    if [ "$status_code" = "200" ]; then
        echo "✅ OAuth callback successful!"
        echo "$body" | jq . 2>/dev/null > "$TEMP_FILE"
        echo "Tokens saved to $TEMP_FILE"
    else
        echo "❌ OAuth callback failed! (Status: $status_code)"
        echo "$body"
    fi
}

# Function to run all tests
run_all_tests() {
    echo "🚀 Running all authentication tests..."
    echo

    test_oauth_initiation
    echo

    create_test_tokens
    echo

    test_token_validation
    echo

    test_token_refresh
    echo

    test_session_info
    echo

    echo "✅ All tests completed!"
}

# Function to show usage
show_usage() {
    echo "OAuth Authentication Testing Script"
    echo
    echo "Usage: $0 [command] [args...]"
    echo
    echo "Commands:"
    echo "  oauth_init              Test OAuth initiation endpoint"
    echo "  create_tokens           Create test JWT tokens"
    echo "  validate_token          Test token validation"
    echo "  refresh_token           Test token refresh"
    echo "  session_info            Test session info endpoint"
    echo "  oauth_callback <code>   Test OAuth callback with auth code"
    echo "  all                     Run all tests"
    echo "  help                    Show this help"
    echo
    echo "Examples:"
    echo "  $0 all                                    # Run all tests"
    echo "  $0 create_tokens                          # Create test tokens"
    echo "  $0 oauth_callback 4/0AdQt8qh...           # Test with real auth code"
}

# Main script logic
case "${1:-all}" in
    oauth_init)
        test_oauth_initiation
        ;;
    create_tokens)
        create_test_tokens
        ;;
    validate_token)
        test_token_validation
        ;;
    refresh_token)
        test_token_refresh
        ;;
    session_info)
        test_session_info
        ;;
    oauth_callback)
        test_oauth_callback "$2" "$3"
        ;;
    all)
        run_all_tests
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo
        show_usage
        exit 1
        ;;
esac

# Cleanup
if [ -f "$TEMP_FILE" ] && [ "${1:-all}" = "all" ]; then
    echo "🧹 Cleaning up temporary files..."
    rm -f "$TEMP_FILE"
fi

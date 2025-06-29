#!/usr/bin/env python3
"""
OAuth Flow Testing Script

This script provides multiple ways to test the OAuth authentication flow:
1. Mock OAuth flow simulation
2. Real OAuth flow with manual callback handling
3. Token validation testing
"""

import asyncio
import json
import sys

import httpx

from workout_api.auth.jwt import JWTManager
from workout_api.core.config import get_settings


class OAuthTester:
    def __init__(self):
        self.settings = get_settings()
        self.base_url = "http://localhost:8080/api/v1"
        self.client = httpx.AsyncClient(timeout=30.0)

    async def test_oauth_initiation(self):
        """Test OAuth initiation endpoint"""
        print("🔍 Testing OAuth initiation...")

        response = await self.client.get(f"{self.base_url}/auth/google")

        if response.status_code == 302:
            redirect_url = response.headers.get("location")
            print("✅ OAuth initiation successful!")
            print(f"📍 Redirect URL: {redirect_url}")
            return redirect_url
        elif response.status_code == 500:
            print(
                f"⚠️  OAuth initiation endpoint accessible but configuration may be missing: {response.status_code}"
            )
            print(f"Response: {response.text}")
            return None
        else:
            print(f"❌ OAuth initiation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None

    async def test_token_endpoints(self, access_token: str, refresh_token: str):
        """Test token validation and refresh endpoints"""
        print("\n🔍 Testing token endpoints...")

        # Test token validation
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await self.client.get(
            f"{self.base_url}/auth/validate", headers=headers
        )

        if response.status_code == 200:
            print("✅ Token validation successful!")
            print(f"Token info: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"❌ Token validation failed: {response.status_code}")

        # Test token refresh
        response = await self.client.post(
            f"{self.base_url}/auth/refresh", json={"refresh_token": refresh_token}
        )

        if response.status_code == 200:
            print("✅ Token refresh successful!")
            new_token = response.json()
            print(f"New access token: {new_token['access_token'][:50]}...")
        else:
            print(f"❌ Token refresh failed: {response.status_code}")

    async def simulate_oauth_callback(self, auth_code: str, state: str = "test_state"):
        """Simulate OAuth callback with auth code"""
        print(f"\n🔍 Simulating OAuth callback with code: {auth_code[:20]}...")

        response = await self.client.get(
            f"{self.base_url}/auth/google/callback",
            params={"code": auth_code, "state": state},
        )

        if response.status_code == 200:
            print("✅ OAuth callback successful!")
            data = response.json()
            print(f"User: {data['user']['email_address']}")
            return data["tokens"]
        else:
            print(f"❌ OAuth callback failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None

    def create_test_tokens(self):
        """Create test JWT tokens for testing"""
        print("\n🔍 Creating test tokens...")

        jwt_manager = JWTManager(self.settings)

        # Create tokens for a test user
        access_token = jwt_manager.create_access_token(
            user_id=999, email="test-cli@example.com"
        )
        refresh_token = jwt_manager.create_refresh_token(
            user_id=999, email="test-cli@example.com"
        )

        print("✅ Test tokens created!")
        print(f"Access Token: {access_token}")
        print(f"Refresh Token: {refresh_token}")

        return access_token, refresh_token

    async def run_mock_test(self):
        """Run mock OAuth test"""
        print("🚀 Running Mock OAuth Test\n")

        # Test OAuth initiation
        redirect_url = await self.test_oauth_initiation()

        if not redirect_url:
            return

        # Create test tokens
        access_token, refresh_token = self.create_test_tokens()

        # Test token endpoints
        await self.test_token_endpoints(access_token, refresh_token)

        print("\n✅ Mock OAuth test completed!")

    async def run_manual_test(self):
        """Run manual OAuth test with real Google"""
        print("🚀 Running Manual OAuth Test\n")
        print("This will require manual intervention...")

        # Get OAuth initiation URL
        redirect_url = await self.test_oauth_initiation()

        if not redirect_url:
            return

        print("\n📋 Manual Steps:")
        print("1. Open this URL in your browser:")
        print(f"   {redirect_url}")
        print("2. Complete Google OAuth flow")
        print("3. Copy the 'code' parameter from the callback URL")
        print("4. Paste it below")

        try:
            auth_code = input("\n🔑 Enter the authorization code: ").strip()

            if auth_code:
                tokens = await self.simulate_oauth_callback(auth_code)
                if tokens:
                    await self.test_token_endpoints(
                        tokens["access_token"], tokens["refresh_token"]
                    )
        except KeyboardInterrupt:
            print("\n❌ Test cancelled by user")

    async def close(self):
        await self.client.aclose()


async def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("OAuth Testing Script")
        print("Usage:")
        print("  python test_oauth.py mock     # Run mock OAuth test")
        print("  python test_oauth.py manual   # Run manual OAuth test")
        print("  python test_oauth.py tokens   # Just create test tokens")
        return

    tester = OAuthTester()

    try:
        mode = sys.argv[1] if len(sys.argv) > 1 else "mock"

        if mode == "mock":
            await tester.run_mock_test()
        elif mode == "manual":
            await tester.run_manual_test()
        elif mode == "tokens":
            tester.create_test_tokens()
        else:
            print(f"❌ Unknown mode: {mode}")
            print("Use 'mock', 'manual', or 'tokens'")

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(main())

import pytest
import jwt
import os
import tempfile
import time
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Import the FastAPI app and dependencies
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from db import get_db
from models import Base

# Load environment variables
load_dotenv()

ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET", "default_access_token_secret")
REFRESH_TOKEN_SECRET = os.getenv("REFRESH_TOKEN_SECRET", "default_refresh_token_secret")


class TestLogoutEndpoint:
    """Test suite for the /logout endpoint"""
    
    @pytest.fixture
    def test_db(self):
        """Create a temporary test database"""
        # Create a temporary database file
        db_fd, db_path = tempfile.mkstemp()
        
        # Create test engine and session
        test_engine = create_engine(f"sqlite:///{db_path}", echo=False)
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
        
        # Create all tables
        Base.metadata.create_all(bind=test_engine)
        
        # Override the get_db dependency
        def override_get_db():
            try:
                db = TestingSessionLocal()
                yield db
            finally:
                db.close()
        
        app.dependency_overrides[get_db] = override_get_db
        
        yield TestingSessionLocal
        
        # Cleanup
        os.close(db_fd)
        os.unlink(db_path)
        app.dependency_overrides.clear()

    @pytest.fixture
    def client(self, test_db):
        """Create a test client"""
        return TestClient(app)

    @pytest.fixture
    def authenticated_user(self, client):
        """Create and authenticate a test user, return the response with cookies"""
        # Register a test user
        register_response = client.post(
            "/register",
            json={"user": "testlogoutuser", "pwd": "testpassword"}
        )
        assert register_response.status_code in [200, 409]  # 409 if user already exists
        
        # Login to get tokens
        login_response = client.post(
            "/auth",
            json={"user": "testlogoutuser", "pwd": "testpassword"}
        )
        assert login_response.status_code == 200
        assert "jwt" in login_response.cookies
        
        return login_response

    def test_logout_success(self, client, authenticated_user):
        """Test successful logout with valid refresh token"""
        # Use the authenticated user's cookies
        cookies = authenticated_user.cookies
        
        # Make logout request with the JWT cookie
        logout_response = client.post("/logout", cookies=cookies)
        
        # Should return 204 No Content on successful logout
        assert logout_response.status_code == 204
        
        # Verify the JWT cookie is cleared
        if "jwt" in logout_response.cookies:
            # Cookie should be cleared (empty value)
            jwt_cookie = logout_response.cookies["jwt"]
            assert jwt_cookie == ""

    def test_logout_no_cookie(self, client):
        """Test logout when no JWT cookie is present"""
        # Make logout request without any cookies
        logout_response = client.post("/logout")
        
        # Should return 204 No Content even when no cookie is present
        assert logout_response.status_code == 204

    def test_logout_invalid_token(self, client):
        """Test logout with invalid/non-existent refresh token"""
        # Make logout request with invalid token
        logout_response = client.post("/logout", cookies={"jwt": "invalid_token_12345"})
        
        # Should return 204 No Content even with invalid token
        assert logout_response.status_code == 204
        
        # Verify the JWT cookie is cleared
        if "jwt" in logout_response.cookies:
            jwt_cookie = logout_response.cookies["jwt"]
            assert jwt_cookie == ""

    def test_logout_expired_token(self, client):
        """Test logout with an expired but valid refresh token"""
        # Create an expired token manually
        expired_payload = {
            "username": "expireduser",
            "iat": int(time.time()) - 3600,  # 1 hour ago
            "exp": int(time.time()) - 1800   # 30 minutes ago (expired)
        }
        
        expired_token = jwt.encode(
            expired_payload,
            REFRESH_TOKEN_SECRET,
            algorithm="HS256"
        )
        
        # Make logout request with expired token
        logout_response = client.post("/logout", cookies={"jwt": expired_token})
        
        # Should return 204 No Content even with expired token
        assert logout_response.status_code == 204
        
        # Verify the JWT cookie is cleared
        if "jwt" in logout_response.cookies:
            jwt_cookie = logout_response.cookies["jwt"]
            assert jwt_cookie == ""

    def test_logout_clears_refresh_token_from_db(self, client, authenticated_user):
        """Test that logout properly clears refresh token from database"""
        # Get the refresh token from login
        cookies = authenticated_user.cookies
        refresh_token = cookies["jwt"]
        
        # Perform logout
        logout_response = client.post("/logout", cookies=cookies)
        assert logout_response.status_code == 204
        
        # Try to use the refresh endpoint with the same refresh token
        # This should fail because the token was cleared from the database
        refresh_response = client.post("/refresh", cookies=cookies)
        
        # Should fail because refresh token was cleared from database
        # The exact status code depends on implementation, but should not be successful
        assert refresh_response.status_code in [401, 403, 204]

    def test_logout_multiple_times(self, client, authenticated_user):
        """Test that multiple logout calls don't cause errors"""
        cookies = authenticated_user.cookies
        
        # First logout
        logout_response1 = client.post("/logout", cookies=cookies)
        assert logout_response1.status_code == 204
        
        # Second logout (should still work gracefully)
        logout_response2 = client.post("/logout", cookies=cookies)
        assert logout_response2.status_code == 204

    def test_logout_with_empty_jwt_cookie(self, client):
        """Test logout with empty JWT cookie value"""
        # Make logout request with empty JWT cookie
        logout_response = client.post("/logout", cookies={"jwt": ""})
        
        # Should return 204 No Content
        assert logout_response.status_code == 204

    def test_refresh_fails_after_logout(self, client, authenticated_user):
        """Test that refresh endpoint fails after logout"""
        cookies = authenticated_user.cookies
        
        # Perform logout
        logout_response = client.post("/logout", cookies=cookies)
        assert logout_response.status_code == 204
        
        # Try to use refresh endpoint with the same cookies
        refresh_response = client.post("/refresh", cookies=cookies)
        
        # Should fail because refresh token was cleared from database
        # The exact status code depends on implementation (401, 403, or 204)
        assert refresh_response.status_code in [401, 403, 204]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

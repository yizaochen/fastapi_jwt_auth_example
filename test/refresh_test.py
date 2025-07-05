import pytest
import jwt
import os
import tempfile
from datetime import datetime, timedelta, timezone
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


class TestRefreshEndpoint:
    """Test suite for the /refresh endpoint"""
    
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

    def setup_method(self):
        """Clear any persistent state before each test"""
        pass

    @pytest.fixture
    def authenticated_user(self, client):
        """Create an authenticated user and return the refresh token"""
        # Register a test user
        register_response = client.post(
            "/register",
            json={"user": "refreshtest", "pwd": "testpassword"}
        )
        assert register_response.status_code in [200, 409]
        
        # Login to get tokens
        login_response = client.post(
            "/auth",
            json={"user": "refreshtest", "pwd": "testpassword"}
        )
        assert login_response.status_code == 200
        
        # Extract refresh token from cookies
        refresh_token = login_response.cookies.get("jwt")
        return refresh_token

    def test_refresh_success(self, client, authenticated_user):
        """Test successful refresh token usage"""
        refresh_token = authenticated_user
        
        # Set cookies on client instance to avoid deprecation warning
        client.cookies.set("jwt", refresh_token)
        
        # Make refresh request with valid refresh token
        response = client.post("/refresh")
        
        assert response.status_code == 200
        response_data = response.json()
        
        # Validate response structure
        assert "accessToken" in response_data
        assert "roles" in response_data
        assert isinstance(response_data["roles"], list)
        
        # Validate new access token
        access_token = response_data["accessToken"]
        decoded_token = jwt.decode(
            access_token, 
            ACCESS_TOKEN_SECRET, 
            algorithms=["HS256"]
        )
        
        # Validate token structure
        assert "UserInfo" in decoded_token
        assert "username" in decoded_token["UserInfo"]
        assert "roles" in decoded_token["UserInfo"]
        assert "exp" in decoded_token
        assert "iat" in decoded_token
        assert decoded_token["UserInfo"]["username"] == "refreshtest"

    def test_refresh_no_cookie(self, client):
        """Test refresh request without JWT cookie"""
        client.cookies.clear()  # Ensure no cookies are set
        response = client.post("/refresh")
        
        assert response.status_code == 401

    def test_refresh_empty_cookie(self, client):
        """Test refresh request with empty JWT cookie"""
        client.cookies.clear()
        client.cookies.set("jwt", "")
        response = client.post("/refresh")
        
        assert response.status_code == 401

    def test_refresh_invalid_token(self, client):
        """Test refresh request with invalid token"""
        client.cookies.set("jwt", "invalid.token.here")
        response = client.post("/refresh")
        
        assert response.status_code == 403

    def test_refresh_expired_token(self, client, authenticated_user):
        """Test refresh request with expired token"""
        # Create an expired refresh token
        now = datetime.now(timezone.utc)
        expired_token = jwt.encode(
            {
                "username": "refreshtest",
                "exp": now - timedelta(hours=1),  # Expired 1 hour ago
                "iat": now - timedelta(hours=2)
            },
            REFRESH_TOKEN_SECRET,
            algorithm="HS256"
        )
        
        client.cookies.set("jwt", expired_token)
        response = client.post("/refresh")
        
        assert response.status_code == 403

    def test_refresh_token_not_in_database(self, client):
        """Test refresh request with valid JWT but not stored in database"""
        # Create a valid JWT but not associated with any user in DB
        now = datetime.now(timezone.utc)
        fake_token = jwt.encode(
            {
                "username": "nonexistentuser",
                "exp": now + timedelta(days=1),
                "iat": now
            },
            REFRESH_TOKEN_SECRET,
            algorithm="HS256"
        )
        
        client.cookies.set("jwt", fake_token)
        response = client.post("/refresh")
        
        assert response.status_code == 403

    def test_refresh_username_mismatch(self, client, test_db):
        """Test refresh request where token username doesn't match database user"""
        # First, create a user and get their refresh token
        client.post("/register", json={"user": "user1", "pwd": "password"})
        login_response = client.post("/auth", json={"user": "user1", "pwd": "password"})
        
        # Get the refresh token from database
        db_session = test_db()
        from models import User
        user = db_session.query(User).filter(User.username == "user1").first()
        stored_refresh_token = user.refresh_token
        db_session.close()
        
        # Decode the token and create a new one with different username
        decoded = jwt.decode(stored_refresh_token, REFRESH_TOKEN_SECRET, algorithms=["HS256"])
        
        # Create a token with different username but same token value in DB
        malicious_token = jwt.encode(
            {
                "username": "differentuser",  # Different username
                "exp": decoded["exp"],
                "iat": decoded["iat"]
            },
            REFRESH_TOKEN_SECRET,
            algorithm="HS256"
        )
        
        # Update the user's refresh token to the malicious one
        db_session = test_db()
        user = db_session.query(User).filter(User.username == "user1").first()
        user.refresh_token = malicious_token
        db_session.commit()
        db_session.close()
        
        client.cookies.set("jwt", malicious_token)
        response = client.post("/refresh")
        
        assert response.status_code == 403

    def test_refresh_malformed_token(self, client):
        """Test refresh request with malformed JWT"""
        client.cookies.set("jwt", "this.is.not.a.valid.jwt")
        response = client.post("/refresh")
        
        assert response.status_code == 403

    def test_refresh_token_wrong_secret(self, client):
        """Test refresh request with token signed with wrong secret"""
        now = datetime.now(timezone.utc)
        wrong_secret_token = jwt.encode(
            {
                "username": "refreshtest",
                "exp": now + timedelta(days=1),
                "iat": now
            },
            "wrong_secret",  # Wrong secret
            algorithm="HS256"
        )
        
        client.cookies.set("jwt", wrong_secret_token)
        response = client.post("/refresh")
        
        assert response.status_code == 403

    def test_refresh_multiple_requests(self, client, authenticated_user):
        """Test multiple refresh requests with same token"""
        refresh_token = authenticated_user
        
        # Set the refresh token cookie on the client
        client.cookies.set("jwt", refresh_token)
        
        # First refresh should work
        response1 = client.post("/refresh")
        assert response1.status_code == 200
        
        # Second refresh with same token should also work
        # (since the refresh token doesn't get invalidated on use)
        response2 = client.post("/refresh")
        assert response2.status_code == 200
        
        # Both should return valid access tokens
        token1 = response1.json()["accessToken"]
        token2 = response2.json()["accessToken"]
        
        # Both tokens should be valid (though different due to different iat)
        decoded1 = jwt.decode(token1, ACCESS_TOKEN_SECRET, algorithms=["HS256"])
        decoded2 = jwt.decode(token2, ACCESS_TOKEN_SECRET, algorithms=["HS256"])
        
        assert decoded1["UserInfo"]["username"] == "refreshtest"
        assert decoded2["UserInfo"]["username"] == "refreshtest"

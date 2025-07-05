import pytest
import jwt
import os
import tempfile
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


class TestAuthEndpoint:
    """Test suite for the /auth endpoint"""
    
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

    def test_login_success(self, client):
        """Test successful login with valid credentials"""
        # First, ensure the test user exists by registering
        register_response = client.post(
            "/register",
            json={"user": "testuser", "pwd": "testpassword"}
        )
        
        # Should succeed (200) or user already exists (409)
        assert register_response.status_code in [200, 409]
        
        # Now test the login
        login_response = client.post(
            "/auth",
            json={"user": "testuser", "pwd": "testpassword"}
        )
        
        assert login_response.status_code == 200
        response_data = login_response.json()
        
        # Validate response structure
        assert "accessToken" in response_data
        assert "roles" in response_data
        assert isinstance(response_data["roles"], list)
        
        # Validate JWT token
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
        assert decoded_token["UserInfo"]["username"] == "testuser"
        
        # Check for refresh token cookie
        cookies = login_response.cookies
        assert "jwt" in cookies
        
        refresh_token = cookies["jwt"]
        decoded_refresh = jwt.decode(
            refresh_token,
            REFRESH_TOKEN_SECRET,
            algorithms=["HS256"]
        )
        
        # Validate refresh token structure
        assert "username" in decoded_refresh
        assert "exp" in decoded_refresh
        assert "iat" in decoded_refresh
        assert decoded_refresh["username"] == "testuser"

    def test_login_invalid_username(self, client):
        """Test login with invalid username"""
        response = client.post(
            "/auth",
            json={"user": "nonexistentuser", "pwd": "somepassword"}
        )
        
        assert response.status_code == 401
        response_data = response.json()
        assert "detail" in response_data
        assert response_data["detail"] == "Invalid username or password"

    def test_login_invalid_password(self, client):
        """Test login with valid username but invalid password"""
        # First ensure test user exists
        register_response = client.post(
            "/register",
            json={"user": "testuser2", "pwd": "correctpassword"}
        )
        assert register_response.status_code in [200, 409]
        
        # Now test with wrong password
        response = client.post(
            "/auth",
            json={"user": "testuser2", "pwd": "wrongpassword"}
        )
        
        assert response.status_code == 401
        response_data = response.json()
        assert "detail" in response_data
        assert response_data["detail"] == "Invalid username or password"

    def test_login_missing_credentials(self, client):
        """Test login with missing username or password"""
        # Test missing username
        response1 = client.post(
            "/auth",
            json={"user": "", "pwd": "password"}
        )
        
        assert response1.status_code == 400
        response_data1 = response1.json()
        assert "detail" in response_data1
        assert response_data1["detail"] == "Username and password are required."
        
        # Test missing password
        response2 = client.post(
            "/auth",
            json={"user": "username", "pwd": ""}
        )
        
        assert response2.status_code == 400
        response_data2 = response2.json()
        assert "detail" in response_data2
        assert response_data2["detail"] == "Username and password are required."
        
        # Test missing both
        response3 = client.post(
            "/auth",
            json={"user": "", "pwd": ""}
        )
        
        assert response3.status_code == 400

    def test_login_malformed_request(self, client):
        """Test login with malformed JSON request"""
        # Test with wrong field names
        response = client.post(
            "/auth",
            json={"username": "testuser", "password": "testpassword"}  # Wrong field names
        )
        
        # Should return 422 for validation error
        assert response.status_code == 422

    def test_cookie_attributes(self, client):
        """Test that login sets cookies with correct attributes"""
        # Ensure test user exists
        client.post("/register", json={"user": "cookietest", "pwd": "testpass"})
        
        # Login to get cookie
        response = client.post(
            "/auth",
            json={"user": "cookietest", "pwd": "testpass"}
        )
        
        assert response.status_code == 200
        
        # Check cookie attributes
        cookies = response.cookies
        assert "jwt" in cookies
        
        # Check the Set-Cookie header for attributes
        set_cookie_header = response.headers.get("set-cookie", "")
        
        # Check for HttpOnly attribute
        assert "HttpOnly" in set_cookie_header
        
        # Check for Max-Age
        assert "Max-Age" in set_cookie_header

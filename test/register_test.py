import pytest
import os
import tempfile
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch

# Import the FastAPI app and dependencies
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from db import get_db
from models import Base, User


class TestRegisterEndpoint:
    """Test suite for the /register endpoint"""
    
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

    def test_register_success(self, client):
        """Test successful user registration"""
        response = client.post(
            "/register",
            json={"user": "testuser1", "pwd": "testpassword1"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "testuser1" in data["success"]
        assert "created" in data["success"]

    def test_register_missing_username(self, client):
        """Test registration with missing username"""
        response = client.post(
            "/register",
            json={"pwd": "testpassword1"}
        )
        
        assert response.status_code == 422  # Pydantic validation error

    def test_register_missing_password(self, client):
        """Test registration with missing password"""
        response = client.post(
            "/register",
            json={"user": "testuser1"}
        )
        
        assert response.status_code == 422  # Pydantic validation error

    def test_register_empty_username(self, client):
        """Test registration with empty username"""
        response = client.post(
            "/register",
            json={"user": "", "pwd": "testpassword1"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Username and password are required" in data["detail"]

    def test_register_empty_password(self, client):
        """Test registration with empty password"""
        response = client.post(
            "/register",
            json={"user": "testuser1", "pwd": ""}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Username and password are required" in data["detail"]

    def test_register_both_empty(self, client):
        """Test registration with both username and password empty"""
        response = client.post(
            "/register",
            json={"user": "", "pwd": ""}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Username and password are required" in data["detail"]

    def test_register_duplicate_username(self, client):
        """Test registration with duplicate username"""
        # First registration should succeed
        response1 = client.post(
            "/register",
            json={"user": "testuser1", "pwd": "testpassword1"}
        )
        assert response1.status_code == 200
        
        # Second registration with same username should fail
        response2 = client.post(
            "/register",
            json={"user": "testuser1", "pwd": "testpassword2"}
        )
        assert response2.status_code == 409
        data = response2.json()
        assert "Username already exists" in data["detail"]


    def test_register_multiple_users(self, client):
        """Test registering multiple different users"""
        users = [
            {"user": "user1", "pwd": "password1"},
            {"user": "user2", "pwd": "password2"},
            {"user": "user3", "pwd": "password3"}
        ]
        
        for user_data in users:
            response = client.post("/register", json=user_data)
            assert response.status_code == 200
            data = response.json()
            assert user_data["user"] in data["success"]

    def test_register_invalid_json(self, client):
        """Test registration with invalid JSON"""
        response = client.post(
            "/register",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422

    def test_register_wrong_field_names(self, client):
        """Test registration with wrong field names"""
        response = client.post(
            "/register",
            json={"username": "testuser1", "password": "testpassword1"}  # Wrong field names
        )
        
        assert response.status_code == 422  # Pydantic validation error

    def test_register_password_hashing(self, client, test_db):
        """Test that passwords are properly hashed in the database"""
        password = "testpassword123"
        username = "testuser1"
        
        # Register a user
        response = client.post(
            "/register",
            json={"user": username, "pwd": password}
        )
        assert response.status_code == 200
        
        # Check that password is hashed in database
        db = test_db()
        user = db.query(User).filter(User.username == username).first()
        db.close()
        
        assert user is not None
        assert user.password != password  # Password should be hashed, not plain text
        assert user.password.startswith("$2b$")  # bcrypt hash starts with $2b$
        assert len(user.password) == 60  # bcrypt hash is 60 characters long
        
        # Verify we can check the password with bcrypt
        import bcrypt
        assert bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8'))

    def test_register_default_roles(self, client, test_db):
        """Test that new users get default roles assigned"""
        response = client.post(
            "/register",
            json={"user": "testuser1", "pwd": "testpassword1"}
        )
        assert response.status_code == 200
        
        # Check user roles in database
        db = test_db()
        user = db.query(User).filter(User.username == "testuser1").first()
        db.close()
        
        assert user is not None
        assert user.roles == "2001"  # Default role from models.py


if __name__ == "__main__":
    # Simple runner for quick testing
    pytest.main([__file__, "-v"])

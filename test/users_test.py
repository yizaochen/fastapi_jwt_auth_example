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
from models import Base, User
from routes.auth_utils import ROLES

# Load environment variables
load_dotenv()

ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET", "default_access_token_secret")


class TestUsersEndpoints:
    """Test suite for the /users endpoints"""
    
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
    def admin_token(self):
        """Create a valid admin token for testing"""
        payload = {
            "UserInfo": {
                "username": "admin",
                "roles": [ROLES["Admin"]]
            }
        }
        return jwt.encode(payload, ACCESS_TOKEN_SECRET, algorithm="HS256")

    @pytest.fixture
    def user_token(self):
        """Create a valid user token for testing (no admin privileges)"""
        payload = {
            "UserInfo": {
                "username": "regular_user",
                "roles": [ROLES["User"]]
            }
        }
        return jwt.encode(payload, ACCESS_TOKEN_SECRET, algorithm="HS256")

    @pytest.fixture
    def sample_users(self, test_db):
        """Create sample users in the database"""
        db = test_db()
        
        # Create test users with roles as comma-separated strings
        from models import deserialize_roles
        user1 = User(username="testuser1", password="hashedpassword1", roles=deserialize_roles([ROLES["User"]]))
        user2 = User(username="testuser2", password="hashedpassword2", roles=deserialize_roles([ROLES["Editor"]]))
        user3 = User(username="testuser3", password="hashedpassword3", roles=deserialize_roles([ROLES["Admin"]]))
        
        db.add(user1)
        db.add(user2)
        db.add(user3)
        db.commit()
        
        # Return user data for verification
        users = [
            {"id": user1.id, "username": "testuser1", "roles": [ROLES["User"]]},
            {"id": user2.id, "username": "testuser2", "roles": [ROLES["Editor"]]},
            {"id": user3.id, "username": "testuser3", "roles": [ROLES["Admin"]]},
        ]
        
        db.close()
        return users

    def test_get_all_users_success(self, client, admin_token, sample_users):
        """Test successful retrieval of all users with admin token"""
        response = client.get(
            "/users/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        response_data = response.json()
        
        # Should return list of users
        assert isinstance(response_data, list)
        assert len(response_data) == 3
        
        # Verify response format
        for user in response_data:
            assert "id" in user
            assert "username" in user
            assert "roles" in user
            assert isinstance(user["roles"], list)
            
        # Verify specific users are present
        usernames = [user["username"] for user in response_data]
        assert "testuser1" in usernames
        assert "testuser2" in usernames
        assert "testuser3" in usernames

    def test_get_all_users_no_users(self, client, admin_token):
        """Test get all users when no users exist"""
        response = client.get(
            "/users/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 204
        response_data = response.json()
        assert "message" in response_data
        assert response_data["message"] == "No users found"

    def test_get_all_users_no_admin_access(self, client, user_token):
        """Test get all users with non-admin token should fail"""
        response = client.get(
            "/users/",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 403
        response_data = response.json()
        assert "detail" in response_data

    def test_get_all_users_no_token(self, client):
        """Test get all users without authentication token"""
        response = client.get("/users/")
        
        assert response.status_code == 403

    def test_get_user_by_id_success(self, client, admin_token, sample_users):
        """Test successful retrieval of specific user by ID"""
        # Get the first user's ID
        user_id = sample_users[0]["id"]
        
        response = client.get(
            f"/users/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        response_data = response.json()
        
        # Verify response structure
        assert "id" in response_data
        assert "username" in response_data
        assert "roles" in response_data
        
        # Verify correct user data
        assert response_data["id"] == user_id
        assert response_data["username"] == "testuser1"
        assert response_data["roles"] == [ROLES["User"]]

    def test_get_user_by_id_not_found(self, client, admin_token):
        """Test get user by ID when user doesn't exist"""
        response = client.get(
            "/users/99999",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 204
        response_data = response.json()
        assert "message" in response_data
        assert "User ID 99999 not found" in response_data["message"]

    def test_get_user_by_id_no_admin_access(self, client, user_token, sample_users):
        """Test get user by ID with non-admin token should fail"""
        user_id = sample_users[0]["id"]
        
        response = client.get(
            f"/users/{user_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 403

    def test_get_user_by_id_no_token(self, client, sample_users):
        """Test get user by ID without authentication token"""
        user_id = sample_users[0]["id"]
        
        response = client.get(f"/users/{user_id}")
        
        assert response.status_code == 403

    def test_delete_user_success(self, client, admin_token, sample_users):
        """Test successful user deletion with admin token"""
        user_id = sample_users[0]["id"]
        
        response = client.request(
            "DELETE",
            "/users/",
            json={"id": user_id},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        response_data = response.json()
        
        assert "message" in response_data
        assert f"User {user_id} deleted successfully" in response_data["message"]
        
        # Verify user is actually deleted by trying to get it
        get_response = client.get(
            f"/users/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert get_response.status_code == 204

    def test_delete_user_not_found(self, client, admin_token):
        """Test delete user when user doesn't exist"""
        response = client.request(
            "DELETE",
            "/users/",
            json={"id": 99999},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 204
        response_data = response.json()
        assert "message" in response_data
        assert "User ID 99999 not found" in response_data["message"]

    def test_delete_user_missing_id(self, client, admin_token):
        """Test delete user without providing user ID"""
        response = client.request(
            "DELETE",
            "/users/",
            json={},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 422  # Validation error for missing required field

    def test_delete_user_invalid_id(self, client, admin_token):
        """Test delete user with invalid ID format"""
        response = client.request(
            "DELETE",
            "/users/",
            json={"id": "invalid"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 422  # Validation error for invalid type

    def test_delete_user_no_admin_access(self, client, user_token, sample_users):
        """Test delete user with non-admin token should fail"""
        user_id = sample_users[0]["id"]
        
        response = client.request(
            "DELETE",
            "/users/",
            json={"id": user_id},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 403

    def test_delete_user_no_token(self, client, sample_users):
        """Test delete user without authentication token"""
        user_id = sample_users[0]["id"]
        
        response = client.request(
            "DELETE",
            "/users/",
            json={"id": user_id}
        )
        
        assert response.status_code == 403

    def test_malformed_json_requests(self, client, admin_token):
        """Test endpoints with malformed JSON requests"""
        # Test delete with wrong field name
        response = client.request(
            "DELETE",
            "/users/",
            json={"user_id": 1},  # Wrong field name
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 422  # Validation error

    def test_invalid_bearer_token(self, client):
        """Test requests with invalid bearer token"""
        response = client.get(
            "/users/",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 403

    def test_missing_authorization_header(self, client):
        """Test requests without authorization header"""
        response = client.get("/users/")
        assert response.status_code == 403
        
        response = client.get("/users/1")
        assert response.status_code == 403
        
        response = client.request("DELETE", "/users/", json={"id": 1})
        assert response.status_code == 403

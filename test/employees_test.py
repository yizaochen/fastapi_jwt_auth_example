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
from models import Base, Employee
from routes.auth_utils import ROLES

# Load environment variables
load_dotenv()

ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET", "default_access_token_secret")


class TestEmployeesEndpoint:
    """Test suite for the /employees endpoint"""
    
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
    def sample_employee_data(self):
        """Sample employee data for testing"""
        return {
            "firstname": "John",
            "lastname": "Doe"
        }

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
    def editor_token(self):
        """Create a valid editor token for testing"""
        payload = {
            "UserInfo": {
                "username": "editor",
                "roles": [ROLES["Editor"]]
            }
        }
        return jwt.encode(payload, ACCESS_TOKEN_SECRET, algorithm="HS256")

    @pytest.fixture
    def user_token(self):
        """Create a valid user token for testing"""
        payload = {
            "UserInfo": {
                "username": "user",
                "roles": [ROLES["User"]]
            }
        }
        return jwt.encode(payload, ACCESS_TOKEN_SECRET, algorithm="HS256")

    def test_get_all_employees_success(self, client, test_db, user_token, sample_employee_data):
        """Test successful retrieval of all employees"""
        # Create test employee in database
        db = test_db()
        employee = Employee(**sample_employee_data)
        db.add(employee)
        db.commit()
        db.close()
        
        # Test the endpoint
        response = client.get(
            "/employees/",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 200
        response_data = response.json()
        
        # Validate response structure
        assert isinstance(response_data, list)
        assert len(response_data) == 1
        assert response_data[0]["firstname"] == "John"
        assert response_data[0]["lastname"] == "Doe"
        assert "id" in response_data[0]

    def test_get_all_employees_empty_database(self, client, user_token):
        """Test getting employees when database is empty"""
        response = client.get(
            "/employees/",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 204

    def test_get_all_employees_unauthorized(self, client):
        """Test getting employees without authentication"""
        response = client.get("/employees/")
        
        assert response.status_code == 403

    def test_create_employee_admin_success(self, client, admin_token, sample_employee_data):
        """Test successful employee creation with admin role"""
        response = client.post(
            "/employees/",
            json=sample_employee_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 201
        response_data = response.json()
        
        # Validate response structure
        assert response_data["firstname"] == "John"
        assert response_data["lastname"] == "Doe"
        assert "id" in response_data

    def test_create_employee_editor_success(self, client, editor_token, sample_employee_data):
        """Test successful employee creation with editor role"""
        response = client.post(
            "/employees/",
            json=sample_employee_data,
            headers={"Authorization": f"Bearer {editor_token}"}
        )
        
        assert response.status_code == 201
        response_data = response.json()
        
        # Validate response structure
        assert response_data["firstname"] == "John"
        assert response_data["lastname"] == "Doe"
        assert "id" in response_data

    def test_create_employee_user_forbidden(self, client, user_token, sample_employee_data):
        """Test employee creation with insufficient role (user only)"""
        response = client.post(
            "/employees/",
            json=sample_employee_data,
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 403

    def test_create_employee_unauthorized(self, client, sample_employee_data):
        """Test employee creation without authentication"""
        response = client.post(
            "/employees/",
            json=sample_employee_data
        )
        
        assert response.status_code == 403

    def test_create_employee_invalid_data(self, client, admin_token):
        """Test employee creation with invalid data"""
        invalid_data = {"firstname": ""}  # Missing lastname
        
        response = client.post(
            "/employees/",
            json=invalid_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 422

    def test_update_employee_admin_success(self, client, test_db, admin_token, sample_employee_data):
        """Test successful employee update with admin role"""
        # Create test employee in database
        db = test_db()
        employee = Employee(**sample_employee_data)
        db.add(employee)
        db.commit()
        employee_id = employee.id
        db.close()
        
        # Update data
        update_data = {
            "id": employee_id,
            "firstname": "Jane",
            "lastname": "Smith"
        }
        
        response = client.put(
            "/employees/",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        response_data = response.json()
        
        # Validate response
        assert response_data["firstname"] == "Jane"
        assert response_data["lastname"] == "Smith"
        assert response_data["id"] == employee_id

    def test_update_employee_editor_success(self, client, test_db, editor_token, sample_employee_data):
        """Test successful employee update with editor role"""
        # Create test employee in database
        db = test_db()
        employee = Employee(**sample_employee_data)
        db.add(employee)
        db.commit()
        employee_id = employee.id
        db.close()
        
        # Partial update data
        update_data = {
            "id": employee_id,
            "firstname": "Jane"
        }
        
        response = client.put(
            "/employees/",
            json=update_data,
            headers={"Authorization": f"Bearer {editor_token}"}
        )
        
        assert response.status_code == 200
        response_data = response.json()
        
        # Validate response
        assert response_data["firstname"] == "Jane"
        assert response_data["lastname"] == "Doe"  # Should remain unchanged

    def test_update_employee_user_forbidden(self, client, test_db, user_token, sample_employee_data):
        """Test employee update with insufficient role"""
        # Create test employee in database
        db = test_db()
        employee = Employee(**sample_employee_data)
        db.add(employee)
        db.commit()
        employee_id = employee.id
        db.close()
        
        update_data = {
            "id": employee_id,
            "firstname": "Jane"
        }
        
        response = client.put(
            "/employees/",
            json=update_data,
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 403

    def test_update_nonexistent_employee(self, client, admin_token):
        """Test updating a non-existent employee"""
        update_data = {
            "id": 999,
            "firstname": "Jane"
        }
        
        response = client.put(
            "/employees/",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 204

    def test_delete_employee_admin_success(self, client, test_db, admin_token, sample_employee_data):
        """Test successful employee deletion with admin role"""
        # Create test employee in database
        db = test_db()
        employee = Employee(**sample_employee_data)
        db.add(employee)
        db.commit()
        employee_id = employee.id
        db.close()
        
        delete_data = {"id": employee_id}
        
        response = client.request(
            "DELETE",
            "/employees/",
            json=delete_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        response_data = response.json()
        
        # Validate response
        assert "message" in response_data
        assert f"Employee with ID {employee_id}" in response_data["message"]

    def test_delete_employee_editor_forbidden(self, client, test_db, editor_token, sample_employee_data):
        """Test employee deletion with insufficient role (editor cannot delete)"""
        # Create test employee in database
        db = test_db()
        employee = Employee(**sample_employee_data)
        db.add(employee)
        db.commit()
        employee_id = employee.id
        db.close()
        
        delete_data = {"id": employee_id}
        
        response = client.request(
            "DELETE",
            "/employees/",
            json=delete_data,
            headers={"Authorization": f"Bearer {editor_token}"}
        )
        
        assert response.status_code == 403

    def test_delete_employee_user_forbidden(self, client, test_db, user_token, sample_employee_data):
        """Test employee deletion with insufficient role (user cannot delete)"""
        # Create test employee in database
        db = test_db()
        employee = Employee(**sample_employee_data)
        db.add(employee)
        db.commit()
        employee_id = employee.id
        db.close()
        
        delete_data = {"id": employee_id}
        
        response = client.request(
            "DELETE", 
            "/employees/",
            json=delete_data,
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 403

    def test_delete_nonexistent_employee(self, client, admin_token):
        """Test deleting a non-existent employee"""
        delete_data = {"id": 999}
        
        response = client.request(
            "DELETE",
            "/employees/",
            json=delete_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 204

    def test_get_employee_by_id_success(self, client, test_db, user_token, sample_employee_data):
        """Test successful retrieval of employee by ID"""
        # Create test employee in database
        db = test_db()
        employee = Employee(**sample_employee_data)
        db.add(employee)
        db.commit()
        employee_id = employee.id
        db.close()
        
        response = client.get(
            f"/employees/{employee_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 200
        response_data = response.json()
        
        # Validate response
        assert response_data["firstname"] == "John"
        assert response_data["lastname"] == "Doe"
        assert response_data["id"] == employee_id

    def test_get_employee_by_id_not_found(self, client, user_token):
        """Test getting employee by non-existent ID"""
        response = client.get(
            "/employees/999",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 204

    def test_get_employee_by_id_unauthorized(self, client, test_db, sample_employee_data):
        """Test getting employee by ID without authentication"""
        # Create test employee in database
        db = test_db()
        employee = Employee(**sample_employee_data)
        db.add(employee)
        db.commit()
        employee_id = employee.id
        db.close()
        
        response = client.get(f"/employees/{employee_id}")
        
        assert response.status_code == 403

    def test_invalid_token(self, client, sample_employee_data):
        """Test endpoint with invalid JWT token"""
        response = client.get(
            "/employees/",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 403

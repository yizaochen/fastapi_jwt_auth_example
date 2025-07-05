# FastAPI JWT Authentication API

## About This Project

This FastAPI application is designed as a Python equivalent of the Express.js application from [Dave Gray's MongoDB CRUD repository](https://github.com/gitdagray/mongo_async_crud). It implements JWT-based authentication with role-based access control, closely following the patterns and concepts taught in Dave Gray's excellent YouTube course ["Node.js Full Course for Beginners | Complete All-in-One Tutorial | 7 Hours"](https://youtu.be/f2EqECiTBL8?si=2EgTu2DMlNFOxxHj).

### Key Adaptations
- **Framework**: Express.js → FastAPI
- **Database**: MongoDB → SQLite with SQLAlchemy ORM
- **Language**: JavaScript/Node.js → Python
- **Authentication**: JWT implementation adapted for Python ecosystem

### Important Notice
⚠️ **AI-Generated Content Warning**: This codebase and documentation are largely generated with AI assistance. While functional and educational, please review and test thoroughly before using in production environments. Always validate security implementations and adapt to your specific requirements.

### Special Thanks
- **Dave Gray** for the comprehensive Node.js course and original Express.js implementation
- The original MongoDB CRUD project that served as the architectural foundation
- The FastAPI and SQLAlchemy communities for excellent documentation

## Database Setup and Initialization

### Prerequisites
1. Make sure you have all dependencies installed:
```console
uv sync --dev
```

2. Create a `.env` file in the project root with the following environment variables:
```env
# Database Configuration
SQLITE_DB_PATH=db.sqlite3

# JWT Secrets (use strong, random strings in production)
ACCESS_TOKEN_SECRET=your_access_token_secret_here
REFRESH_TOKEN_SECRET=your_refresh_token_secret_here
```

**Quick setup**: Copy the example environment file and customize it:
```console
cp .env.example .env
# Then edit .env with your preferred text editor
```

**Security Note**: In production, generate strong random secrets:
```console
python -c "import secrets; print('ACCESS_TOKEN_SECRET=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('REFRESH_TOKEN_SECRET=' + secrets.token_urlsafe(32))"
```

### Database Initialization

#### Option 1: Initialize Database with Sample Data (Recommended for Development)
Run the database initialization script to create tables and populate with sample users and employees:

```console
python db_init.py
```

This script will:
- Create the SQLite database file at the path specified in `SQLITE_DB_PATH`
- Create all necessary tables (users, employees, etc.)
- Add sample users with different roles:
  - `admin` (password: `admin`) - Has User, Editor, and Admin roles (2001,1984,5150)
  - `user1` (password: `user1pass`) - Has User role (2001)
  - `user2` (password: `user2pass`) - Has User and Editor roles (2001,1984)
- Add sample employees:
  - Dave Gray (ID: 1)
  - John Smith (ID: 2)

**Note**: The script checks for existing records before inserting, so it's safe to run multiple times.

#### Option 2: Initialize Empty Database
If you prefer to start with an empty database:

```console
python -c "
from sqlalchemy import create_engine
from models import Base
import os
from dotenv import load_dotenv

load_dotenv()
sqlite_db_path = os.getenv('SQLITE_DB_PATH', 'db.sqlite3')
engine = create_engine(f'sqlite:///{sqlite_db_path}')
Base.metadata.create_all(engine)
print('Empty database created successfully.')
"
```

### Database Schema

The application uses the following main models:

#### User Model
- `id`: Primary key (auto-increment)
- `username`: Unique username for login
- `password`: Bcrypt hashed password
- `roles`: Comma-separated role codes (e.g., "2001,1984,5150")

#### Employee Model
- `id`: Primary key (manually assigned)
- `firstname`: Employee's first name
- `lastname`: Employee's last name

### User Roles and Permissions

| Role | Code | Permissions |
|------|------|-------------|
| User | 2001 | Basic authenticated access |
| Editor | 1984 | Can create/update employees |
| Admin | 5150 | Full access including user management |

### Testing Database Setup

The test suite automatically creates temporary databases for each test run, so no manual database setup is required for testing. Each test class uses the `test_db` fixture that:
- Creates a temporary SQLite database
- Sets up all tables
- Overrides the main database dependency
- Cleans up after tests complete

### Database Management Commands

#### Reset Database
To completely reset the database (⚠️ **This will delete all data**):
```console
rm -f db.sqlite3  # Remove existing database file
python db_init.py  # Recreate with sample data
```

#### Backup Database
```console
cp db.sqlite3 backup_$(date +%Y%m%d_%H%M%S).sqlite3
```

#### View Database Contents
You can use any SQLite browser or command line:
```console
sqlite3 db.sqlite3 ".tables"  # List all tables
sqlite3 db.sqlite3 "SELECT * FROM users;"  # View all users
sqlite3 db.sqlite3 "SELECT * FROM employees;"  # View all employees
```

### Verify Database Setup

After running the initialization script, you can verify everything is set up correctly:

```console
# Check if database file was created
ls -la db.sqlite3

# Verify the application can start
fastapi dev main.py
```

The application should start without errors. You can then test the authentication by making a login request:

```console
# Test login with sample user (in another terminal)
curl -X POST "http://localhost:8000/auth" \
     -H "Content-Type: application/json" \
     -d '{"user": "admin", "pwd": "admin"}'
```

You should receive a JSON response with an access token if everything is working correctly.

### Troubleshooting Database Issues

#### Common Issues and Solutions

1. **"SQLITE_DB_PATH environment variable is not set"**
   - Make sure you have a `.env` file in the project root
   - Check that `SQLITE_DB_PATH=db.sqlite3` is set in your `.env` file

2. **"No module named 'models'"**
   - Make sure you're running the script from the project root directory
   - Verify all dependencies are installed: `uv sync --dev`

3. **Permission errors**
   - Check that you have write permissions in the project directory
   - On Unix systems, you may need to run: `chmod +x db_init.py`

4. **Database file exists but is corrupted**
   - Delete the existing database file: `rm db.sqlite3`
   - Re-run the initialization script: `python db_init.py`

5. **Import errors during initialization**
   - Ensure your Python environment is activated
   - Install missing dependencies: `uv sync --dev`

#### Development vs Production Setup

**Development (current setup)**:
- Uses SQLite database file
- Sample data included
- Debug-friendly configuration

**Production considerations**:
- Use a production database (PostgreSQL, MySQL, etc.)
- Generate strong, unique JWT secrets
- Remove or secure sample data
- Enable proper logging and monitoring
- Use environment-specific configuration files

## Run
```console
fastapi dev main.py
```

## How to Run All Tests

### Prerequisites
Make sure you have all dependencies installed:
```console
uv sync --dev
```

### Run All Tests at Once
```console
# Run all tests in the test directory
python -m pytest test/ -v

# Run all tests with coverage (if you have pytest-cov installed)
python -m pytest test/ -v --cov=.

# Run tests in parallel (if you have pytest-xdist installed)
python -m pytest test/ -v -n auto
```

### Run Individual Test Suites

#### Authentication Tests
```console
# Run auth tests
python -m pytest test/auth_test.py -v
# Or use the convenience script
python test/run_auth_tests.py
```

#### User Management Tests
```console
# Run users tests
python -m pytest test/users_test.py -v
# Or use the convenience script
python test/run_users_tests.py
```

#### Employee Management Tests
```console
# Run employees tests
python -m pytest test/employees_test.py -v
# Or use the convenience script
python test/run_employees_tests.py
```

#### Token Management Tests
```console
# Run refresh token tests
python -m pytest test/refresh_test.py -v
# Or use the convenience script
python test/run_refresh_tests.py

# Run logout tests
python -m pytest test/logout_test.py -v
# Or use the convenience script
python test/run_logout_tests.py
```

#### Registration Tests
```console
# Run register tests
python -m pytest test/register_test.py -v
# Or use the convenience script
python test/run_register_tests.py
```

### Run Specific Tests
```console
# Run a specific test class
python -m pytest test/users_test.py::TestUsersEndpoints -v

# Run a specific test method
python -m pytest test/users_test.py::TestUsersEndpoints::test_get_all_users_success -v

# Run tests matching a pattern
python -m pytest test/ -k "test_success" -v

# Run tests with specific markers (if configured)
python -m pytest test/ -m "integration" -v
```

### Test Output Options
```console
# Detailed output with stack traces
python -m pytest test/ -v --tb=long

# Short output format
python -m pytest test/ -v --tb=short

# Stop on first failure
python -m pytest test/ -v -x

# Show local variables in tracebacks
python -m pytest test/ -v --tb=long --showlocals
```

### Run Tests with Environment Variables
If you need to set specific environment variables for testing:
```console
# Set environment variables for testing
ACCESS_TOKEN_SECRET=test_secret python -m pytest test/ -v
```

## References and Resources

### Original Inspiration
- **Dave Gray's MongoDB CRUD Repository**: https://github.com/gitdagray/mongo_async_crud
- **Dave Gray's Node.js Full Course**: ["Node.js Full Course for Beginners | Complete All-in-One Tutorial | 7 Hours"](https://youtu.be/f2EqECiTBL8?si=2EgTu2DMlNFOxxHj)

### Additional Resources
- **FastAPI MVC Template**: https://github.com/ViktorViskov/fastapi-mvc/tree/main
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **SQLAlchemy Documentation**: https://docs.sqlalchemy.org/
- **JWT.io**: https://jwt.io/ (for understanding JWT tokens)
- **Python-JOSE**: https://python-jose.readthedocs.io/ (JWT library used in this project)

# FastAPI JWT Authentication API

This FastAPI application provides a complete JWT-based authentication system with role-based access control. This documentation will help you build a ReactJS frontend to consume these APIs.

## API Base URL
```
http://localhost:8000
```

## Authentication Flow

The API uses JWT (JSON Web Tokens) for authentication with the following flow:
1. **Login**: Get access token (15 min expiry) and refresh token (24 hours, stored as HTTP-only cookie)
2. **API Calls**: Include access token in `Authorization: Bearer <token>` header
3. **Token Refresh**: Use `/refresh` endpoint when access token expires
4. **Logout**: Clear tokens and invalidate session

## User Roles

- **User** (2001): Basic authenticated user
- **Editor** (1984): Can create/update employees
- **Admin** (5150): Full access including user management

---

## 🔐 Authentication Endpoints

### POST `/auth` - Login
**Purpose**: Authenticate user and get tokens

**Request Body**:
```json
{
  "user": "string",
  "pwd": "string"
}
```

**Success Response** (200):
```json
{
  "roles": [2001, 1984],
  "accessToken": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Cookie Set**: `jwt` (HTTP-only, contains refresh token)

**Errors**:
- 400: Missing username/password
- 401: Invalid credentials

---

### POST `/register` - Register New User
**Purpose**: Create a new user account

**Request Body**:
```json
{
  "user": "string",
  "pwd": "string"
}
```

**Success Response** (200):
```json
{
  "success": "New user john_doe created!"
}
```

**Errors**:
- 400: Missing username/password
- 409: Username already exists

---

### POST `/refresh` - Refresh Access Token
**Purpose**: Get new access token using refresh token

**Authentication**: Requires `jwt` cookie (refresh token)

**Success Response** (200):
```json
{
  "roles": [2001, 1984],
  "accessToken": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Errors**:
- 401: Missing refresh token cookie
- 403: Invalid/expired refresh token

---

### POST `/logout` - Logout
**Purpose**: Invalidate session and clear tokens

**Authentication**: Requires `jwt` cookie

**Success Response**: 204 (No Content)

**Note**: Clears refresh token from database and cookie

---

## 👥 User Management Endpoints
**(Admin Role Required)**

### GET `/users/` - Get All Users
**Purpose**: Retrieve all users in the system

**Authentication**: Bearer token with Admin role (5150)

**Success Response** (200):
```json
[
  {
    "id": 1,
    "username": "admin",
    "roles": [5150, 1984, 2001]
  },
  {
    "id": 2,
    "username": "editor",
    "roles": [1984, 2001]
  }
]
```

**Errors**:
- 401: Missing/invalid token
- 403: Insufficient permissions
- 204: No users found

---

### GET `/users/{user_id}` - Get Specific User
**Purpose**: Retrieve a specific user by ID

**Authentication**: Bearer token with Admin role (5150)

**Path Parameters**:
- `user_id`: integer

**Success Response** (200):
```json
{
  "id": 1,
  "username": "admin",
  "roles": [5150, 1984, 2001]
}
```

**Errors**:
- 400: Invalid user ID
- 401: Missing/invalid token
- 403: Insufficient permissions
- 204: User not found

---

### DELETE `/users/` - Delete User
**Purpose**: Delete a user by ID

**Authentication**: Bearer token with Admin role (5150)

**Request Body**:
```json
{
  "id": 1
}
```

**Success Response** (200):
```json
{
  "message": "User 1 deleted successfully"
}
```

**Errors**:
- 400: Missing user ID
- 401: Missing/invalid token
- 403: Insufficient permissions
- 204: User not found

---

## 👨‍💼 Employee Management Endpoints

### GET `/employees/` - Get All Employees
**Purpose**: Retrieve all employees

**Authentication**: Bearer token (any authenticated user)

**Success Response** (200):
```json
[
  {
    "id": 1,
    "firstname": "John",
    "lastname": "Doe"
  },
  {
    "id": 2,
    "firstname": "Jane",
    "lastname": "Smith"
  }
]
```

**Errors**:
- 401: Missing/invalid token
- 204: No employees found

---

### GET `/employees/{employee_id}` - Get Specific Employee
**Purpose**: Retrieve a specific employee by ID

**Authentication**: Bearer token (any authenticated user)

**Path Parameters**:
- `employee_id`: integer

**Success Response** (200):
```json
{
  "id": 1,
  "firstname": "John",
  "lastname": "Doe"
}
```

**Errors**:
- 401: Missing/invalid token
- 204: Employee not found

---

### POST `/employees/` - Create Employee
**Purpose**: Create a new employee

**Authentication**: Bearer token with Admin (5150) or Editor (1984) role

**Request Body**:
```json
{
  "firstname": "John",
  "lastname": "Doe"
}
```

**Success Response** (201):
```json
{
  "id": 3,
  "firstname": "John",
  "lastname": "Doe"
}
```

**Errors**:
- 401: Missing/invalid token
- 403: Insufficient permissions
- 500: Failed to create employee

---

### PUT `/employees/` - Update Employee
**Purpose**: Update an existing employee

**Authentication**: Bearer token with Admin (5150) or Editor (1984) role

**Request Body**:
```json
{
  "id": 1,
  "firstname": "John",
  "lastname": "Smith"
}
```

**Success Response** (200):
```json
{
  "id": 1,
  "firstname": "John",
  "lastname": "Smith"
}
```

**Errors**:
- 401: Missing/invalid token
- 403: Insufficient permissions
- 204: Employee not found
- 500: Failed to update employee

---

### DELETE `/employees/` - Delete Employee
**Purpose**: Delete an employee

**Authentication**: Bearer token with Admin (5150) role only

**Request Body**:
```json
{
  "id": 1
}
```

**Success Response** (200):
```json
{
  "message": "Employee with ID 1 has been deleted"
}
```

**Errors**:
- 401: Missing/invalid token
- 403: Insufficient permissions
- 204: Employee not found
- 500: Failed to delete employee

---

## 🌐 Static Content Endpoints

### GET `/` | `/index` | `/index.html` - Home Page
**Purpose**: Serve the main HTML page

**Success Response**: HTML content

---

## 🔧 Frontend Implementation Tips

### 1. **Token Management**
```javascript
// Store access token in localStorage or state
localStorage.setItem('accessToken', response.accessToken);

// Include in API requests
const headers = {
  'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
  'Content-Type': 'application/json'
};
```

### 2. **Automatic Token Refresh**
```javascript
// Set up axios interceptor for automatic token refresh
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 403 && error.config && !error.config._retry) {
      error.config._retry = true;
      try {
        const refreshResponse = await axios.post('/refresh', {}, { withCredentials: true });
        localStorage.setItem('accessToken', refreshResponse.data.accessToken);
        error.config.headers['Authorization'] = `Bearer ${refreshResponse.data.accessToken}`;
        return axios.request(error.config);
      } catch (refreshError) {
        // Redirect to login
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);
```

### 3. **Role-Based UI**
```javascript
// Check user roles for conditional rendering
const userRoles = [2001, 1984]; // From login response
const isAdmin = userRoles.includes(5150);
const isEditor = userRoles.includes(1984);

{isAdmin && <AdminPanel />}
{(isAdmin || isEditor) && <EditButton />}
```

### 4. **Cookie Configuration**
```javascript
// Enable credentials for refresh token cookie
axios.defaults.withCredentials = true;

// Or for individual requests
await axios.post('/refresh', {}, { withCredentials: true });
```

### 5. **Error Handling**
```javascript
try {
  const response = await axios.get('/employees/', { headers });
  setEmployees(response.data);
} catch (error) {
  if (error.response?.status === 401) {
    // Redirect to login
  } else if (error.response?.status === 403) {
    // Show permission denied message
  } else if (error.response?.status === 204) {
    // Handle no content (empty list)
    setEmployees([]);
  }
}
```

---
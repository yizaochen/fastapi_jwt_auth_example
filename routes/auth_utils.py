import os
import jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

load_dotenv()

# Security scheme for Bearer token
security = HTTPBearer()

ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET", "default_access_token_secret")

def verify_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verify JWT token from Authorization header.
    Equivalent to the JavaScript verifyJWT middleware.
    
    Args:
        credentials: HTTPAuthorizationCredentials from FastAPI security
        
    Returns:
        dict: Decoded token payload containing user info
        
    Raises:
        HTTPException: 401 for missing/invalid Bearer token, 403 for invalid/expired token
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract token from Bearer format
    token = credentials.credentials
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing from Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Verify and decode the JWT token
        decoded = jwt.decode(
            token,
            ACCESS_TOKEN_SECRET,
            algorithms=["HS256"]  # Specify the algorithm used
        )
        
        # Return the decoded token data (equivalent to setting req.user and req.roles)
        return {
            "username": decoded.get("UserInfo", {}).get("username"),
            "roles": decoded.get("UserInfo", {}).get("roles"),
            "decoded": decoded
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token verification failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(token_data: dict = Depends(verify_jwt)) -> str:
    """
    Extract username from verified JWT token.
    Equivalent to req.user in the JavaScript middleware.
    
    Args:
        token_data: Decoded token data from verify_jwt
        
    Returns:
        str: Username from the token
    """
    return token_data["username"]

def get_current_user_roles(token_data: dict = Depends(verify_jwt)) -> list:
    """
    Extract user roles from verified JWT token.
    Equivalent to req.roles in the JavaScript middleware.
    
    Args:
        token_data: Decoded token data from verify_jwt
        
    Returns:
        list: User roles from the token
    """
    return token_data["roles"]

def get_current_user_info(token_data: dict = Depends(verify_jwt)) -> dict:
    """
    Get complete user information from verified JWT token.
    
    Args:
        token_data: Decoded token data from verify_jwt
        
    Returns:
        dict: Complete user info including username and roles
    """
    return {
        "username": token_data["username"],
        "roles": token_data["roles"]
    }

# Role constants (equivalent to JavaScript ROLES_LIST)
ROLES = {
    "User": 2001,
    "Editor": 1984,
    "Admin": 5150
}

def verify_roles(*allowed_roles: int):
    """
    Role verification dependency factory.
    Equivalent to the JavaScript verifyRoles middleware.
    
    Args:
        *allowed_roles: Variable number of role IDs that are allowed
        
    Returns:
        Function that can be used as a FastAPI dependency
    """
    def role_checker(token_data: dict = Depends(verify_jwt)) -> dict:
        """
        Check if user has any of the required roles.
        
        Args:
            token_data: Decoded token data from verify_jwt
            
        Returns:
            dict: User info if roles are valid
            
        Raises:
            HTTPException: 403 if user doesn't have required roles
        """
        user_roles = token_data.get("roles", [])
        
        # Check if user has any of the allowed roles
        has_required_role = any(role in user_roles for role in allowed_roles)
        
        if not has_required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
            
        return token_data
    
    return role_checker

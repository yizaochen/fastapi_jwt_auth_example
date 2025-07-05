import os
import jwt
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from db import get_db
from models import User, serialize_roles

load_dotenv()

router = APIRouter()

ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET", "default_access_token_secret")
REFRESH_TOKEN_SECRET = os.getenv("REFRESH_TOKEN_SECRET", "default_refresh_token_secret")


@router.post("/refresh")
async def refresh_token(request: Request, db: Session = Depends(get_db)):
    """
    Handle refresh token to generate new access token.
    Equivalent to the Express.js handleRefreshToken function.
    """
    # Get cookies from request
    cookies = request.cookies
    if not cookies.get("jwt"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    refresh_token = cookies.get("jwt")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    # Find user with the refresh token
    found_user = db.query(User).filter(User.refresh_token == refresh_token).first()
    if not found_user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    try:
        # Verify the refresh token
        decoded = jwt.decode(
            refresh_token,
            REFRESH_TOKEN_SECRET,
            algorithms=["HS256"]
        )
        
        # Check if the username in token matches the user
        if found_user.username != decoded.get("username"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
        
        # Get user roles
        roles = serialize_roles(found_user.roles)
        
        # Generate new access token
        now = datetime.now(timezone.utc)
        access_token = jwt.encode(
            {
                "UserInfo": {
                    "username": decoded.get("username"),
                    "roles": roles
                },
                "exp": now + timedelta(seconds=10),  # 10 seconds expiry like the original
                "iat": now
            },
            ACCESS_TOKEN_SECRET,
            algorithm="HS256"
        )
        
        return JSONResponse({
            "roles": roles,
            "accessToken": access_token
        })
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    except Exception:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

import os
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from fastapi import APIRouter, Response, Depends, HTTPException, status
from pydantic import BaseModel
from dotenv import load_dotenv

from db import get_db
from models import User, serialize_roles

load_dotenv()

router = APIRouter()

class LoginRequest(BaseModel):
    user: str
    pwd: str

ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET", "default_access_token_secret")
REFRESH_TOKEN_SECRET = os.getenv("REFRESH_TOKEN_SECRET", "default_refresh_token_secret")


@router.post("/auth")
def login(request: LoginRequest, response: Response, db: Session = Depends(get_db)):
    # Validate input
    if not request.user or not request.pwd:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password are required.",
        )

    # Find user in database
    found_user = db.query(User).filter(User.username == request.user).first()
    if not found_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid username or password"
        )
    
    # Verify password
    try:
        if not bcrypt.checkpw(request.pwd.encode("utf-8"), found_user.password.encode("utf-8")):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid username or password"
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid username or password"
        )

    # Serialize user roles
    roles = serialize_roles(found_user.roles)
    
    # Current timestamp for token generation
    now = datetime.now(timezone.utc)

    try:
        # Generate access token
        access_token = jwt.encode(
            {
                "UserInfo": {
                    "username": found_user.username,
                    "roles": roles
                },
                "exp": now + timedelta(minutes=15),  # Access token valid for 15 minutes
                "iat": now  # Issued at time
            },
            ACCESS_TOKEN_SECRET,
            algorithm="HS256"
        )

        # Generate refresh token
        refresh_token = jwt.encode(
            {
                "username": found_user.username,
                "exp": now + timedelta(days=1),
                "iat": now
            },
            REFRESH_TOKEN_SECRET,
            algorithm="HS256"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate authentication tokens"
        )

    # Update user's refresh token in database
    try:
        found_user.refresh_token = refresh_token
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user session"
        )

    # Determine if we're in development or production
    is_development = os.getenv("ENVIRONMENT", "development").lower() == "development"
    
    # Set refresh token as HTTP-only cookie
    response.set_cookie(
        key="jwt",
        value=refresh_token,
        httponly=True,
        secure=not is_development,  # Only secure in production
        samesite="lax" if is_development else "none",  # More permissive in development
        max_age=24 * 60 * 60  # 24 hours
    )

    return {"roles": roles, "accessToken": access_token}

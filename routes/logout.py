import os
from sqlalchemy.orm import Session
from fastapi import APIRouter, Request, Response, Depends, status
from dotenv import load_dotenv

from db import get_db
from models import User

load_dotenv()

router = APIRouter()


@router.post("/logout")
async def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    """
    Handle logout by clearing refresh token from database and cookies.
    Equivalent to the Express.js handleLogout function.
    """
    # On client, also delete the accessToken (handled by client-side code)
    
    # Get cookies from request
    cookies = request.cookies
    if not cookies.get("jwt"):
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    
    refresh_token = cookies.get("jwt")
    if not refresh_token:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    
    # Is refreshToken in db?
    found_user = db.query(User).filter(User.refresh_token == refresh_token).first()
    if not found_user:
        # Clear the cookie even if user not found
        _clear_jwt_cookie(response)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    
    # Delete refreshToken in db
    try:
        found_user.refresh_token = ""
        db.commit()
        print(f"Cleared refresh token for user: {found_user.username}")
    except Exception as e:
        db.rollback()
        print(f"Error clearing refresh token: {e}")
    
    # Clear the JWT cookie
    _clear_jwt_cookie(response)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _clear_jwt_cookie(response: Response):
    """Helper function to clear the JWT cookie with proper settings."""
    # Determine if we're in development or production
    is_development = os.getenv("ENVIRONMENT", "development").lower() == "development"
    
    response.delete_cookie(
        key="jwt",
        httponly=True,
        secure=not is_development,  # Only secure in production
        samesite="lax" if is_development else "none"  # More permissive in development
    )

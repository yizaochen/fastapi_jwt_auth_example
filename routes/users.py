from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from .auth_utils import verify_roles, ROLES
from db import get_db
from models import User, serialize_roles
from pydantic import BaseModel

router = APIRouter()


class DeleteUserRequest(BaseModel):
    id: int


@router.get("/", dependencies=[Depends(verify_roles(ROLES["Admin"]))])
async def get_all_users(db: Session = Depends(get_db)):
    """
    Get all users (Admin only).
    Equivalent to Express.js getAllUsers controller.
    """
    users = db.query(User).all()

    if not users:
        return JSONResponse(status_code=204, content={"message": "No users found"})

    # Convert users to response format (excluding sensitive data like passwords)
    user_data = []
    for user in users:
        user_data.append(
            {"id": user.id, "username": user.username, "roles": serialize_roles(user.roles)}
        )

    return user_data


@router.delete("/", dependencies=[Depends(verify_roles(ROLES["Admin"]))])
async def delete_user(request: DeleteUserRequest, db: Session = Depends(get_db)):
    """
    Delete a user by ID (Admin only).
    Equivalent to Express.js deleteUser controller.
    """
    if not request.id:
        raise HTTPException(status_code=400, detail="User ID required")

    user = db.query(User).filter(User.id == request.id).first()

    if not user:
        return JSONResponse(
            status_code=204, content={"message": f"User ID {request.id} not found"}
        )

    # Delete the user
    db.delete(user)
    db.commit()

    return {"message": f"User {request.id} deleted successfully"}


@router.get("/{user_id}", dependencies=[Depends(verify_roles(ROLES["Admin"]))])
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """
    Get a specific user by ID (Admin only).
    Equivalent to Express.js getUser controller.
    """
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID required")

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        return JSONResponse(
            status_code=204, content={"message": f"User ID {user_id} not found"}
        )

    # Return user data (excluding sensitive information)
    return {"id": user.id, "username": user.username, "roles": serialize_roles(user.roles)}

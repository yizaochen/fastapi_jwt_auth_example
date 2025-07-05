import bcrypt
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from db import get_db
from models import User

router = APIRouter()

class RegisterRequest(BaseModel):
    user: str
    pwd: str


@router.post("/register")
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    if not request.user or not request.pwd:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password are required.",
        )

    duplicate = db.query(User).filter(User.username == request.user).first()
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username already exists."
        )

    hashed_pwd = bcrypt.hashpw(request.pwd.encode("utf-8"), bcrypt.gensalt())

    new_user = User(username=request.user, password=hashed_pwd.decode("utf-8"))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"success": f"New user {request.user} created!"}

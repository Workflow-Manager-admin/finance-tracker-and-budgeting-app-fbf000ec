"""
Authentication endpoints and models for the Finance Tracker backend.
Handles user registration, login, password hashing (bcrypt), and JWT token issuance.
FUTURE: Integrate with database layer for user storage/lookup.
"""

from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
import os
from sqlalchemy.orm import Session
from .db import UserORM, get_db

# === JWT settings ===
SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 1 week

# bcrypt password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2PasswordBearer expects an /auth/login endpoint (which we provide)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

router = APIRouter(prefix="/auth", tags=["Authentication"])

# --------------------------------------------------------------------
# User models (Pydantic and connection to ORM)
class User(BaseModel):
    user_id: str
    username: str
    email: str
    hashed_password: str

class CreateUserRequest(BaseModel):
    username: str = Field(..., example="alice", description="Unique username")
    email: EmailStr = Field(..., example="alice@email.com", description="Email address")
    password: str = Field(..., min_length=6, example="secret", description="User password")

class LoginRequest(BaseModel):
    username: str = Field(..., example="alice", description="Username")
    password: str = Field(..., min_length=6, example="secret", description="User password")

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str

# PUBLIC_INTERFACE
def user_orm_to_model(userorm: UserORM) -> User:
    """Convert UserORM to User Pydantic model."""
    return User(
        user_id=userorm.user_id,
        username=userorm.username,
        email=userorm.email,
        hashed_password=userorm.hashed_password,
    )

# PUBLIC_INTERFACE
def get_user_by_username(username: str, db: Session) -> Optional[User]:
    """
    Retrieve a user object by username from the DB.
    """
    user_orm = db.query(UserORM).filter(UserORM.username == username).first()
    if not user_orm:
        return None
    return user_orm_to_model(user_orm)

# PUBLIC_INTERFACE
def get_user_by_id(user_id: str, db: Session) -> Optional[User]:
    """
    Retrieve a user by their unique user_id.
    """
    user_orm = db.query(UserORM).filter(UserORM.user_id == user_id).first()
    if not user_orm:
        return None
    return user_orm_to_model(user_orm)

# PUBLIC_INTERFACE
def create_user(username: str, email: str, password: str, db: Session) -> User:
    """
    Create and store a user in the database and return the user object.
    """
    if db.query(UserORM).filter(UserORM.username == username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    if db.query(UserORM).filter(UserORM.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = pwd_context.hash(password)
    user_orm = UserORM(username=username, email=email, hashed_password=hashed_password)
    db.add(user_orm)
    db.commit()
    db.refresh(user_orm)
    return user_orm_to_model(user_orm)

# PUBLIC_INTERFACE
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify the password using bcrypt.
    """
    return pwd_context.verify(plain_password, hashed_password)

# PUBLIC_INTERFACE
def authenticate_user(username: str, password: str, db: Session) -> Optional[User]:
    """
    Validate user credentials. Returns user if successful, None otherwise.
    """
    user = get_user_by_username(username, db)
    if user and verify_password(password, user.hashed_password):
        return user
    return None

# PUBLIC_INTERFACE
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Generate JWT access token.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# PUBLIC_INTERFACE
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    Retrieve the current user from a JWT token using the database.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user_by_username(username, db)
    if user is None:
        raise credentials_exception
    return user

# ========================================================================
# AUTH ROUTES

# PUBLIC_INTERFACE
@router.post("/register", status_code=201,
    summary="Register a new user",
    description="Registers a new user and returns a JWT access token.")
async def register_user(reg: CreateUserRequest, db: Session = Depends(get_db)):
    if get_user_by_username(reg.username, db):
        raise HTTPException(status_code=400, detail="Username already taken")
    if db.query(UserORM).filter(UserORM.email == reg.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = create_user(reg.username, reg.email, reg.password, db)
    access_token = create_access_token(data={"sub": user.username, "user_id": user.user_id})
    return AuthResponse(access_token=access_token, token_type="bearer", user_id=user.user_id)

# PUBLIC_INTERFACE
@router.post(
    "/login",
    summary="User login (JWT auth)",
    description="Authenticates user and returns JWT access token."
)
async def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    access_token = create_access_token(data={"sub": user.username, "user_id": user.user_id})
    return AuthResponse(access_token=access_token, token_type="bearer", user_id=user.user_id)

# PUBLIC_INTERFACE
@router.post(
    "/logout",
    status_code=204,
    summary="Logout user",
    description="Logs out the user (JWT logout is stateless; just instruct frontend to discard token)."
)
async def logout_user(request: Request, current_user: User = Depends(get_current_user)):
    # No backend action for JWT logout; frontend should just discard the token
    # This endpoint exists to maintain REST docs and for possible session-control expansion.
    return


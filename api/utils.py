from typing import Optional
import os
from deta import Deta
from fastapi import APIRouter, Form, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta, timezone

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", '')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_VALIDITY_MINUTES = int(os.getenv("REFRESH_TOKEN_VALIDITY", "720")) # 12 hrs, after this you need to login

oauth2_schema = OAuth2PasswordBearer(tokenUrl="token")
router = APIRouter(
    prefix="/token",
    tags=["utils"],)

text_db = Deta()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(BaseModel):
    email: str = "@b-tu.de"
    active_inactive: str  = "inactive"
    tag: str = "student"

class CustomOAuth2PasswordRequestForm:
    def __init__(
        self,
        grant_type: str = Form(default="password", regex="password|refresh_token"),
        username: str = Form(default=None),
        password: str = Form(default=None),
        refresh_token: str = Form(default=None),
        scope: str = Form(default=""),
        client_id: Optional[str] = Form(default=None),
        client_secret: Optional[str] = Form(default=None),
    ):
        self.grant_type = grant_type
        self.username = username
        self.password = password
        self.refresh_token = refresh_token
        self.scopes = scope.split()
        self.client_id = client_id
        self.client_secret = client_secret

def authenticate_user(username, password):
    if username.endswith(("@b-tu.de", "@gmail.com")):
        user_info = text_db.Base("user-access")
        info = user_info.fetch({"email": username}).items
        if info:
            if pwd_context.verify(password, info[-1].get('hashed_password')):
                return True
    return False

def get_user_details(token: str=Depends(oauth2_schema)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get('email', "")
    except jwt.PyJWTError:
        raise credentials_exception
    user_info = text_db.Base("user-access")
    valid_user = user_info.fetch({"email": email}).items
    if valid_user:
        user = User(**valid_user[-1])
        return user
    return credentials_exception

def admin_user(current_user: User=Depends(get_user_details)):
    if not current_user.tag == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You dont have authorization to make changes",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return True   

def generic_user(current_user: User=Depends(get_user_details)):
    if not current_user.active_inactive == "active":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User has been deactivated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return True

@router.post("/", include_in_schema=True)
async def get_token(form_data: CustomOAuth2PasswordRequestForm=Depends()):
    email = ""
    access_token = ""
    refresh_token = form_data.refresh_token
    if form_data.grant_type == "password":
        email = form_data.username
        if not authenticate_user(form_data.username, form_data.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"}
            )
        access_token = jwt.encode(
            {
                "email": email,
                "iat": datetime.now(tz=timezone.utc),
                "exp": datetime.now(tz=timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)},
            JWT_SECRET_KEY, algorithm=ALGORITHM)
        refresh_token = jwt.encode(
            {
                "email": email,
                "iat": datetime.now(tz=timezone.utc),
                "exp": datetime.now(tz=timezone.utc) + timedelta(minutes=REFRESH_TOKEN_VALIDITY_MINUTES)},
            JWT_SECRET_KEY, algorithm=ALGORITHM)
    if form_data.grant_type == "refresh_token":
        try:
            payload = jwt.decode(form_data.refresh_token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
            email = payload.get("email")
            access_token = jwt.encode(
            {
                "email": email,
                "iat": datetime.now(tz=timezone.utc),
                "exp": datetime.now(tz=timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES*2)},
            JWT_SECRET_KEY, algorithm=ALGORITHM)
        except (jwt.PyJWTError):
            HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Please login again",
                    headers={"WWW-Authenticate": "Bearer"}
                )
    refresh_token = refresh_token
    return {"access_token": access_token, "refresh_token": refresh_token, "access_type": "bearer"}
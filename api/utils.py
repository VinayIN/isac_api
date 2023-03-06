import os
from deta import Deta
from fastapi import APIRouter, Depends, Form, HTTPException, status, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from passlib.context import CryptContext
import jwt, json
from datetime import datetime, timedelta


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_schema = OAuth2PasswordBearer(tokenUrl="token")
text_db = Deta()
router = APIRouter(
    prefix="/token",
    tags=["utils"]
)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(BaseModel):
    email: str = "@b-tu.de"
    active_inactive: str  = "inactive"
    tag: str = "student"

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
        payload = jwt.decode(token, os.getenv('JWT_SECRET_KEY', ''), algorithms=[ALGORITHM])
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

@router.post("/", include_in_schema=False)
async def get_token(form_data: OAuth2PasswordRequestForm=Depends()):
    if not authenticate_user(form_data.username, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    token_expires = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    email = form_data.username
    access_token = jwt.encode(jsonable_encoder({"email": email, "expires_at": token_expires.isoformat()}), os.getenv('JWT_SECRET_KEY', ''), algorithm=ALGORITHM)
    return {"access_token": access_token, "access_type": "bearer"}
    
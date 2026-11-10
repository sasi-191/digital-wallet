from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from config import ALGORITHM, SECRET_KEY, TOKEN_MINUTES
from database import get_db
from db_models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode(), hashed_password.encode())


def create_access_token(username):
    expires = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_MINUTES)
    return jwt.encode({"sub": username, "exp": expires}, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    error = HTTPException(status_code=401, detail="Please log in again",
                          headers={"WWW-Authenticate": "Bearer"})
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = data.get("sub")
    except JWTError:
        raise error

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise error
    return user

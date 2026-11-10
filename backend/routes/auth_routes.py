from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from auth import create_access_token, hash_password, verify_password
from database import get_db
from db_models import User, Wallet
from schemas import RegisterRequest

router = APIRouter(tags=["login"])


@router.post("/register", status_code=201)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == request.username).first() is not None:
        raise HTTPException(status_code=400, detail="This username is taken")

    user = User(username=request.username, hashed_password=hash_password(request.password))
    db.add(user)
    db.flush()      # gives the user an id, so the wallet can point to it
    db.add(Wallet(user_id=user.id, name=user.username, balance_paise=0))
    db.commit()
    return {"message": "Account created. You can log in now."}


@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form.username).first()
    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Wrong username or password")
    return {"access_token": create_access_token(user.username), "token_type": "bearer"}

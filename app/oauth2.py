from fastapi import Depends, status, HTTPException
from fastapi.security.oauth2 import OAuth2PasswordBearer
from jose import JWTError, jwt  # For JWT Bearer token
from datetime import datetime, timedelta
from . import schemas, databases, models
from sqlalchemy.orm import Session
from .config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
#ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes


def create_access_token(data: dict):
    to_encode = data.copy()

    # expire = datetime.utcnow() + timedelta(
    #     minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    # )  # always expiration time is in utc
    # to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_access_token(token: str, credentials_exceptions):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        user_id: str = payload.get("user_id")

        if user_id is None:
            raise credentials_exceptions

        token_data = schemas.TokenData(id=user_id)

    except JWTError:
        raise credentials_exceptions

    return token_data


def get_current_user(token: str = Depends(oauth2_scheme),
                     db: Session = Depends(databases.get_db)):
    credentials_exceptions = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f"Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = verify_access_token(token, credentials_exceptions)

    user_data = db.query(
        models.Users).filter(models.Users.id == token.id).first()

    return user_data

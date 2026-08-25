from datetime import datetime , timedelta  ,timezone
from typing import Dict ,Any
from src.config.settings import settings
import jwt
from passlib.context import CryptContext


crypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(credentials: Dict[str, Any]):

    to_encode = credentials.copy()


    expires_in = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({'exp': expires_in})

    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

    return encoded_jwt


def verify_password(user_pass :str ,hashed_password : str):
    return crypt_context.verify(user_pass ,hashed_password )


def get_password_hash(password : str):
    return crypt_context.hash(password)


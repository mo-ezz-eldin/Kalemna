from datetime import datetime , timedelta  ,timezone
from typing import Dict ,Any
from src.config.settings import settings
import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException , status

from src.presentation.api.dependency import oauth2_scheme

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


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])

        username = payload.get("sub")

        user_id = payload.get("user_id")

        if user_id is None or username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                          detail="could not validate credentials",
                          headers={"WWW-Authenticate": "Bearer"})

    except jwt.ExpiredSignatureError:

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")

    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                          detail="could not validate credentials",
                          headers={"WWW-Authenticate": "Bearer"})

    return {'user_id': user_id , 'username': username}


def rate_limit_by_user(request: Request):
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm] ,
                                 options={'verify_exp':False})
            user_id = payload.get('user_id')
            if user_id:
                return f'user_id:{user_id}'
        except Exception:
            pass


    return get_remote_address(request)






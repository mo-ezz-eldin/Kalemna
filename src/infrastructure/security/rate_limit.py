from fastapi import Request
import jwt
from slowapi import Limiter
from slowapi.util import get_remote_address
from src.config.settings import settings


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


limiter = Limiter(key_func=rate_limit_by_user)
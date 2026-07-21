from fastapi import Request
from loguru import logger
from fastapi.responses import JSONResponse


def exception_handler(request: Request, exc: Exception):
    logger.exception(f'there is an error at {request.url} - Error {exc}')

    return JSONResponse(content={'success': False, 'message': 'عذراً، حدث خطأ تقني، جاري العمل على حله.'}, status_code=500)
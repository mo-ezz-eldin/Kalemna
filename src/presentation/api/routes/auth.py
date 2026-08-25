from fastapi import APIRouter, Depends , HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from src.domain.interfaces.IDatabase import IDatabase
from src.infrastructure.security.user_security_credentials import verify_password, create_access_token, \
    get_password_hash
from src.presentation.api.dependency import get_db
from src.presentation.api.schemas import Token_Data, UserSignup

auth_router = APIRouter()

@auth_router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: IDatabase = Depends(get_db)
) -> Token_Data:


    user = await db.get_user(form_data.username)

    if not user or not verify_password(form_data.password, user.get('hashed_password')):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    encrypted_token = create_access_token({'sub': user.get('username'),
                                           'user_id': str(user.get('user_id'))})

    return Token_Data(access_token=encrypted_token, token_type="Bearer")




@auth_router.post("/signup")
async def signup(user_details: UserSignup, db: IDatabase = Depends(get_db)):
    existing_user = await db.get_user(user_details.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists"
        )

    user_dict = user_details.model_dump()

    raw_password = user_dict.pop('password')
    user_dict['hashed_password'] = get_password_hash(raw_password)


    user_id = await db.create_user(user_dict)

    if not user_id:
        raise HTTPException(status_code=500, detail="Database error occurred")

    encrypted_token = create_access_token({'sub': user_details.username , 'user_id': str(user_id)})

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"message": "User created successfully", "access_token": encrypted_token}
    )



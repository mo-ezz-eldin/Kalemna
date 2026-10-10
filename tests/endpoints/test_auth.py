from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import HTTPException

from src.config.settings import settings
from src.infrastructure.security.user_security_credentials import (
    create_access_token,
    get_current_user,
    get_password_hash,
    verify_password,
)


@pytest.mark.asyncio(loop_scope="session")
async def test_signup_success(client, db):
    new_user = {
        "username": "test_user",
        "password": "123456",
        "email": "test_email@gmail.com",
        "phone": "01019440379",
        "default_address": "test_default_address",
    }

    response = await client.post("/signup", json=new_user)
    data = response.json()
    assert response.status_code == 201
    assert response.json()["message"] == "User created successfully"
    assert "access_token" in data
    user = await db.get_user_by_username(new_user["username"])
    assert verify_password(new_user["password"], user["hashed_password"]) == True
    assert user["hashed_password"] != "123456"


@pytest.mark.asyncio(loop_scope="session")
async def test_signup_user_found(client, db):
    password = "123456"

    hashed_pass = get_password_hash(password)

    new_user = {
        "username": "test_user",
        "hashed_password": hashed_pass,
        "email": "test_email@gmail.com",
        "phone": "01019440379",
        "default_address": "test_default_address",
    }

    await db.create_user(new_user)

    signup_user = {
        "username": "test_user",
        "password": password,
        "email": new_user["email"],
        "phone": new_user["phone"],
        "default_address": new_user["default_address"],
    }

    response = await client.post("/signup", json=signup_user)

    assert response.status_code == 409


@pytest.mark.asyncio(loop_scope="session")
async def test_login_success(client, db):

    user = {"username": "test_user", "password": "19389832m"}

    hashed_pass = get_password_hash(user["password"])

    new_user = {
        "username": "test_user",
        "hashed_password": hashed_pass,
        "email": "test_email@gmail.com",
        "phone": "01019440379",
        "default_address": "test_default_address",
    }

    await db.create_user(new_user)

    response = await client.post("/login", data=user)
    data = response.json()
    assert response.status_code == 200
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "Bearer"


@pytest.mark.asyncio(loop_scope="session")
async def test_login_wrong_password(client, db):
    wrong_password = "19389832mm"
    correct_password = "19389832m"
    user = {"username": "test_user", "password": wrong_password}

    hashed_pass = get_password_hash(correct_password)

    new_user = {
        "username": "test_user",
        "hashed_password": hashed_pass,
        "email": "test_email@gmail.com",
        "phone": "01019440379",
        "default_address": "test_default_address",
    }

    await db.create_user(new_user)

    response = await client.post("/login", data=user)

    assert response.status_code == 401

    assert response.json()["detail"] == "Incorrect username or password"

    assert response.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.asyncio(loop_scope="session")
async def test_login_user_not_found(client, db):

    user = {"username": "test_user", "password": "1929893982m"}

    response = await client.post("/login", data=user)

    assert response.status_code == 401

    assert response.json()["detail"] == "Incorrect username or password"

    assert response.headers["WWW-Authenticate"] == "Bearer"


async def test_verify_password_and_hash():

    user_pass = "12349554"

    wrong_pass = "12349554mo"

    hashed_pass = get_password_hash(user_pass)

    assert verify_password(user_pass, hashed_pass) == True

    assert verify_password(wrong_pass, hashed_pass) == False

    assert get_password_hash(user_pass) != user_pass


async def test_create_access_token(create_token):

    decoded_payload = jwt.decode(create_token, settings.secret_key, algorithms=[settings.algorithm])

    assert decoded_payload["sub"] == "test_user"
    assert decoded_payload["user_id"] == 10
    assert decoded_payload["exp"] is not None


async def test_get_current_user_invalid_token():

    invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.token"

    with pytest.raises(HTTPException) as e:
        await get_current_user(invalid_token)

    assert e.value.status_code == 401
    assert e.value.detail == "could not validate credentials"


@pytest.mark.asyncio
async def test_get_current_user_expired_token():
    payload = {"sub": "test_user", "user_id": 10}

    expire = datetime.now(timezone.utc) + timedelta(minutes=-1)

    payload.update({"exp": expire})

    encoded = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

    with pytest.raises(HTTPException) as e:
        await get_current_user(encoded)

    assert e.value.status_code == 401
    assert e.value.detail == "Token has expired"


@pytest.mark.asyncio
async def test_get_current_user_missing_payload_data():

    incomplete_payload = {"user_id": "1"}

    token = create_access_token(incomplete_payload)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token=token)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "could not validate credentials"


@pytest.mark.asyncio
async def test_get_current_user_valid_token():

    token = create_access_token({"sub": "valid_user", "user_id": "15"})

    user_dict = await get_current_user(token=token)

    assert user_dict["username"] == "valid_user"
    assert user_dict["user_id"] == "15"

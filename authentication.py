from passlib.context import CryptContext
from models import *
from fastapi import FastAPI, status, HTTPException, Depends
import jwt
from dotenv import dotenv_values

config_credentials = dict(dotenv_values(".env"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_pass(password):
    return pwd_context.hash(password)

def verify_password(normal_password, hash_password):
    return pwd_context.verify(normal_password, hash_password)


async def authenticate_user(username: str, password: str):
    user = await User.get(username = username)
    if user  and verify_password(password, user.password):
        return user
    return False

async def token_generator(username: str, password: str):
    user = await authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED, 
            detail = "Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = {
        "id" : user.id,
        "username" : user.username
    }

    token = jwt.encode(token_data, "secret")
    return token

    
import logging 
import datetime
from typing import Annotated
from database import users_table, database
from jose import jwt, ExpiredSignatureError, JWTError
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

__name__="core.main"
logger=logging.getLogger(__name__)

pwd_context=CryptContext(schemes=["bcrypt"])

def hash_password(password:str)->str:
    return(pwd_context.hash(password))

def verify_password(plain_password:str,hashed_password:str)->bool:
    return(pwd_context.verify(plain_password,hashed_password))

SECRET_KEY="cae7ed63dd93fe2c3913c317e401ac662d461c9c8cb251f6ebb535ad570eecea"
ALGORITHM="HS256"
oauth2scheme=OAuth2PasswordBearer(tokenUrl="token")

def access_token_expire_minutes()->int:
    return 30


def create_access_token(username: str):
    logger.info("Creating access token")
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=access_token_expire_minutes())
    expire_timestamp = int(expire.timestamp())  # convert to int

    content = {"sub": username, "expire": expire_timestamp}
    jwt_encoded = jwt.encode(content, key=SECRET_KEY, algorithm=ALGORITHM)
    return jwt_encoded

credential_error= HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate":"Bearer"}
    )

async def authenticate_user(username:str,password:str):
    logger.info("Authenticating user")
    user=await get_user(username)
    if user is None:
        raise credential_error
    if not verify_password(password,user['password']):
        raise credential_error
    return user


async def get_user(username:str):
    logger.info("Fetching user with username")
    query=users_table.select().where(users_table.c.username==username)
    result=await database.fetch_one(query)
    print(result)
    return result

async def get_current_user(token: Annotated[str, Depends(oauth2scheme)]):
    logger.info("Getting current user from token")
    try:
        payload=jwt.decode(token=token,key=SECRET_KEY,algorithms=[ALGORITHM]) 
    except ExpiredSignatureError as e:
        raise HTTPException(status_code=401,detail="Token has expired",headers={"WWW-Authenticate":"Bearer"}) from e
    except jwt.JWTError as e:
        raise credential_error from e
    username=payload.get("sub")
    user=await get_user(username)
    if user is None:
        raise credential_error
    return user



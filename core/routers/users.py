import logging
from fastapi import APIRouter, HTTPException, status, Depends
from database import users_table, farmer_table, buyer_table, database
from models.users import *
from security import get_user, verify_password, create_access_token,get_current_user
from typing import Annotated
from security import hash_password, authenticate_user
from fastapi.security import OAuth2PasswordRequestForm

router=APIRouter()

__name__="storeapi.main"
logger=logging.getLogger(__name__)

@router.post("/register",status_code=status.HTTP_201_CREATED)
async def register_user(user:User):
    if await get_user(user.username):
        print("User already exists")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")
    query=users_table.insert().values(username=user.username,email=user.email,password=hash_password(user.password)) 
    logger.debug(query)
    await database.execute(query)
    created_user=await get_user(user.username)
    if user.role=="farmer":
        farmer_query=farmer_table.insert().values(user_id=created_user.id,  age=None, aadhar_id=None, location=None)
        await database.execute(farmer_query)
    elif user.role=="buyer":
        buyer_query=buyer_table.insert().values(user_id=created_user.id, crop_id=None, sold_price=None, location=None)
        await database.execute(buyer_query)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role specified")
    
    return {"message":"User created successfully"}
    
@router.post("/token")
async def login(form_data:OAuth2PasswordRequestForm=Depends()):
    logger.info("Attempting login")
    user=await authenticate_user(form_data.username,form_data.password)
    access_token=create_access_token(user.username)
    return {"access_token":access_token, "token_type":"bearer"}

async def get_user_by_id(user_id:int):
    query=users_table.select().where(users_table.c.id==user_id)
    user =await database.fetch_one(query)
    return user
    

@router.put("/farmers/{user_id}",status_code=status.HTTP_200_OK)
async def update_farmer(user_id:int, farmer:Farmer,current_user:Annotated[User,Depends(get_current_user)]):
    if not await get_user_by_id(user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    query=farmer_table.update().where(farmer_table.c.user_id==user_id).values(**farmer.dict())
    await database.execute(query)
    return {"message":"Farmer updated successfully"}

@router.put("/buyers/{user_id}",status_code=status.HTTP_200_OK)
async def update_buyer(user_id:int, buyer:Buyer,current_user:Annotated[User,Depends(get_current_user)]):
    if not await get_user_by_id(user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    query=buyer_table.update().where(buyer_table.c.user_id==user_id).values(**buyer.dict())
    await database.execute(query)
    return {"message":"Buyer updated successfully"}
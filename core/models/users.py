from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
# ---------------------------
# USER & AUTHENTICATION MODELS
# ---------------------------

class User(BaseModel):
    username: str
    email: str
    password: str
    role:str

class UserOut(BaseModel):
    username: str
    password: str
    

class UserIn(User):
    id:int

# ---------------------------
# FARMER MODELS
# ---------------------------

class Farmer(BaseModel):
    age: int
    aadhar_id: str
    location: str


# ---------------------------
# BUYER MODELS
# ---------------------------

class Buyer(BaseModel):
    user_id: int
    crop_id: Optional[int] = None
    sold_price: Optional[int] = None
    location: str


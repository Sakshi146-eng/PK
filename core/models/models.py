from fastapi import FastAPI
from pydantic import BaseModel
from datetime import date
from typing import Optional

# ---------------------------
# LAND MODELS
# ---------------------------

class LandIn(BaseModel):
    location: str
    soil: str
    size: float
    crop_id: list[int]
    harvest_date: Optional[date] = None


class Land(LandIn):
    id: int


# ---------------------------
# CROP MODELS
# ---------------------------

class CropIn(BaseModel):
    name: str


class Crop(CropIn):
    id: int


# ---------------------------
# PLANTED CROP MODELS
# ---------------------------

class PlantedCropIn(BaseModel):
    crop_id: int
    land_id: int
    quantity: int
    planting_date: date
    harvest_date: Optional[date] = None


class PlantedCrop(PlantedCropIn):
    id: int


# ---------------------------
# CROP GROWTH MODELS
# ---------------------------

class CropGrowthIn(BaseModel):
    growth_stage: str
    date_recorded: date


class CropGrowth(CropGrowthIn):
    pass


# ---------------------------
# TRANSACTION MODELS
# ---------------------------

class TransactionIn(BaseModel):
    buyer_id: int
    planted_crop_id: int
    selling_price: int
    purchase_price: int
    buy: bool = False


class Transaction(TransactionIn):
    id: int


class TransactionCreate(BaseModel):
    selling_price: int  # farmer's price


class PurchaseOffer(BaseModel):
    buyer_id: int
    purchase_price: int  # buyer's offer
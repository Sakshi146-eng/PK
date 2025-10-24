from fastapi import APIRouter, HTTPException, status, Depends
from models.models import LandIn, CropGrowthIn,TransactionCreate, PurchaseOffer
from database import land_table, database, crop_table, planted_crop_table, crop_growth_table, transaction_table, buyer_table
from datetime import date
from typing import List

router=APIRouter()

@router.post("/register-land/{user_id}", status_code=status.HTTP_201_CREATED)
async def register_land(user_id:int, land:LandIn):
    query=land_table.insert().values(
        location=land.location,
        soil=land.soil,
        size=land.size,
        owner_id=user_id
    )
    land_id=await database.execute(query)
    valid_crops=await database.fetch_all(crop_table.select().where(crop_table.c.id.in_(land.crop_id)))
    if len(valid_crops)!=len(land.crop_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more crop IDs are invalid")
    for crop in land.crop_id:
        planted_crop_query=planted_crop_table.insert().values(
            crop_id=crop,
            land_id=land_id,
            quantity=0,
            planting_date=date.today(),
            harvest_date=land.harvest_date
        )
        await database.execute(planted_crop_query)
    return {"message":"Land registered successfully", "land_id":land_id}

@router.post("/record-growth/{planted_crop_id}", status_code=status.HTTP_201_CREATED)
async def record_growth(planted_crop_id: int, data: CropGrowthIn):
    try:
        # Insert the growth record into database
        query = crop_growth_table.insert().values(
            planted_crop_id=planted_crop_id,
            growth_stage=data.growth_stage,  # store the image URL
            date_recorded=date.today()
        )
        await database.execute(query)

        return {
            "message": "Growth record saved successfully",
            "planted_crop_id": planted_crop_id,
            "image_url": data.growth_stage,
            "date_recorded": str(date.today())
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving growth record: {str(e)}"
        )
    

@router.post("/harvest-ready/", status_code=status.HTTP_201_CREATED)
async def move_harvest_ready_crops():
    """
    Checks for crops whose harvest_date == today
    and creates a transaction entry for them with the farmer's selling price.
    """

    today = date.today()

    # Fetch all harvested crops ready today
    query = planted_crop_table.select().where(planted_crop_table.c.harvest_date == today)
    harvested_crops = await database.fetch_all(query)

    if not harvested_crops:
        return {"message": "No crops ready for harvest today."}

    created_transactions = []

    for crop in harvested_crops:
        # Ensure not already in transaction table
        check_query = transaction_table.select().where(
            transaction_table.c.planted_crop_id == crop.id
        )
        existing_txn = await database.fetch_one(check_query)
        if existing_txn:
            continue  # Skip already listed crops

        # Ask frontend to provide farmer’s selling price later (default 0 for now)
        insert_query = transaction_table.insert().values(
            buyer_id=None,  # buyer not decided yet
            planted_crop_id=crop.id,
            selling_price=0,
            purchase_price=0,
            buy=False,
        )
        txn_id = await database.execute(insert_query)
        created_transactions.append(txn_id)

    return {"message": "Transactions created for harvested crops", "transaction_ids": created_transactions}


# ---------------------------
# 2️⃣ Farmer Sets Selling Price
# ---------------------------

@router.put("/set-selling-price/{planted_crop_id}")
async def set_selling_price(planted_crop_id: int, data: TransactionCreate):
    """
    Farmer sets or updates the selling price for a harvested crop.
    """

    # Check if crop already exists in transaction table
    query = transaction_table.select().where(transaction_table.c.planted_crop_id == planted_crop_id)
    transaction = await database.fetch_one(query)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found for this crop")

    update_query = (
        transaction_table.update()
        .where(transaction_table.c.planted_crop_id == planted_crop_id)
        .values(selling_price=data.selling_price)
    )
    await database.execute(update_query)

    return {"message": "Selling price set successfully"}


# ---------------------------
# 3️⃣ Buyer Places an Offer
# ---------------------------

@router.put("/offer/{planted_crop_id}")
async def make_offer(planted_crop_id: int, offer: PurchaseOffer):
    """
    Buyer places an offer for a crop.
    """
    query = transaction_table.select().where(transaction_table.c.planted_crop_id == planted_crop_id)
    transaction = await database.fetch_one(query)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if not offer.buyer_id in await database.fetch_all("SELECT user_id FROM buyers"):
        raise HTTPException(status_code=400, detail="Invalid buyer ID")

    update_query = (
        transaction_table.update()
        .where(transaction_table.c.planted_crop_id == planted_crop_id)
        .values(
            buyer_id=offer.buyer_id,
            purchase_price=offer.purchase_price
        )
    )

    
    await database.execute(update_query)

    return {"message": "Offer placed successfully"}


# ---------------------------
# 4️⃣ Farmer Accepts Offer
# ---------------------------

@router.put("/accept-offer/{planted_crop_id}")
async def accept_offer(planted_crop_id: int):
    """
    Farmer accepts a buyer's offer → finalizes transaction.
    """

    query = transaction_table.select().where(transaction_table.c.planted_crop_id == planted_crop_id)
    transaction = await database.fetch_one(query)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if not transaction["buyer_id"]:
        raise HTTPException(status_code=400, detail="No buyer has placed an offer yet")

    # Mark transaction as bought
    update_query = (
        transaction_table.update()
        .where(transaction_table.c.planted_crop_id == planted_crop_id)
        .values(buy=True)
    )
    await database.execute(update_query)

    # Record this purchase in buyer_profile table
    # (Assuming buyer_profile has columns: buyer_id, crop_id, and total_spent or sold_price)
    insert_profile_query = buyer_table.insert().values(
        buyer_id=transaction["buyer_id"],
        crop_id=transaction["planted_crop_id"],
        sold_price=transaction["purchase_price"]
    )
    await database.execute(insert_profile_query)

    return {
        "message": "Offer accepted. Transaction completed successfully.",
        "buyer_id": transaction["buyer_id"],
        "crop_id": transaction["planted_crop_id"],
        "sold_price": transaction["purchase_price"]
    }


# ---------------------------
# 5️⃣ View All Active Transactions
# ---------------------------

@router.get("/transactions/", response_model=List[dict])
async def list_transactions():
    """
    Returns all active transactions (where buy = False)
    """
    query = transaction_table.select().where(transaction_table.c.buy == False)
    transactions = await database.fetch_all(query)
    return transactions

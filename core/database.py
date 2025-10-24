import databases
import sqlalchemy
from config import config

metadata=sqlalchemy.MetaData()


users_table=sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id",sqlalchemy.Integer,primary_key=True),
    sqlalchemy.Column("username",sqlalchemy.String,unique=True),
    sqlalchemy.Column("email",sqlalchemy.String,unique=True),
    sqlalchemy.Column("password",sqlalchemy.String)
)

farmer_table=sqlalchemy.Table(
    "farmers",
    metadata,
    sqlalchemy.Column("user_id",sqlalchemy.ForeignKey("users.id"),primary_key=True),
    sqlalchemy.Column("age",sqlalchemy.Integer,nullable=True),
    sqlalchemy.Column("aadhar_id",sqlalchemy.String,unique=True,nullable=True),
    sqlalchemy.Column("location",sqlalchemy.String,nullable=True),

)

buyer_table = sqlalchemy.Table(
    "buyers",
    metadata,
    sqlalchemy.Column("user_id", sqlalchemy.ForeignKey("users.id"), primary_key=True),
    sqlalchemy.Column("location", sqlalchemy.String),
    sqlalchemy.Column("total_sold_price", sqlalchemy.Integer, default=0),  # total sum of all purchases
)

buyer_purchases_table = sqlalchemy.Table(
    "buyer_purchases",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("buyer_id", sqlalchemy.ForeignKey("buyers.user_id")),
    sqlalchemy.Column("crop_id", sqlalchemy.ForeignKey("transactions.planted_crop_id")),
    sqlalchemy.Column("sold_price", sqlalchemy.Integer)
)


land_table=sqlalchemy.Table(
    "land",
    metadata,
    sqlalchemy.Column("id",sqlalchemy.Integer,primary_key=True),
    sqlalchemy.Column("location",sqlalchemy.String),
    sqlalchemy.Column("soil",sqlalchemy.String),
    sqlalchemy.Column("size",sqlalchemy.Float),
    sqlalchemy.Column("owner_id",sqlalchemy.ForeignKey("users.id")),
)

crop_table = sqlalchemy.Table(
    "crops",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("name", sqlalchemy.String, unique=True, nullable=False),
)

planted_crop_table = sqlalchemy.Table(
    "planted_crops",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("crop_id", sqlalchemy.ForeignKey("crops.id")),
    sqlalchemy.Column("land_id", sqlalchemy.ForeignKey("land.id")),
    sqlalchemy.Column("quantity", sqlalchemy.Integer, nullable=False),
    sqlalchemy.Column("planting_date", sqlalchemy.Date, nullable=False),
    sqlalchemy.Column("harvest_date", sqlalchemy.Date, nullable=True),
)

crop_growth_table = sqlalchemy.Table(
    "crop_growth",
    metadata,
    sqlalchemy.Column("planted_crop_id", sqlalchemy.ForeignKey("planted_crops.id")),
    sqlalchemy.Column("growth_stage", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("date_recorded", sqlalchemy.Date, nullable=False),
)

transaction_table = sqlalchemy.Table(
    "transactions",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("buyer_id", sqlalchemy.ForeignKey("buyers.user_id")),
    sqlalchemy.Column("planted_crop_id", sqlalchemy.ForeignKey("planted_crops.crop_id")),
    sqlalchemy.Column("selling_price", sqlalchemy.Integer, nullable=False),
    sqlalchemy.Column("purchase_price", sqlalchemy.Integer, nullable=False),
    sqlalchemy.Column("buy", sqlalchemy.Boolean, default=False),
)

PREDEFINED_CROPS = ["Wheat", "Rice", "Corn", "Soybeans", "Cotton", "Barley", "Oats", "Sorghum"]



engine=sqlalchemy.create_engine(config.DATABASE_URL,connect_args={"check_same_thread":False})

metadata.create_all(engine)
database=databases.Database(config.DATABASE_URL,force_rollback=config.DB_FORCE_ROLLBACK)

with engine.connect() as conn:
    existing_crops=conn.execute(sqlalchemy.select(crop_table.c.name)).scalars().all()
    new_crops=[c for c in PREDEFINED_CROPS if c not in existing_crops]
    if new_crops:
        conn.execute(crop_table.insert(),[{"name":c} for c in new_crops])
        conn.commit()
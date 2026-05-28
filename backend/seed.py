from database import SessionLocal
from models import Product

db = SessionLocal()

products = [
    Product(
        name="Vgate iCar Pro Bluetooth 4.0",
        price=590,
        in_stock=True
    ),
    Product(
        name="Foxsur FPT-200",
        price=1490,
        in_stock=True
    )
]

db.add_all(products)
db.commit()
db.close()

print("Products added successfully")
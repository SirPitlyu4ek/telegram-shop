from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Product, Order

from integrations.salesdrive import send_order_to_salesdrive
from integrations.novaposhta import search_cities, get_warehouses

app = FastAPI()


class OrderCreate(BaseModel):
    customer_name: str
    phone: str
    telegram_id: str | None = None
    telegram_username: str | None = None
    product_id: int
    quantity: int
    city: str | None = None
    warehouse: str | None = None
    payment_method: str | None = None
    comment: str | None = None


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def home():
    return {"message": "Telegram shop backend is working"}


@app.get("/products")
def get_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()

    result = []

    for product in products:
        result.append({
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "in_stock": product.in_stock
        })

    return result


@app.post("/orders")
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == order.product_id).first()

    if product is None:
        return {"error": "Product not found"}

    total_price = product.price * order.quantity

    new_order = Order(
        customer_name=order.customer_name,
        phone=order.phone,
        telegram_id=order.telegram_id,
        telegram_username=order.telegram_username,
        product_id=order.product_id,
        quantity=order.quantity,
        total_price=total_price,
        city=order.city,
        warehouse=order.warehouse,
        payment_method=order.payment_method,
        comment=order.comment,
        status="new"
    )

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    salesdrive_result = send_order_to_salesdrive(
        new_order,
        product
    )

    return {
        "id": new_order.id,
        "customer_name": new_order.customer_name,
        "phone": new_order.phone,
        "telegram_id": new_order.telegram_id,
        "telegram_username": new_order.telegram_username,
        "product": {
            "id": product.id,
            "name": product.name,
            "price": product.price
        },
        "quantity": new_order.quantity,
        "total_price": new_order.total_price,
        "city": new_order.city,
        "warehouse": new_order.warehouse,
        "payment_method": new_order.payment_method,
        "comment": new_order.comment,
        "status": new_order.status,
        "salesdrive": salesdrive_result
    }


@app.get("/orders")
def get_orders(db: Session = Depends(get_db)):
    orders = db.query(Order).all()

    result = []

    for order in orders:
        product = db.query(Product).filter(Product.id == order.product_id).first()

        result.append({
            "id": order.id,
            "customer_name": order.customer_name,
            "phone": order.phone,
            "telegram_id": order.telegram_id,
            "telegram_username": order.telegram_username,
            "product": product.name if product else None,
            "quantity": order.quantity,
            "total_price": order.total_price,
            "city": order.city,
            "warehouse": order.warehouse,
            "payment_method": order.payment_method,
            "comment": order.comment,
            "status": order.status
        })

    return result


@app.get("/novaposhta/cities")
def novaposhta_cities(city: str):
    return search_cities(city)


@app.get("/novaposhta/warehouses")
def novaposhta_warehouses(city_ref: str):
    return get_warehouses(city_ref)
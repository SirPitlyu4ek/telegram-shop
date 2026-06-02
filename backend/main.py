from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Product, Order
from typing import Literal

from integrations.salesdrive import (
    send_order_to_salesdrive,
    notify_salesdrive_payment,
    update_salesdrive_payment_status,
    set_salesdrive_payment_unpaid
)

from integrations.novaposhta import search_cities, get_warehouses
from integrations.rozetka_delivery import get_rozetka_cities, get_rozetka_departments
import json
import time
from fastapi import Request

from integrations.wayforpay import (
    create_payment_url,
    generate_wayforpay_callback_signature,
    generate_wayforpay_accept_signature
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class OrderCreate(BaseModel):
    customer_name: str
    last_name: str | None = None
    middle_name: str | None = None
    phone: str
    email: str | None = None
    telegram_id: str | None = None
    telegram_username: str | None = None
    product_id: int
    quantity: int
    city: str | None = None
    warehouse: str | None = None
    city_ref: str | None = None
    warehouse_ref: str | None = None
    payment_method: Literal["Накладений платіж", "WayForPay", "Оплата на рахунок"]
    comment: str | None = None
    shipping_method: Literal["novaposhta", "rozetka", "ukrposhta"]


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

    if order.shipping_method == "ukrposhta" and order.payment_method == "Накладений платіж":
        return {"error": "Для Укрпошти доступна тільки повна передоплата"}

    total_price = product.price * order.quantity

    new_order = Order(
        customer_name=order.customer_name,
        last_name=order.last_name,
        middle_name=order.middle_name,
        phone=order.phone,
        email=order.email,
        telegram_id=order.telegram_id,
        telegram_username=order.telegram_username,
        product_id=order.product_id,
        quantity=order.quantity,
        total_price=total_price,
        city=order.city,
        warehouse=order.warehouse,
        city_ref=order.city_ref,
        warehouse_ref=order.warehouse_ref,
        payment_method=order.payment_method,
        comment=order.comment,
        shipping_method=order.shipping_method,
        status="Новий",
        payment_status="Не оплачений"
    )

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    salesdrive_result = {
        "status_code": None,
        "response": "SalesDrive request was not sent"
    }

    try:
        salesdrive_result = send_order_to_salesdrive(new_order, product)

        try:
            salesdrive_response = json.loads(salesdrive_result["response"])

            if salesdrive_response.get("success"):
                new_order.salesdrive_order_id = salesdrive_response["data"]["orderId"]
                db.commit()
                db.refresh(new_order)

                if new_order.payment_method in ["WayForPay", "Оплата на рахунок"]:
                    try:
                        unpaid_result = set_salesdrive_payment_unpaid(new_order)
                        print("SalesDrive unpaid status:", unpaid_result)

                        salesdrive_result["payment_status_update"] = unpaid_result

                    except Exception as error:
                        print("SalesDrive unpaid status error:", error)

                        salesdrive_result["payment_status_update"] = {
                            "status_code": 0,
                            "response": f"SalesDrive unpaid status error: {str(error)}"
                        }
                else:
                    print("SalesDrive payment status skipped for cash on delivery")

        except Exception as error:
            print("SalesDrive response parse error:", error)
            
            salesdrive_result["parse_error"] = str(error)

    except Exception as error:
        print("SalesDrive connection error:", error)

        salesdrive_result = {
            "status_code": 0,
            "response": f"SalesDrive connection error: {str(error)}"
        }

    return {
        "id": new_order.id,
        "customer_name": new_order.customer_name,
        "last_name": new_order.last_name,
        "middle_name": new_order.middle_name,
        "phone": new_order.phone,
        "email": new_order.email,
        "telegram_id": new_order.telegram_id,
        "telegram_username": new_order.telegram_username,
        "product": {
            "id": product.id,
            "name": product.name,
            "price": product.price
        },
        "quantity": new_order.quantity,
        "total_price": new_order.total_price,
        "shipping_method": new_order.shipping_method,
        "city": new_order.city,
        "warehouse": new_order.warehouse,
        "city_ref": new_order.city_ref,
        "warehouse_ref": new_order.warehouse_ref,
        "payment_method": new_order.payment_method,
        "payment_status": new_order.payment_status,
        "comment": new_order.comment,
        "status": new_order.status,
        "salesdrive": salesdrive_result,
        "salesdrive_order_id": new_order.salesdrive_order_id,
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
            "last_name": order.last_name,
            "middle_name": order.middle_name,
            "phone": order.phone,
            "email": order.email,
            "telegram_id": order.telegram_id,
            "telegram_username": order.telegram_username,
            "product": product.name if product else None,
            "quantity": order.quantity,
            "total_price": order.total_price,
            "shipping_method": order.shipping_method,
            "city": order.city,
            "warehouse": order.warehouse,
            "city_ref": order.city_ref,
            "warehouse_ref": order.warehouse_ref,
            "payment_method": order.payment_method,
            "payment_status": order.payment_status,
            "comment": order.comment,
            "status": order.status,
            "salesdrive_order_id": order.salesdrive_order_id,
        })

    return result


@app.get("/novaposhta/cities")
def novaposhta_cities(city: str):
    return search_cities(city)


@app.get("/novaposhta/warehouses")
def novaposhta_warehouses(city_ref: str):
    return get_warehouses(city_ref)


@app.get("/rozetka/cities")
def rozetka_cities():
    return get_rozetka_cities()


@app.get("/rozetka/departments")
def rozetka_departments(city_id: str):
    return get_rozetka_departments(city_id)


@app.get("/orders/{order_id}/payment-url")
def get_order_payment_url(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()

    if order is None:
        return {"error": "Order not found"}

    product = db.query(Product).filter(Product.id == order.product_id).first()

    if product is None:
        return {"error": "Product not found"}

    payment_url = create_payment_url(order, product)

    return {
        "order_id": order.id,
        "payment_status": order.payment_status,
        "payment_url": payment_url
    }


@app.post("/wayforpay/callback")
async def wayforpay_callback(request: Request, db: Session = Depends(get_db)):
    data = await request.json()

    order_reference = data.get("orderReference")
    transaction_status = data.get("transactionStatus")
    received_signature = data.get("merchantSignature")

    expected_signature = generate_wayforpay_callback_signature(data)

    if received_signature != expected_signature:
        return {"error": "Invalid signature"}

    if not order_reference:
        return {"error": "Missing orderReference"}

    order_id = order_reference.replace("ORDER-", "")

    order = db.query(Order).filter(Order.id == int(order_id)).first()

    if order is None:
        return {"error": "Order not found"}

    if transaction_status == "Approved":
        order.payment_status = "Оплачений"
        db.commit()
        db.refresh(order)
        
        if order.salesdrive_order_id:
            salesdrive_update_result = update_salesdrive_payment_status(order)
            print("SalesDrive payment status update:", salesdrive_update_result)
        else:
            notify_salesdrive_payment(order)

    response_time = int(time.time())
    response_status = "accept"
    response_signature = generate_wayforpay_accept_signature(
        order_reference,
        response_status,
        response_time
    )

    return {
        "orderReference": order_reference,
        "status": response_status,
        "time": response_time,
        "signature": response_signature
    }
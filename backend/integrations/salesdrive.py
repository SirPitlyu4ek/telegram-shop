import os
import requests
from dotenv import load_dotenv

load_dotenv()

SALESDRIVE_API_KEY = os.getenv("SALESDRIVE_API_KEY")
SALESDRIVE_DOMAIN = os.getenv("SALESDRIVE_DOMAIN")


def send_order_to_salesdrive(order, product):
    url = f"https://{SALESDRIVE_DOMAIN}/handler/"
    
    shipping_method_parameters = {
        "novaposhta": "Нова Пошта",
        "rozetka": "Видача у ROZETKA",
        "ukrposhta": 'Доставка "Укрпошта"'
    }

    shipping_method_names = {
        "novaposhta": "Нова Пошта",
        "rozetka": "Rozetka Delivery",
        "ukrposhta": "Укрпошта"
    }

    payment_method_parameters = {
        "Накладений платіж": "id_13",
        "WayForPay": "Оплата картой Visa, Mastercard - WayForPay",
        "Оплата на рахунок": "Оплата на счет"
    }

    shipping_method_parameter = shipping_method_parameters.get(
        order.shipping_method,
        order.shipping_method
    )

    shipping_method_name = shipping_method_names.get(
        order.shipping_method,
        order.shipping_method
    )

    payment_method_parameter = payment_method_parameters.get(
        order.payment_method,
        order.payment_method
    )

    payload = {
        "form": SALESDRIVE_API_KEY,
        "getResultData": 1,

        "fName": order.customer_name,
        "lName": order.last_name or "",
        "mName": order.middle_name or "",
        "phone": order.phone,
        "email": order.email or "",

        "products": [
            {
                "id": str(product.id),
                "name": product.name,
                "costPerItem": int(product.price),
                "amount": int(order.quantity),
                "description": "Товар із Telegram-магазину",
                "sku": str(product.id)
            }
        ],

        "payment_method": payment_method_parameter,
        "shipping_method": shipping_method_parameter,
        "shipping_address": f"{order.city}, {order.warehouse}",

        "comment": (
            f"{order.comment or ''}\n\n"
            f"Спосіб доставки: {shipping_method_name}\n"
            f"Місто: {order.city}\n"
            f"Відділення: {order.warehouse}"
        ),

        "externalId": str(order.id),

        "sajt": "Telegram Mini App",
        "utmSource": "telegram",
        "utmMedium": "bot",
        "utmCampaign": "telegram_shop",

        "con_telegram": order.telegram_username or ""
    }

    if order.shipping_method == "novaposhta":
        payload["novaposhta"] = {
            "ServiceType": "Warehouse",
            "payer": "recipient",
            "city": order.city_ref,
            "WarehouseNumber": order.warehouse_ref
        }


    if order.shipping_method == "rozetka":
        payload["rozetka_delivery"] = {
            "payer": "recipient"
        }


    if order.shipping_method == "ukrposhta":
        payload["ukrposhta"] = {
            "ServiceType": "Warehouse",
            "payer": "recipient"
        }

    response = requests.post(url, json=payload, timeout=15)

    return {
        "status_code": response.status_code,
        "response": response.text
    }

def add_payment_note_to_salesdrive(order):
    url = f"https://{SALESDRIVE_DOMAIN}/api/order/note/"

    payload = {
        "form": SALESDRIVE_API_KEY,
        "id": order.salesdrive_order_id,
        "note": (
            f"Оплату отримано через WayForPay\n"
            f"ID замовлення в backend: {order.id}\n"
            f"Сума: {order.total_price} грн\n"
            f"Статус оплати: {order.payment_status}"
        )
    }

    response = requests.post(url, json=payload, timeout=15)

    return {
        "status_code": response.status_code,
        "response": response.text
    }

def update_salesdrive_payment_status(order):
    url = f"https://{SALESDRIVE_DOMAIN}/api/order/update/"

    payload = {
        "form": SALESDRIVE_API_KEY,
        "id": order.salesdrive_order_id,
        "data[statusOplati2]": "id_66"
    }

    response = requests.post(url, data=payload, timeout=15)

    return {
        "status_code": response.status_code,
        "response": response.text
    }

def set_salesdrive_payment_unpaid(order):
    url = f"https://{SALESDRIVE_DOMAIN}/api/order/update/"

    payload = {
        "form": SALESDRIVE_API_KEY,
        "id": order.salesdrive_order_id,
        "data[statusOplati2]": "id_65"
    }

    response = requests.post(url, data=payload, timeout=15)

    return {
        "status_code": response.status_code,
        "response": response.text
    }

def notify_salesdrive_payment(order):
    url = f"https://{SALESDRIVE_DOMAIN}/handler/"

    payload = {
        "form": SALESDRIVE_API_KEY,
        "getResultData": 1,
        "externalId": f"PAYMENT-{order.id}",
        "fName": order.customer_name,
        "lName": order.last_name or "",
        "phone": order.phone,
        "payment_method": order.payment_method,
        "comment": (
            f"Оплату отримано через WayForPay\n"
            f"ID замовлення в backend: {order.id}\n"
            f"Сума: {order.total_price} грн\n"
            f"Статус оплати: {order.payment_status}"
        ),
        "utmSource": "telegram",
        "utmMedium": "payment_callback",
        "utmCampaign": "wayforpay_paid"
    }

    response = requests.post(url, json=payload, timeout=15)

    return {
        "status_code": response.status_code,
        "response": response.text
    }
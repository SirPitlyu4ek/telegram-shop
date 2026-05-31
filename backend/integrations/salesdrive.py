import os
import requests
from dotenv import load_dotenv

load_dotenv()

SALESDRIVE_API_KEY = os.getenv("SALESDRIVE_API_KEY")
SALESDRIVE_DOMAIN = os.getenv("SALESDRIVE_DOMAIN")


def send_order_to_salesdrive(order, product):
    url = f"https://{SALESDRIVE_DOMAIN}/handler/"

    payload = {
        "form": SALESDRIVE_API_KEY,
        "getResultData": 1,

        "fName": order.customer_name,
        "phone": order.phone,

        "products": [
            {
                "name": product.name,
                "costPerItem": product.price,
                "amount": order.quantity,
                "description": "Товар із Telegram-магазину"
            }
        ],

        "payment_method": order.payment_method or "Не вказано",
       "shipping_method": order.shipping_method or "novaposhta",
        "shipping_address": f"{order.city}, {order.warehouse}",

        "comment": order.comment or "",
        "externalId": str(order.id),
        "sajt": "Telegram Mini App",
        "con_telegram": order.telegram_username or "",

        "utmSource": "telegram",
        "utmMedium": "bot",
        "utmCampaign": "telegram_shop"
    }

    response = requests.post(url, json=payload, timeout=15)

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
import os
import time
import hmac
import hashlib
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()

WAYFORPAY_MERCHANT_ACCOUNT = os.getenv("WAYFORPAY_MERCHANT_ACCOUNT")
WAYFORPAY_SECRET_KEY = os.getenv("WAYFORPAY_SECRET_KEY")
WAYFORPAY_DOMAIN = os.getenv("WAYFORPAY_DOMAIN")


def generate_wayforpay_signature(data: list[str]) -> str:
    signature_string = ";".join(data)

    return hmac.new(
        WAYFORPAY_SECRET_KEY.encode("utf-8"),
        signature_string.encode("utf-8"),
        hashlib.md5
    ).hexdigest()


def create_payment_url(order, product):
    order_reference = f"ORDER-{order.id}"
    order_date = int(time.time())
    amount = order.total_price
    currency = "UAH"

    product_name = product.name
    product_count = order.quantity
    product_price = product.price

    signature_data = [
        WAYFORPAY_MERCHANT_ACCOUNT,
        WAYFORPAY_DOMAIN,
        order_reference,
        str(order_date),
        str(amount),
        currency,
        product_name,
        str(product_count),
        str(product_price)
    ]

    merchant_signature = generate_wayforpay_signature(signature_data)

    params = {
        "merchantAccount": WAYFORPAY_MERCHANT_ACCOUNT,
        "merchantDomainName": WAYFORPAY_DOMAIN,
        "merchantSignature": merchant_signature,
        "orderReference": order_reference,
        "orderDate": order_date,
        "amount": amount,
        "currency": currency,
        "productName[]": product_name,
        "productCount[]": product_count,
        "productPrice[]": product_price,
        "language": "UA",
        "serviceUrl": "https://bungee-spleen-dealmaker.ngrok-free.dev/wayforpay/callback"
    }

    return "https://secure.wayforpay.com/pay/get?" + urlencode(params)

def generate_wayforpay_callback_signature(data: dict) -> str:
    signature_data = [
        data.get("merchantAccount", ""),
        data.get("orderReference", ""),
        str(data.get("amount", "")),
        data.get("currency", ""),
        data.get("authCode", ""),
        data.get("cardPan", ""),
        data.get("transactionStatus", ""),
        str(data.get("reasonCode", ""))
    ]

    return generate_wayforpay_signature(signature_data)


def generate_wayforpay_accept_signature(order_reference: str, status: str, timestamp: int) -> str:
    signature_data = [
        order_reference,
        status,
        str(timestamp)
    ]

    return generate_wayforpay_signature(signature_data)
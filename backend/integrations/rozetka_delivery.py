import requests

ROZETKA_DELIVERY_API_URL = "https://rz-delivery.rozetka.ua/api"


def get_rozetka_cities():
    url = f"{ROZETKA_DELIVERY_API_URL}/city"

    response = requests.get(url, timeout=15)

    return response.json()


def get_rozetka_departments(city_id: str):
    url = f"{ROZETKA_DELIVERY_API_URL}/department"

    params = {
        "city_id": city_id
    }

    response = requests.get(url, params=params, timeout=15)

    return response.json()
import os
import requests
from dotenv import load_dotenv

load_dotenv()

NOVAPOSHTA_API_KEY = os.getenv("NOVAPOSHTA_API_KEY")
NOVAPOSHTA_API_URL = "https://api.novaposhta.ua/v2.0/json/"


def search_cities(city_name: str):
    payload = {
        "apiKey": NOVAPOSHTA_API_KEY,
        "modelName": "Address",
        "calledMethod": "getCities",
        "methodProperties": {
            "FindByString": city_name,
            "Limit": "10"
        }
    }

    response = requests.post(NOVAPOSHTA_API_URL, json=payload, timeout=15)
    return response.json()


def get_warehouses(city_ref: str):
    payload = {
        "apiKey": NOVAPOSHTA_API_KEY,
        "modelName": "Address",
        "calledMethod": "getWarehouses",
        "methodProperties": {
            "CityRef": city_ref
        }
    }

    response = requests.post(NOVAPOSHTA_API_URL, json=payload, timeout=15)
    return response.json()
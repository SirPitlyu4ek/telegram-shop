import os
import requests
from dotenv import load_dotenv

load_dotenv()

NOVAPOSHTA_API_KEY = os.getenv("NOVAPOSHTA_API_KEY")
NOVAPOSHTA_API_URL = "https://api.novaposhta.ua/v2.0/json/"


def search_cities(city: str):
    payload = {
        "apiKey": NOVAPOSHTA_API_KEY,
        "modelName": "Address",
        "calledMethod": "searchSettlements",
        "methodProperties": {
            "CityName": city,
            "Limit": "10",
            "Page": "1"
        }
    }

    try:
        response = requests.post(NOVAPOSHTA_API_URL, json=payload, timeout=15)
        return response.json()

    except Exception as error:
        print("Nova Poshta city search error:", error)

        return {
            "success": False,
            "data": [
                {
                    "Addresses": []
                }
            ],
            "errors": [str(error)]
        }


def get_warehouses(city_ref: str, limit: int = 500):
    warehouses = []
    page = 1

    try:
        while True:
            payload = {
                "apiKey": NOVAPOSHTA_API_KEY,
                "modelName": "AddressGeneral",
                "calledMethod": "getWarehouses",
                "methodProperties": {
                    "CityRef": city_ref,
                    "Limit": str(limit),
                    "Page": str(page),
                    "Language": "UA"
                }
            }

            response = requests.post(NOVAPOSHTA_API_URL, json=payload, timeout=15)
            data = response.json()

            items = data.get("data", [])

            if not items:
                break

            for item in items:
                warehouses.append({
                    "ref": item.get("Ref"),
                    "number": item.get("Number"),
                    "description": item.get("Description"),
                    "short_address": item.get("ShortAddress"),
                    "city": item.get("CityDescription"),
                    "type": item.get("TypeOfWarehouse"),
                    "type_ref": item.get("TypeOfWarehouseRef"),
                    "category": item.get("CategoryOfWarehouse")
                })

            if len(items) < limit:
                break

            page += 1

        return {
            "success": True,
            "count": len(warehouses),
            "warehouses": warehouses,
            "errors": [],
            "warnings": []
        }

    except Exception as error:
        print("Nova Poshta warehouses error:", error)

        return {
            "success": False,
            "count": 0,
            "warehouses": [],
            "errors": [str(error)],
            "warnings": []
        }
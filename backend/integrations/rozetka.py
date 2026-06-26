import requests


ROZETKA_API_URL = "https://rz-delivery.rozetka.ua/api"


def _safe_json_response(response):
    try:
        return response.json()
    except Exception:
        return {
            "statusCode": 1,
            "data": [],
            "errors": [response.text[:500]],
        }


def search_rozetka_cities(city: str = ""):
    try:
        response = requests.get(
            f"{ROZETKA_API_URL}/city",
            timeout=20,
        )

        data = _safe_json_response(response)

        if isinstance(data, dict):
            return data

        if isinstance(data, list):
            return {
                "statusCode": 0,
                "data": data,
                "errors": [],
            }

        return {
            "statusCode": 1,
            "data": [],
            "errors": ["Unexpected Rozetka cities response"],
        }

    except Exception as error:
        print("Rozetka city search error:", error)

        return {
            "statusCode": 1,
            "data": [],
            "errors": [str(error)],
        }


def get_rozetka_departments(city_id: str):
    if not city_id:
        return {
            "statusCode": 1,
            "data": [],
            "errors": ["city_id is required"],
        }

    try:
        response = requests.get(
            f"{ROZETKA_API_URL}/department",
            params={
                "city_id": city_id,
            },
            timeout=20,
        )

        data = _safe_json_response(response)

        if isinstance(data, dict):
            return data

        if isinstance(data, list):
            return {
                "statusCode": 0,
                "data": data,
                "errors": [],
            }

        return {
            "statusCode": 1,
            "data": [],
            "errors": ["Unexpected Rozetka departments response"],
        }

    except Exception as error:
        print("Rozetka departments error:", error)

        return {
            "statusCode": 1,
            "data": [],
            "errors": [str(error)],
        }
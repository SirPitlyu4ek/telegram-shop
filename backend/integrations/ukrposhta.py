import os
import xml.etree.ElementTree as ET

import requests


UKRPOSHTA_ADDRESS_API_URL = "https://www.ukrposhta.ua/address-classifier"
UKRPOSHTA_BEARER = os.getenv("UKRPOSHTA_BEARER", "")


def _headers():
    headers = {
        "Accept": "application/json",
    }

    if UKRPOSHTA_BEARER:
        headers["Authorization"] = f"Bearer {UKRPOSHTA_BEARER}"

    return headers


def _as_list(value):
    if not value:
        return []

    if isinstance(value, list):
        return value

    return [value]


def _clean_tag(tag: str):
    return str(tag).split("}")[-1]


def _entries_from_json(data):
    entries = data.get("Entries", {}).get("Entry", [])
    return _as_list(entries)


def _entries_from_xml(text):
    try:
        root = ET.fromstring(text)
    except Exception:
        return []

    entries = []

    for entry in root.iter():
        if _clean_tag(entry.tag) != "Entry":
            continue

        item = {}

        for child in list(entry):
            item[_clean_tag(child.tag)] = child.text

        entries.append(item)

    return entries


def _request_entries(endpoint: str, params: dict):
    url = f"{UKRPOSHTA_ADDRESS_API_URL}/{endpoint}"

    clean_params = {
        key: value
        for key, value in params.items()
        if value not in [None, ""]
    }

    try:
        response = requests.get(
            url,
            params=clean_params,
            headers=_headers(),
            timeout=20,
        )

        try:
            data = response.json()
            return _entries_from_json(data)
        except Exception:
            return _entries_from_xml(response.text)

    except Exception as error:
        print("Ukrposhta API error:", error)
        return []


def _normalize_city_name(value: str):
    return (
        str(value or "")
        .lower()
        .replace("м.", "")
        .replace("с.", "")
        .replace("смт.", "")
        .strip()
    )


def search_ukrposhta_cities(city: str):
    if not city or len(city.strip()) < 2:
        return {
            "success": True,
            "count": 0,
            "cities": [],
            "errors": [],
        }

    city_query = city.strip()
    normalized_query = _normalize_city_name(city_query)

    entries = _request_entries(
        "get_city_by_region_id_and_district_id_and_city_ua",
        {
            "city_ua": city_query,
        },
    )

    cities = []

    for item in entries:
        city_name = item.get("CITY_UA") or item.get("CITY_NAME") or ""

        city_type = (
            item.get("SHORTCITYTYPE_UA")
            or item.get("CITYTYPE_UA")
            or item.get("CITYTYPE_NAME")
            or ""
        )

        region_name = item.get("REGION_UA") or item.get("REGION_NAME") or ""

        district_name = (
            item.get("DISTRICT_UA")
            or item.get("DISTRICT_NAME")
            or item.get("NEW_DISTRICT_NAME")
            or ""
        )

        if not city_name:
            continue

        normalized_name = _normalize_city_name(city_name)

        if normalized_query not in normalized_name:
            continue

        label_parts = []

        if city_type:
            label_parts.append(f"{city_type} {city_name}")
        else:
            label_parts.append(city_name)

        if district_name:
            label_parts.append(f"{district_name} р-н")

        if region_name:
            label_parts.append(f"{region_name} обл.")

        cities.append(
            {
                "id": item.get("CITY_ID") or "",
                "name": city_name,
                "type": city_type,
                "label": ", ".join(label_parts),
                "region_name": region_name,
                "district_name": district_name,
                "koatuu": item.get("CITY_KOATUU") or "",
                "katottg": item.get("CITY_KATOTTG") or "",
            }
        )

    cities = sorted(
        cities,
        key=lambda item: (
            0 if _normalize_city_name(item["name"]) == normalized_query else 1,
            0 if _normalize_city_name(item["name"]).startswith(normalized_query) else 1,
            item["name"],
        ),
    )

    return {
        "success": True,
        "count": len(cities),
        "cities": cities[:30],
        "errors": [],
    }


def get_ukrposhta_offices(
    city_id: str = "",
    city_koatuu: str = "",
    city_katottg: str = "",
):
    if not city_id and not city_koatuu and not city_katottg:
        return {
            "success": False,
            "count": 0,
            "offices": [],
            "errors": ["city_id, city_koatuu або city_katottg обов'язковий"],
        }

    entries = _request_entries(
        "get_postoffices_by_postcode_cityid_cityvpzid",
        {
            "city_id": city_id,
            "city_koatuu": city_koatuu,
            "city_katottg": city_katottg,
        },
    )

    offices = []

    for item in entries:
        lock_code = str(item.get("LOCK_CODE") or "")
        is_security = str(item.get("IS_SECURITY") or "")

        if lock_code and lock_code != "0":
            continue

        if is_security == "1":
            continue

        postcode = item.get("POSTCODE") or item.get("POSTINDEX") or ""

        postoffice_name_raw = item.get("POSTOFFICE_UA") or ""
        postoffice_name = postoffice_name_raw.strip()

        if postcode and postoffice_name.startswith(postcode):
            postoffice_name = postoffice_name[len(postcode):].strip(" —-–,:")

        city_name = item.get("CITY_UA_VPZ") or item.get("CITY_UA") or ""
        street = item.get("STREET_UA_VPZ") or ""
        house_number = item.get("HOUSENUMBER") or ""

        address_parts = []

        if city_name:
            address_parts.append(city_name)

        if street:
            if house_number:
                address_parts.append(f"{street}, {house_number}")
            else:
                address_parts.append(street)

        address = ", ".join(address_parts)

        if postcode and address:
            description = f"{postcode} — {address}"
        elif postcode and postoffice_name:
            description = f"{postcode} — {postoffice_name}"
        elif postcode:
            description = postcode
        else:
            description = postoffice_name or address or "Відділення Укрпошти"

        address_parts = []

        if city_name:
            address_parts.append(city_name)

        if street:
            if house_number:
                address_parts.append(f"{street}, {house_number}")
            else:
                address_parts.append(street)

        address = ", ".join(address_parts)

        if postcode and postoffice_name and address:
            description = f"{postcode} — {postoffice_name}, {address}"
        elif postcode and postoffice_name:
            description = f"{postcode} — {postoffice_name}"
        elif postcode:
            description = postcode
        else:
            description = postoffice_name or address or "Відділення Укрпошти"

        offices.append(
            {
                "id": item.get("POSTOFFICE_ID") or postcode,
                "postcode": postcode,
                "name": postoffice_name,
                "address": address,
                "description": description,
                "type": item.get("TYPE_LONG") or item.get("TYPE_ACRONYM") or "",
                "city": city_name,
                "phone": item.get("PHONE") or "",
                "latitude": item.get("LATTITUDE") or "",
                "longitude": item.get("LONGITUDE") or "",
            }
        )

    offices = sorted(offices, key=lambda item: item["postcode"])

    return {
        "success": True,
        "count": len(offices),
        "offices": offices,
        "errors": [],
    }
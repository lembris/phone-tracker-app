"""
Legitimate OSINT intelligence helpers for educational demos.
No live tracking, wiretapping, or carrier intrusion.
"""

import json
import os
import re
import urllib.parse
import urllib.request

import phonenumbers
from phonenumbers import geocoder


# Common TAC prefixes (Type Allocation Code = first 8 IMEI digits)
# Source: public GSMA allocation data / manufacturer specs (educational subset)
TAC_DATABASE = {
    "35332510": {"brand": "Apple", "model": "iPhone 13"},
    "35391107": {"brand": "Apple", "model": "iPhone 14 Pro"},
    "35693803": {"brand": "Samsung", "model": "Galaxy S21"},
    "35260911": {"brand": "Samsung", "model": "Galaxy A52"},
    "86740004": {"brand": "Huawei", "model": "P30 Pro"},
    "86146004": {"brand": "Xiaomi", "model": "Redmi Note 10"},
    "35428009": {"brand": "Google", "model": "Pixel 6"},
    "35982710": {"brand": "OnePlus", "model": "OnePlus 9"},
    "35405811": {"brand": "Nokia", "model": "Nokia G50"},
    "35288807": {"brand": "Sony", "model": "Xperia 1 III"},
    "86892803": {"brand": "Oppo", "model": "Find X3"},
    "86970604": {"brand": "Vivo", "model": "Vivo V21"},
    "35699606": {"brand": "Motorola", "model": "Moto G Power"},
    "35407114": {"brand": "Apple", "model": "iPhone 12"},
    "35397810": {"brand": "Apple", "model": "iPhone 11"},
    "35925711": {"brand": "Samsung", "model": "Galaxy S22"},
    "35403811": {"brand": "Tecno", "model": "Spark 8"},
    "86803104": {"brand": "Infinix", "model": "Hot 11"},
    "35488509": {"brand": "Realme", "model": "Realme 8"},
    "35784109": {"brand": "Samsung", "model": "Galaxy S23 Ultra"},
    "35260912": {"brand": "Samsung", "model": "Galaxy S23"},
    "35194045": {"brand": "Samsung", "model": "Galaxy S24 Ultra"},
    "35394711": {"brand": "Apple", "model": "iPhone 15 Pro"},
    "35420257": {"brand": "Apple", "model": "iPhone 15"},
    "86898803": {"brand": "Xiaomi", "model": "Redmi Note 13"},
    "86102204": {"brand": "Xiaomi", "model": "Poco X5"},
}


def luhn_check(digits: str) -> bool:
    """Validate IMEI check digit (Luhn algorithm)."""
    total = 0
    for i, d in enumerate(reversed(digits)):
        n = int(d)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def analyze_imei(imei_raw: str) -> dict:
    """Decode IMEI: format check, Luhn validation, TAC device lookup."""
    imei = re.sub(r"\D", "", imei_raw.strip())
    result = {
        "raw": imei_raw.strip(),
        "imei": imei,
        "valid_format": len(imei) == 15 and imei.isdigit(),
        "luhn_valid": False,
        "tac": imei[:8] if len(imei) >= 8 else imei,
        "serial": imei[8:14] if len(imei) >= 14 else "",
        "check_digit": imei[14] if len(imei) == 15 else "",
        "brand": "UNKNOWN",
        "model": "UNKNOWN",
        "device_known": False,
        "location_note": "IMEI identifies DEVICE only - not GPS position",
        "live_location": "BLOCKED — requires carrier + warrant",
    }

    if result["valid_format"]:
        result["luhn_valid"] = luhn_check(imei)

    tac_info = TAC_DATABASE.get(result["tac"])
    if tac_info:
        result["brand"] = tac_info["brand"]
        result["model"] = tac_info["model"]
        result["device_known"] = True
    else:
        result["model"] = "Not in local TAC database"
        result["lookup_hint"] = (
            f"TAC {result['tac']} is valid but not in our bundled list "
            f"({len(TAC_DATABASE)} devices). GSMA registry has 250,000+."
        )

    result["valid"] = result["valid_format"] and result["luhn_valid"]
    return result


def assess_location_confidence(parsed_number, region_description: str, iso: str) -> dict:
    """
    Rate how precise OSINT location can be from a phone number alone.
    Live GPS is never available through public data.
    """
    region = (region_description or "").strip()
    country_names = set()
    if iso and iso != "XX":
        try:
            import pycountry
            c = pycountry.countries.get(alpha_2=iso)
            if c:
                country_names.add(c.name.lower())
                if hasattr(c, "official_name") and c.official_name:
                    country_names.add(c.official_name.lower())
        except ImportError:
            pass

    region_lower = region.lower()
    is_country_only = (
        not region
        or region_lower in country_names
        or region_lower == "unknown"
    )

    # Some numbers return city/state — more specific than country
    if is_country_only:
        return {
            "level": 1,
            "label": "LOW - COUNTRY/REGION ESTIMATE",
            "accuracy": "~100-500 km radius",
            "source": "ITU numbering plan + libphonenumber geocoder",
            "live_gps": False,
            "bar_pct": 25,
            "color": "#ffaa00",
            "detail": (
                "Number prefix maps to a country/region. "
                "This is NOT the phone's current position."
            ),
        }

    return {
        "level": 2,
        "label": "MEDIUM - AREA/CITY ESTIMATE",
        "accuracy": "~10-100 km radius",
        "source": "Numbering plan area code assignment",
        "live_gps": False,
        "bar_pct": 45,
        "color": "#ffaa00",
        "detail": (
            f"Area hint: {region}. Still registration geography, "
            "not real-time GPS. Subscriber may be anywhere."
        ),
    }


def geocode_region(description: str, iso: str = ""):
    """Resolve region name to coordinates via OpenStreetMap Nominatim (public API)."""
    if not description or description.upper() == "UNKNOWN":
        return None

    query = description
    if iso and iso != "XX":
        query = f"{description}, {iso}"

    try:
        params = urllib.parse.urlencode({
            "q": query,
            "format": "json",
            "limit": 1,
        })
        url = f"https://nominatim.openstreetmap.org/search?{params}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "GhostTrace-Educational-Demo/1.0"},
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())

        if not data:
            return None

        hit = data[0]
        return {
            "lat": float(hit["lat"]),
            "lng": float(hit["lon"]),
            "display": hit.get("display_name", query),
            "source": "OpenStreetMap Nominatim (OSINT geocode)",
        }
    except (OSError, ValueError, KeyError, json.JSONDecodeError):
        return None


def get_region_description(parsed_number) -> str:
    """Best available geographic description from phone number."""
    return geocoder.description_for_number(parsed_number, "en") or "Unknown"


LEGAL_INTERCEPT_STEPS = [
    {
        "phase": "01",
        "title": "OSINT RECONNAISSANCE",
        "status": "AVAILABLE (THIS TOOL)",
        "detail": (
            "Public data: country, carrier, line type, timezone, IMEI device model. "
            "No subscriber identity. No live location."
        ),
        "legal": "Legal — public numbering databases",
    },
    {
        "phase": "02",
        "title": "INCIDENT REPORT",
        "status": "REQUIRED",
        "detail": (
            "Victim files police report with phone number, IMEI, incident details. "
            "Creates official case record."
        ),
        "legal": "Legal — standard procedure",
    },
    {
        "phase": "03",
        "title": "COURT ORDER / WARRANT",
        "status": "REQUIRED FOR LIVE DATA",
        "detail": (
            "Judge issues warrant for subscriber records, CDR, or real-time "
            "location. Without this, carriers must refuse."
        ),
        "legal": "Legal — judicial oversight",
    },
    {
        "phase": "04",
        "title": "CARRIER LAWFUL INTERCEPT",
        "status": "CARRIER-ONLY",
        "detail": (
            "Mobile operator queries HLR/VLR, cell towers (MCC/MNC/LAC/CID). "
            "Returns triangulated position to authorized agency."
        ),
        "legal": "Legal — with warrant only",
    },
    {
        "phase": "05",
        "title": "WIRETAP / CDR ACCESS",
        "status": "STRICTLY CONTROLLED",
        "detail": (
            "Call metadata or content interception requires separate explicit "
            "authorization. Never available via phone number OSINT."
        ),
        "legal": "Legal — highest scrutiny",
    },
    {
        "phase": "06",
        "title": "ILLEGAL METHODS",
        "status": "BLOCKED IN DEMO",
        "detail": (
            "SS7 exploitation, IMSI catchers, spyware, unauthorized wiretaps — "
            "criminal offenses. This demo does NOT implement these."
        ),
        "legal": "ILLEGAL — do not attempt",
    },
]

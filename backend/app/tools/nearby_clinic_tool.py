"""
nearby_clinic_tool.py
Optimized clinic/hospital finder based on the Colab notebook approach:
  1. Geocode location name via Nominatim (OSM) if no GPS coords provided
  2. Query Overpass API for hospitals + clinics + healthcare:doctor within 10km
  3. Compute geodesic distances, sort by proximity, return top 10
  4. Optionally detect specialist type from user symptom/query using Groq
"""

import math
import requests
from app.mcp.router import ToolOutput
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_HEADERS = {"User-Agent": "VoiceMedicalAssistant/1.0"}


# ── Haversine distance (km) ───────────────────────────────────────────────────

def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ── Geocode location name → (lat, lon) via Nominatim ─────────────────────────

def _geocode(location_name: str) -> tuple[float, float] | None:
    try:
        resp = requests.get(
            NOMINATIM_URL,
            params={"q": location_name, "format": "json", "limit": 1},
            headers=NOMINATIM_HEADERS,
            timeout=10,
        )
        data = resp.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        logger.warning(f"[ClinicTool] Geocode failed for '{location_name}': {e}")
    return None


# ── Overpass API Query (same approach as Colab) ───────────────────────────────

def _search_overpass(lat: float, lon: float, radius_m: int = 10000) -> list[dict]:
    """
    Query Overpass API for hospitals, clinics, and healthcare:doctor
    within radius_m metres of (lat, lon).
    Returns a list of raw OSM elements.
    """
    query = f"""
    [out:json][timeout:30];
    (
      node["amenity"="hospital"](around:{radius_m},{lat},{lon});
      way["amenity"="hospital"](around:{radius_m},{lat},{lon});
      relation["amenity"="hospital"](around:{radius_m},{lat},{lon});

      node["amenity"="clinic"](around:{radius_m},{lat},{lon});
      way["amenity"="clinic"](around:{radius_m},{lat},{lon});
      relation["amenity"="clinic"](around:{radius_m},{lat},{lon});

      node["healthcare"="doctor"](around:{radius_m},{lat},{lon});
      way["healthcare"="doctor"](around:{radius_m},{lat},{lon});
      relation["healthcare"="doctor"](around:{radius_m},{lat},{lon});
    );
    out center;
    """
    try:
        resp = requests.get(
            OVERPASS_URL,
            params={"data": query},
            timeout=35,
        )
        if resp.status_code != 200:
            logger.error(f"[ClinicTool] Overpass API error: {resp.status_code}")
            return []
        elements = resp.json().get("elements", [])
        logger.info(f"[ClinicTool] Overpass returned {len(elements)} raw elements")
        return elements
    except Exception as e:
        logger.error(f"[ClinicTool] Overpass request failed: {e}")
        return []


# ── Parse Overpass elements → clean clinic list ───────────────────────────────

def _parse_elements(elements: list[dict], user_lat: float, user_lon: float) -> list[dict]:
    """
    Extract name, phone, coordinates from Overpass elements.
    Compute distance from user, sort by distance, deduplicate, return top 10.
    """
    hospital_list = []
    seen = set()

    for place in elements:
        tags = place.get("tags", {})
        name = tags.get("name", "").strip()
        if not name or name in seen:
            continue
        seen.add(name)

        # Get coordinates (nodes have lat/lon directly; ways/relations have center)
        if "lat" in place:
            plat = float(place["lat"])
            plon = float(place["lon"])
        elif "center" in place:
            plat = float(place["center"]["lat"])
            plon = float(place["center"]["lon"])
        else:
            continue

        phone = tags.get("phone") or tags.get("contact:phone") or "N/A"
        opening_hours = tags.get("opening_hours", "")
        website = tags.get("website") or tags.get("contact:website") or ""
        amenity = tags.get("amenity") or tags.get("healthcare") or "facility"
        distance_km = _haversine(user_lat, user_lon, plat, plon)

        hospital_list.append({
            "name": name,
            "phone": phone,
            "lat": plat,
            "lng": plon,
            "distance_km": round(distance_km, 2),
            "type": amenity,
            "opening_hours": opening_hours,
            "website": website,
            "address": tags.get("addr:full")
                       or f"{tags.get('addr:street', '')} {tags.get('addr:city', '')}".strip()
                       or "See map for location",
        })

    # Sort by distance and return top 10
    hospital_list.sort(key=lambda x: x["distance_km"])
    return hospital_list[:10]


# ── Main Entry Point ──────────────────────────────────────────────────────────

def find_nearby_clinics(entities: dict) -> ToolOutput:
    """
    Full pipeline:
      GPS coords or geocode → Overpass API search → parse + sort → ToolOutput with map_data
    """
    exact_lat = entities.get("lat")
    exact_lng = entities.get("lng")
    location_name = entities.get("location") or settings.default_location

    try:
        # ── Step 1: Resolve coordinates ───────────────────────────────────────
        if exact_lat and exact_lng:
            lat = float(exact_lat)
            lon = float(exact_lng)
            display_location = f"your current location"
            logger.info(f"[ClinicTool] Using exact GPS: lat={lat}, lon={lon}")
        else:
            coords = _geocode(location_name)
            if not coords:
                # Fallback to default city
                logger.warning(f"[ClinicTool] Geocode failed for '{location_name}', trying default: {settings.default_location}")
                coords = _geocode(settings.default_location)
                location_name = settings.default_location

            if not coords:
                raise ValueError(f"Cannot resolve location: {location_name}")

            lat, lon = coords
            display_location = location_name
            logger.info(f"[ClinicTool] Geocoded '{location_name}' → lat={lat}, lon={lon}")

        # ── Step 2: Query Overpass API ────────────────────────────────────────
        raw_elements = _search_overpass(lat, lon, radius_m=10000)

        # ── Step 3: Parse and rank by distance ───────────────────────────────
        clinics = _parse_elements(raw_elements, lat, lon)
        logger.info(f"[ClinicTool] {len(clinics)} clinics found near '{display_location}'")

        # ── Step 4: Build result + map_data ──────────────────────────────────
        map_data = {
            "type": "clinics",
            "search_location": display_location,
            "center_lat": lat,
            "center_lng": lon,
            "locations": clinics,
        }

        result = {
            "location": display_location,
            "clinics": clinics,
            "count": len(clinics),
            "success": True,
        }

        return ToolOutput(
            tool_name="nearby_clinic",
            result=result,
            map_data=map_data,
            success=True,
            confidence=0.95 if clinics else 0.5,
            error=None,
        )

    except Exception as e:
        logger.error(f"[ClinicTool] Pipeline error for '{location_name}': {e}")
        return ToolOutput(
            tool_name="nearby_clinic",
            result={
                "message": f"Unable to find clinics near '{location_name}' at this time.",
                "location": location_name,
                "clinics": [],
                "count": 0,
                "success": False,
            },
            success=False,
            confidence=0.0,
            error=str(e),
        )

import httpx
from app.mcp.router import ToolOutput
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def find_nearby_clinics(entities: dict) -> ToolOutput:
    """Find top 10 nearest clinics/hospitals using Free Nominatim (OpenStreetMap) API.
    
    If entities contain 'lat'/'lng' (from browser geolocation), skip geocoding
    and use exact coordinates for maximum precision.
    Otherwise, fall back to location name → geocode → search.
    """
    headers = {"User-Agent": "VoiceMedicalAssistant/1.0"}

    # Check if exact GPS coords were passed from frontend
    exact_lat = entities.get("lat")
    exact_lng = entities.get("lng")
    location_name = entities.get("location") or settings.default_location

    try:
        with httpx.Client(timeout=15) as client:

            if exact_lat and exact_lng:
                # Use exact GPS coordinates directly — no geocoding needed
                lat = float(exact_lat)
                lng = float(exact_lng)
                location_name = f"your location ({lat:.4f}, {lng:.4f})"
                logger.info(f"Using exact GPS coords: lat={lat}, lng={lng}")
            else:
                # Geocode the location name → lat/lng
                geo_params = {"q": location_name, "format": "json", "limit": 1}
                geo_response = client.get(
                    "https://nominatim.openstreetmap.org/search",
                    params=geo_params,
                    headers=headers,
                )
                geo_response.raise_for_status()
                geo_data = geo_response.json()

                # Fallback to default city when location is vague (e.g. "nearby clinic")
                if not geo_data:
                    logger.warning(
                        f"Geocode failed for '{location_name}', falling back to '{settings.default_location}'"
                    )
                    location_name = settings.default_location
                    geo_params["q"] = location_name
                    geo_response = client.get(
                        "https://nominatim.openstreetmap.org/search",
                        params=geo_params,
                        headers=headers,
                    )
                    geo_response.raise_for_status()
                    geo_data = geo_response.json()

                if not geo_data:
                    raise ValueError(f"Could not geocode location: {location_name}")

                lat = float(geo_data[0]["lat"])
                lng = float(geo_data[0]["lon"])

            # Search for top 10 hospitals + clinics near the coordinates via Nominatim
            clinics = []
            for amenity in ["hospital", "clinic"]:
                if len(clinics) >= 10:
                    break
                search_params = {
                    "amenity": amenity,
                    "format": "json",
                    "limit": 10,
                    "lat": lat,
                    "lon": lng,
                    "addressdetails": 1,
                }
                resp = client.get(
                    "https://nominatim.openstreetmap.org/search",
                    params=search_params,
                    headers=headers,
                )
                resp.raise_for_status()
                results = resp.json()

                for place in results:
                    if len(clinics) >= 10:
                        break
                    name = place.get("name", "").strip()
                    if not name:
                        continue
                    addr = place.get("display_name", "Location on Map")
                    clinics.append({
                        "name": name,
                        "address": addr,
                        "lat": float(place["lat"]),
                        "lng": float(place["lon"]),
                    })

        map_data = {
            "type": "clinics",
            "search_location": location_name,
            "center_lat": lat,
            "center_lng": lng,
            "locations": clinics,
        }

        logger.info(f"Found {len(clinics)} clinics near '{location_name}'")

        return ToolOutput(
            tool_name="nearby_clinic",
            result={
                "location": location_name,
                "clinics": clinics,
                "count": len(clinics),
            },
            map_data=map_data,
        )

    except Exception as e:
        logger.error(f"Clinic search error for '{location_name}': {e}")
        return ToolOutput(
            tool_name="nearby_clinic",
            result={"message": f"Unable to find clinics near '{location_name}'."},
            error=str(e),
        )

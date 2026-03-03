import httpx
from app.mcp.router import ToolOutput
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def find_nearby_clinics(entities: dict) -> ToolOutput:
    """Find nearby clinics/hospitals using Google Maps Places API."""
    location = entities.get("location") or "Chennai"

    try:
        # Step 1: Geocode location string → lat/lng
        geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
        geo_params = {"address": location, "key": settings.maps_api_key}

        with httpx.Client(timeout=10) as client:
            geo_response = client.get(geocode_url, params=geo_params)
            geo_response.raise_for_status()
            geo_data = geo_response.json()

        geo_results = geo_data.get("results", [])
        if not geo_results:
            raise ValueError(f"Could not geocode location: {location}")

        loc = geo_results[0]["geometry"]["location"]
        lat, lng = loc["lat"], loc["lng"]

        # Step 2: Nearby search for clinics/hospitals
        places_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        places_params = {
            "location": f"{lat},{lng}",
            "radius": 5000,
            "type": "hospital",
            "key": settings.maps_api_key,
        }
        places_response = client.get(places_url, params=places_params)
        places_response.raise_for_status()
        places_data = places_response.json()

        clinics = []
        for place in places_data.get("results", [])[:5]:
            geometry = place.get("geometry", {}).get("location", {})
            clinics.append({
                "name": place.get("name", "Unknown Clinic"),
                "address": place.get("vicinity", ""),
                "lat": geometry.get("lat"),
                "lng": geometry.get("lng"),
                "rating": place.get("rating"),
                "open_now": place.get("opening_hours", {}).get("open_now"),
            })

        map_data = {
            "type": "clinics",
            "search_location": location,
            "center_lat": lat,
            "center_lng": lng,
            "locations": clinics,
        }

        return ToolOutput(
            tool_name="nearby_clinic",
            result={"location": location, "clinics": clinics, "count": len(clinics)},
            map_data=map_data,
        )

    except Exception as e:
        logger.error(f"Clinic search error for '{location}': {e}")
        return ToolOutput(
            tool_name="nearby_clinic",
            result={"message": f"Unable to find clinics near '{location}'."},
            error=str(e),
        )

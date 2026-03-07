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

            # ── Haversine Distance Helper ─────────────────────────────
            import math
            def calculate_distance(lat1, lon1, lat2, lon2):
                R = 6371.0 # Earth radius in kilometers
                dlat = math.radians(lat2 - lat1)
                dlon = math.radians(lon2 - lon1)
                a = (math.sin(dlat / 2)**2 
                     + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2)
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                return R * c

            # Search for hospitals + clinics near the coordinates via Nominatim
            clinics_list = []
            for amenity in ["hospital", "clinic"]:
                search_params = {
                    "amenity": amenity,
                    "format": "json",
                    "limit": 15,
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
                    name = place.get("name", "").strip()
                    if not name:
                        continue
                        
                    p_lat = float(place["lat"])
                    p_lng = float(place["lon"])
                    dist_km = calculate_distance(lat, lng, p_lat, p_lng)
                    
                    addr = place.get("display_name", "Location on Map")
                    clinics_list.append({
                        "name": name,
                        "address": addr,
                        "lat": p_lat,
                        "lng": p_lng,
                        "distance_km": round(dist_km, 1)
                    })
            
            # Sort by distance and deduplicate by name, keeping exactly top 5
            clinics_list.sort(key=lambda x: x["distance_km"])
            seen_names = set()
            clinics = []
            for c in clinics_list:
                if c["name"] not in seen_names and len(clinics) < 5:
                    seen_names.add(c["name"])
                    clinics.append(c)

        result = {
            "location": location_name,
            "clinics": clinics,
            "count": len(clinics),
            "success": True
        }

        map_data = {
            "type": "clinics",
            "search_location": location_name,
            "center_lat": lat,
            "center_lng": lng,
            "locations": clinics,
        }

        result = {
            "location": location_name,
            "clinics": clinics,
            "count": len(clinics),
            "success": True
        }

        logger.info(f"Found {len(clinics)} clinics near '{location_name}'")

        return ToolOutput(
            tool_name="nearby_clinic",
            result=result,
            map_data=map_data,
            success=True,
            confidence=0.95 if clinics else 0.5,
            error=None
        )

    except Exception as e:
        logger.error(f"Clinic search error for '{location_name}': {e}")
        return ToolOutput(
            tool_name="nearby_clinic",
            result={
                "message": f"Unable to find clinics near '{location_name}' at this time.",
                "location": location_name,
                "clinics": [],
                "count": 0,
                "success": False
            },
            success=False,
            confidence=0.0,
            error=str(e),
        )

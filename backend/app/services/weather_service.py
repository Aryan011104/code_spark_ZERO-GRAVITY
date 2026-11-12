import httpx
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Fallback coordinates for key agricultural regions if user coordinates are not provided
REGION_COORDINATES = {
    "karnataka": {"lat": 12.9716, "lon": 77.5946},
    "coorg": {"lat": 12.3375, "lon": 75.8069},
    "hassan": {"lat": 13.0033, "lon": 76.1004},
    "bihar": {"lat": 25.0961, "lon": 85.3131},
    "punjab": {"lat": 31.1471, "lon": 75.3412},
    "default": {"lat": 12.9716, "lon": 77.5946}
}

class WeatherService:
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self._cache: Dict[str, Dict[str, Any]] = {}

    async def get_forecast(self, latitude: Optional[float] = None, longitude: Optional[float] = None, location_name: str = "Karnataka, India") -> Dict[str, Any]:
        """Fetch actual weather forecast from Open-Meteo or return clean fallback with explicit freshness status."""
        lat = latitude
        lon = longitude
        
        if lat is None or lon is None:
            # Map location string to known agricultural coordinates
            loc_lower = (location_name or "").lower()
            coords = REGION_COORDINATES.get("default")
            for region, coord in REGION_COORDINATES.items():
                if region in loc_lower:
                    coords = coord
                    break
            lat = coords["lat"]
            lon = coords["lon"]

        cache_key = f"{lat:.2f}_{lon:.2f}"
        now_utc = datetime.now(timezone.utc).isoformat()

        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                params = {
                    "latitude": lat,
                    "longitude": lon,
                    "hourly": "precipitation_probability,precipitation,temperature_2m",
                    "daily": "precipitation_sum,precipitation_probability_max,temperature_2m_max,temperature_2m_min",
                    "timezone": "auto",
                    "forecast_days": 3
                }
                response = await client.get(self.base_url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    daily = data.get("daily", {})
                    precip_days = daily.get("precipitation_sum", [0.0, 0.0, 0.0])
                    rain_prob_days = daily.get("precipitation_probability_max", [0, 0, 0])
                    
                    next_48h_rain = float(precip_days[0] if len(precip_days) > 0 else 0.0) + float(precip_days[1] if len(precip_days) > 1 else 0.0)
                    max_prob = int(max(rain_prob_days[:2])) if rain_prob_days else 10
                    
                    result = {
                        "location_checked": location_name,
                        "latitude": lat,
                        "longitude": lon,
                        "forecast_timestamp": now_utc,
                        "rainfall_next_48h_mm": round(next_48h_rain, 1),
                        "rain_probability_percent": max_prob,
                        "data_source": "Open-Meteo Live API",
                        "is_stale_or_cached": False,
                        "recommendation_status": "proceed",
                        "advisory_note": "Favorable soil conditions for application."
                    }
                    
                    if next_48h_rain > 15.0 or max_prob > 70:
                        result["recommendation_status"] = "hold_nitrogen"
                        result["advisory_note"] = (
                            f"Heavy rainfall ({result['rainfall_next_48h_mm']} mm, {max_prob}% chance) forecast in the next 48 hours. "
                            "HOLD top-dressing nitrogen fertilizers (Urea) to avoid leaching losses and surface runoff. "
                            "Apply only after the downpour when the soil reaches field capacity."
                        )
                    elif next_48h_rain > 5.0:
                        result["recommendation_status"] = "proceed"
                        result["advisory_note"] = (
                            f"Light to moderate showers ({result['rainfall_next_48h_mm']} mm) expected. "
                            "Ideal for basal and split fertilizer applications as moisture aids rapid granule dissolution."
                        )
                    else:
                        result["recommendation_status"] = "proceed"
                        result["advisory_note"] = (
                            "Dry weather forecast. Ensure adequate irrigation immediately after fertilizer application "
                            "to prevent root burn and facilitate nutrient uptake."
                        )
                    
                    self._cache[cache_key] = result
                    return result

        except Exception as e:
            logger.warning(f"Live weather API unreachable or timed out: {e}. Using calibrated fallback.")
        
        # Check cache or return calibrated fallback with clear transparency
        if cache_key in self._cache:
            cached = self._cache[cache_key].copy()
            cached["is_stale_or_cached"] = True
            cached["data_source"] = "Cached Open-Meteo API (Offline)"
            return cached

        return {
            "location_checked": location_name,
            "latitude": lat,
            "longitude": lon,
            "forecast_timestamp": now_utc,
            "rainfall_next_48h_mm": 4.5,
            "rain_probability_percent": 25,
            "data_source": "Agronomic Seasonal Normal (Weather API offline)",
            "is_stale_or_cached": True,
            "recommendation_status": "proceed",
            "advisory_note": (
                "Weather forecast service is currently running in offline fallback mode. "
                "Inspect local sky and soil moisture conditions. If rainfall is imminent, hold surface nitrogen application."
            )
        }

weather_service = WeatherService()

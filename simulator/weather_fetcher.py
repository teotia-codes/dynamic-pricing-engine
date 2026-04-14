import requests
from core.db import get_connection, release_connection
from backend.app.logger import logger

# Map your region_name from DB -> (latitude, longitude, city)
REGION_COORDS = {
    "Connaught Place": (28.6315, 77.2167, "Delhi"),
    "Sector 18": (28.5708, 77.3260, "Noida"),
    "Cyber Hub": (28.4959, 77.0890, "Gurgaon"),
    "HSR Layout": (12.9116, 77.6474, "Bengaluru"),
    "Andheri West": (19.1364, 72.8276, "Mumbai"),
}


def map_weather_code(weather_code: int) -> str:
    """
    Convert Open-Meteo weather codes into simplified pricing categories.
    """
    if weather_code in [0, 1]:
        return "Clear"
    elif weather_code in [2, 3]:
        return "Cloudy"
    elif weather_code in [45, 48]:
        return "Fog"
    elif weather_code in [51, 53, 55]:
        return "Drizzle"
    elif weather_code in [61, 63]:
        return "Rain"
    elif weather_code in [65, 80, 81, 82]:
        return "Heavy Rain"
    elif weather_code in [95, 96, 99]:
        return "Thunderstorm"
    else:
        return "Clear"


def fetch_weather():
    conn = get_connection()

    try:
        cur = conn.cursor()

        # Read actual regions from DB so your code stays dynamic
        cur.execute("SELECT region_id, region_name FROM regions ORDER BY region_id;")
        regions = cur.fetchall()

        for region_id, region_name in regions:
            if region_name not in REGION_COORDS:
                logger.warning(f"No weather coordinates configured for region={region_name}")
                continue

            lat, lon, city = REGION_COORDS[region_name]

            url = (
                f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={lat}&longitude={lon}"
                f"&current=temperature_2m,precipitation,weather_code"
            )

            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()

                current = data.get("current", {})
                temperature_c = float(current.get("temperature_2m", 25.0))
                rain_mm = float(current.get("precipitation", 0.0))
                weather_code = int(current.get("weather_code", 0))

                weather_condition = map_weather_code(weather_code)

                cur.execute(
                    """
                    INSERT INTO weather_events (
                        region_id,
                        temperature_c,
                        rain_mm,
                        weather_condition
                    )
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        region_id,
                        temperature_c,
                        rain_mm,
                        weather_condition,
                    ),
                )

                logger.info(
                    f"Weather inserted | region={region_name} | city={city} | "
                    f"condition={weather_condition} | temp={temperature_c}C | rain={rain_mm}mm"
                )

            except requests.RequestException as e:
                logger.warning(
                    f"Weather API request failed | region={region_name} | city={city} | error={e}"
                )
            except Exception as e:
                logger.exception(
                    f"Unexpected weather processing error | region={region_name} | city={city} | error={e}"
                )

        conn.commit()
        cur.close()

    finally:
        release_connection(conn)


if __name__ == "__main__":
    fetch_weather()
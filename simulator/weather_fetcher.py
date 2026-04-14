import requests
from simulator.db import get_connection
# region_id -> (lat, lon, label)
REGION_COORDS = {
    1: (28.6315, 77.2167, "Connaught Place, Delhi"),
    2: (28.5708, 77.3260, "Sector 18, Noida"),
    3: (28.4959, 77.0890, "Cyber Hub, Gurgaon"),
    4: (12.9116, 77.6474, "HSR Layout, Bengaluru"),
    5: (19.1364, 72.8276, "Andheri West, Mumbai"),
}

def map_weather_code(weather_code):
    # Open-Meteo weather code mapping (simplified)
    if weather_code in [0, 1]:
        return "Clear"
    elif weather_code in [2, 3]:
        return "Cloudy"
    elif weather_code in [51, 53, 55, 61, 63, 65]:
        return "Rain"
    elif weather_code in [66, 67, 80, 81, 82]:
        return "Heavy Rain"
    elif weather_code in [95, 96, 99]:
        return "Storm"
    else:
        return "Unknown"

def fetch_weather():
    conn = get_connection()
    cur = conn.cursor()

    for region_id, (lat, lon, label) in REGION_COORDS.items():
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,precipitation,weather_code"
        )

        try:
            response = requests.get(url, timeout=10)
            data = response.json()

            current = data.get("current", {})
            temperature_c = current.get("temperature_2m", 25.0)
            rain_mm = current.get("precipitation", 0.0)
            weather_code = current.get("weather_code", 0)

            weather_condition = map_weather_code(weather_code)

            cur.execute("""
                INSERT INTO weather_events (
                    region_id,
                    temperature_c,
                    rain_mm,
                    weather_condition
                )
                VALUES (%s, %s, %s, %s)
            """, (
                region_id,
                temperature_c,
                rain_mm,
                weather_condition
            ))

            print(f"✅ Weather inserted for {label}: {weather_condition}, {temperature_c}°C")

        except Exception as e:
            print(f"❌ Failed weather fetch for {label}: {e}")

    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    fetch_weather()
import time
import requests
from core.db import get_connection, release_connection

# region_id -> (lat, lon, label)
REGION_COORDS = {
    1: (28.6315, 77.2167, "Connaught Place, Delhi"),
    2: (28.5708, 77.3260, "Sector 18, Noida"),
    3: (28.4959, 77.0890, "Cyber Hub, Gurgaon"),
    4: (12.9116, 77.6474, "HSR Layout, Bengaluru"),
    5: (19.1364, 72.8276, "Andheri West, Mumbai"),
}

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2

def map_weather_code(weather_code):
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
    return "Unknown"


def log_ingestion_error(cur, source_name, region_id, error_message):
    cur.execute("""
        INSERT INTO ingestion_errors (
            source_name,
            region_id,
            error_message
        )
        VALUES (%s, %s, %s)
    """, (source_name, region_id, error_message))


def fetch_weather():
    conn = get_connection()

    try:
        cur = conn.cursor()

        for region_id, (lat, lon, label) in REGION_COORDS.items():
            url = (
                f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={lat}&longitude={lon}"
                f"&current=temperature_2m,precipitation,weather_code"
            )

            success = False

            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
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
                    success = True
                    break

                except Exception as e:
                    print(f"⚠️ Attempt {attempt}/{MAX_RETRIES} failed for {label}: {e}")

                    if attempt < MAX_RETRIES:
                        time.sleep(RETRY_DELAY_SECONDS)
                    else:
                        log_ingestion_error(
                            cur,
                            "weather_fetcher",
                            region_id,
                            str(e)
                        )
                        print(f"❌ Logged weather fetch failure for {label}")

            if not success:
                print(f"❌ Final failure for {label} after {MAX_RETRIES} attempts")

        conn.commit()
        cur.close()

    except Exception as e:
        print(f"❌ Error in fetch_weather: {e}")

    finally:
        release_connection(conn)

if __name__ == "__main__":
    fetch_weather()
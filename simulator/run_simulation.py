import time
from simulator.generate_orders import generate_orders
from simulator.generate_supply import generate_supply
from simulator.weather_fetcher import fetch_weather
from simulator.traffic_simulator import simulate_traffic
from simulator.store_load_simulator import simulate_store_load

def run_simulation():
    cycle = 1

    while True:
        print(f"\n🚀 Simulation cycle {cycle} started...")

        try:
            generate_orders()
            generate_supply()
            simulate_traffic()
            simulate_store_load()
            fetch_weather()

            print(f"✅ Simulation cycle {cycle} completed")
        except Exception as e:
            print(f"❌ Error in simulation cycle {cycle}: {e}")

        cycle += 1
        time.sleep(10)

if __name__ == "__main__":
    run_simulation()
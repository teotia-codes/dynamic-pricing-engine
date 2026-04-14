import time

from simulator.generate_orders import generate_orders
from simulator.generate_supply import generate_supply
from simulator.weather_fetcher import fetch_weather
from simulator.traffic_simulator import simulate_traffic
from simulator.store_load_simulator import simulate_store_load
from backend.app.logger import logger


def run_simulation():
    cycle = 1

    while True:
        logger.info("Simulation cycle %s started", cycle)

        try:
            generate_orders()
            generate_supply()
            simulate_traffic()
            simulate_store_load()
            fetch_weather()

            logger.info("Simulation cycle %s completed", cycle)
        except Exception:
            logger.exception("Error in simulation cycle %s", cycle)

        cycle += 1
        time.sleep(10)


if __name__ == "__main__":
    run_simulation()
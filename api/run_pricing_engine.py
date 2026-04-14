import time
from api.pricing_engine import calculate_prices
from backend.app.logger import logger


def run_pricing_engine():
    cycle = 1

    while True:
        logger.info("Pricing cycle %s started", cycle)

        try:
            calculate_prices()
            logger.info("Pricing cycle %s completed", cycle)
        except Exception:
            logger.exception("Error in pricing cycle %s", cycle)

        cycle += 1
        time.sleep(10)


if __name__ == "__main__":
    run_pricing_engine()
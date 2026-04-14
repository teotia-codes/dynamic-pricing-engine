import time
from api.pricing_engine import calculate_prices
def run_pricing_engine():
    cycle = 1

    while True:
        print(f"\n💰 Pricing cycle {cycle} started...")

        try:
            calculate_prices()
            print(f"✅ Pricing cycle {cycle} completed")
        except Exception as e:
            print(f"❌ Error in pricing cycle {cycle}: {e}")

        cycle += 1
        time.sleep(10)  # every 10 seconds

if __name__ == "__main__":
    run_pricing_engine()
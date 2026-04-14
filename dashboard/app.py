import time
import requests
import pandas as pd
import streamlit as st

API_BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Dynamic Pricing Dashboard",
    page_icon="💰",
    layout="wide"
)

# -----------------------------
# Helper Functions
# -----------------------------
def fetch_json(endpoint):
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=10)
        response.raise_for_status()
        return response.json(), None
    except Exception as e:
        return None, str(e)

def get_health():
    return fetch_json("/health")

def get_latest_prices():
    return fetch_json("/latest-prices")

def get_latest_prices_by_platform(platform):
    return fetch_json(f"/latest-prices/{platform}")

def get_top_surges(limit=10):
    return fetch_json(f"/top-surges?limit={limit}")

def get_history(platform, region, limit=20):
    region_encoded = region.replace(" ", "%20")
    return fetch_json(f"/history/{platform}/{region_encoded}?limit={limit}")

# -----------------------------
# Header
# -----------------------------
st.title("🚀 Real-Time Dynamic Pricing Dashboard")
st.caption("Swiggy / Zomato / Blinkit Style Delivery Pricing Engine")

# -----------------------------
# Sidebar Controls
# -----------------------------
st.sidebar.header("⚙️ Controls")

platform_filter = st.sidebar.selectbox(
    "Select Platform",
    ["All", "Swiggy", "Zomato", "Blinkit"]
)

auto_refresh = st.sidebar.checkbox("Auto Refresh (every 10 sec)", value=False)

history_platform = st.sidebar.selectbox(
    "History Platform",
    ["Swiggy", "Zomato", "Blinkit"]
)

history_region = st.sidebar.selectbox(
    "History Region",
    ["Connaught Place", "Sector 18", "Cyber Hub", "HSR Layout", "Andheri West"]
)

history_limit = st.sidebar.slider("History Rows", 5, 50, 20)

# -----------------------------
# Health Check
# -----------------------------
health_data, health_error = get_health()

col1, col2, col3 = st.columns(3)

if health_error:
    col1.error("API: DOWN")
    col2.error("DB: UNKNOWN")
    col3.error("Health Check Failed")
else:
    col1.success("API: RUNNING")
    col2.success("DB: CONNECTED")
    col3.info(f"DB Time: {health_data['db_time']}")

st.divider()

# -----------------------------
# Latest Prices Section
# -----------------------------
st.subheader("📊 Latest Dynamic Prices")

if platform_filter == "All":
    latest_data, latest_error = get_latest_prices()
else:
    latest_data, latest_error = get_latest_prices_by_platform(platform_filter)

if latest_error:
    st.error(f"Failed to fetch latest prices: {latest_error}")
    latest_df = pd.DataFrame()
else:
    latest_df = pd.DataFrame(latest_data["data"])

    if not latest_df.empty:
        # KPIs
        k1, k2, k3, k4 = st.columns(4)

        avg_fee = round(latest_df["final_fee"].mean(), 2)
        max_fee = round(latest_df["final_fee"].max(), 2)
        avg_ratio = round(latest_df["demand_supply_ratio"].mean(), 2)
        max_multiplier = round(latest_df["final_multiplier"].max(), 2)

        k1.metric("Average Final Fee", f"₹{avg_fee}")
        k2.metric("Highest Final Fee", f"₹{max_fee}")
        k3.metric("Avg Demand/Supply Ratio", avg_ratio)
        k4.metric("Max Surge Multiplier", f"{max_multiplier}x")

        st.dataframe(
            latest_df,
            use_container_width=True
        )
    else:
        st.warning("No latest pricing data found.")

st.divider()

# -----------------------------
# Top Surges Section
# -----------------------------
st.subheader("🔥 Top Surges Right Now")

top_data, top_error = get_top_surges(limit=10)

if top_error:
    st.error(f"Failed to fetch top surges: {top_error}")
    top_df = pd.DataFrame()
else:
    top_df = pd.DataFrame(top_data["data"])

    if not top_df.empty:
        st.dataframe(top_df, use_container_width=True)

        st.bar_chart(
            top_df.set_index("region")["final_fee"]
        )
    else:
        st.warning("No surge data available.")

st.divider()

# -----------------------------
# Price History Section
# -----------------------------
st.subheader("📈 Price History")

history_data, history_error = get_history(history_platform, history_region, history_limit)

if history_error:
    st.error(f"Failed to fetch history: {history_error}")
    history_df = pd.DataFrame()
else:
    history_df = pd.DataFrame(history_data["data"])

    if not history_df.empty:
        history_df = history_df.sort_values("calculated_at")

        h1, h2 = st.columns(2)

        with h1:
            st.write(f"### {history_platform} - {history_region}")
            st.dataframe(history_df, use_container_width=True)

        with h2:
            chart_df = history_df[["calculated_at", "final_fee"]].copy()
            chart_df = chart_df.set_index("calculated_at")

            st.line_chart(chart_df)

    else:
        st.warning("No history data found for selected platform/region.")

st.divider()

# -----------------------------
# Platform Comparison
# -----------------------------
st.subheader("⚖️ Platform Comparison (Average Current Fee)")

if not latest_df.empty:
    comparison_df = latest_df.groupby("platform", as_index=False)["final_fee"].mean()
    comparison_df["final_fee"] = comparison_df["final_fee"].round(2)

    st.dataframe(comparison_df, use_container_width=True)

    st.bar_chart(comparison_df.set_index("platform")["final_fee"])
else:
    st.warning("No data available for platform comparison.")

# -----------------------------
# Auto Refresh
# -----------------------------
if auto_refresh:
    st.info("Auto refresh is ON. Refreshing every 10 seconds...")
    time.sleep(10)
    st.rerun()
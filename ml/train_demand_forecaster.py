import os
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from core.db import get_connection, release_connection

MODEL_DIR = "ml/models"
MODEL_PATH = os.path.join(MODEL_DIR, "demand_forecaster.pkl")


def fetch_order_history():
    conn = get_connection()
    try:
        query = """
        SELECT
            platform_id,
            region_id,
            order_count,
            event_time
        FROM orders
        ORDER BY event_time ASC;
        """
        df = pd.read_sql(query, conn)
        return df
    finally:
        release_connection(conn)


def build_training_data(df: pd.DataFrame):
    if df.empty:
        return pd.DataFrame()

    df["event_time"] = pd.to_datetime(df["event_time"], utc=True)

    # Bucket into 1-minute intervals (better for your fast simulator)
    df["bucket_time"] = df["event_time"].dt.floor("1min")

    agg = (
        df.groupby(["platform_id", "region_id", "bucket_time"], as_index=False)["order_count"]
        .sum()
        .sort_values(["platform_id", "region_id", "bucket_time"])
    )

    # Time features
    agg["hour"] = agg["bucket_time"].dt.hour
    agg["day_of_week"] = agg["bucket_time"].dt.dayofweek
    agg["is_weekend"] = (agg["day_of_week"] >= 5).astype(int)

    # Lag features per platform-region
    agg["lag_1"] = agg.groupby(["platform_id", "region_id"])["order_count"].shift(1)
    agg["lag_2"] = agg.groupby(["platform_id", "region_id"])["order_count"].shift(2)
    agg["lag_3"] = agg.groupby(["platform_id", "region_id"])["order_count"].shift(3)

    # Rolling mean of previous 3 buckets
    agg["rolling_mean_3"] = (
        agg.groupby(["platform_id", "region_id"])["order_count"]
        .transform(lambda s: s.shift(1).rolling(3).mean())
    )

    # Target = next bucket's order_count
    agg["target_next_order_count"] = (
        agg.groupby(["platform_id", "region_id"])["order_count"].shift(-1)
    )

    # Drop rows without enough history / no target
    train_df = agg.dropna().copy()

    return train_df


def train_and_save_model():
    print("📦 Fetching order history...")
    df = fetch_order_history()

    if df.empty:
        print("❌ No order history found in database.")
        return

    train_df = build_training_data(df)

    if train_df.empty:
        print("❌ Not enough historical data to train model.")
        print("➡️ Run simulator longer so at least a few 1-minute buckets are available.")
        return

    feature_cols = [
        "platform_id",
        "region_id",
        "hour",
        "day_of_week",
        "is_weekend",
        "lag_1",
        "lag_2",
        "lag_3",
        "rolling_mean_3",
    ]

    X = train_df[feature_cols]
    y = train_df["target_next_order_count"]

    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=8,
        random_state=42,
        n_jobs=-1,
    )

    print(f"🧠 Training on {len(train_df)} samples...")
    model.fit(X, y)

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(
        {
            "model": model,
            "feature_cols": feature_cols,
        },
        MODEL_PATH,
    )

    print(f"✅ Demand forecasting model saved to: {MODEL_PATH}")


if __name__ == "__main__":
    train_and_save_model()
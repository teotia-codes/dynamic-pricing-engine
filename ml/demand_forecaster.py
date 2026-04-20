import os
import joblib
import pandas as pd
from core.db import get_connection, release_connection

MODEL_PATH = os.path.join("ml", "models", "demand_forecaster.pkl")


def load_model_bundle():
    if not os.path.exists(MODEL_PATH):
        return None
    return joblib.load(MODEL_PATH)


def fetch_recent_order_buckets():
    conn = get_connection()
    try:
        query = """
        SELECT
            platform_id,
            region_id,
            order_count,
            event_time
        FROM orders
        WHERE event_time >= NOW() - INTERVAL '2 hours'
        ORDER BY event_time ASC;
        """
        df = pd.read_sql(query, conn)
        return df
    finally:
        release_connection(conn)


def build_latest_features(df: pd.DataFrame):
    if df.empty:
        return pd.DataFrame()

    df["event_time"] = pd.to_datetime(df["event_time"], utc=True)
    df["bucket_time"] = df["event_time"].dt.floor("1min")

    agg = (
        df.groupby(["platform_id", "region_id", "bucket_time"], as_index=False)["order_count"]
        .sum()
        .sort_values(["platform_id", "region_id", "bucket_time"])
    )

    latest_rows = []

    for (platform_id, region_id), group in agg.groupby(["platform_id", "region_id"]):
        group = group.sort_values("bucket_time").copy()

        if len(group) < 3:
            continue

        last_time = group["bucket_time"].iloc[-1]
        next_time = last_time + pd.Timedelta(minutes=1)

        lag_1 = group["order_count"].iloc[-1]
        lag_2 = group["order_count"].iloc[-2]
        lag_3 = group["order_count"].iloc[-3]
        rolling_mean_3 = group["order_count"].iloc[-3:].mean()

        latest_rows.append(
            {
                "platform_id": platform_id,
                "region_id": region_id,
                "bucket_time": next_time,
                "hour": next_time.hour,
                "day_of_week": next_time.dayofweek,
                "is_weekend": 1 if next_time.dayofweek >= 5 else 0,
                "lag_1": lag_1,
                "lag_2": lag_2,
                "lag_3": lag_3,
                "rolling_mean_3": rolling_mean_3,
            }
        )

    return pd.DataFrame(latest_rows)


def predict_next_demand():
    bundle = load_model_bundle()
    if bundle is None:
        return {}

    model = bundle["model"]
    feature_cols = bundle["feature_cols"]

    df = fetch_recent_order_buckets()
    feature_df = build_latest_features(df)

    if feature_df.empty:
        return {}

    X = feature_df[feature_cols]
    preds = model.predict(X)

    result = {}
    for _, row in feature_df.assign(predicted_order_count=preds).iterrows():
        key = (int(row["platform_id"]), int(row["region_id"]))
        result[key] = max(0, float(row["predicted_order_count"]))

    return result
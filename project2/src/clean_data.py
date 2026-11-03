"""Audit, clean, and summarize the simulated raw credit dataset."""
import logging

import numpy as np
import pandas as pd
from scipy.stats import pointbiserialr
from sklearn.preprocessing import StandardScaler

from .config import (
    CLEAN_DATA_PATH, FEATURE_COLUMNS, RAW_DATA_PATH, RESULTS_DIR, TABLES_DIR,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def _scale_summary(frame: pd.DataFrame) -> pd.DataFrame:
    x = frame[FEATURE_COLUMNS]
    standardized = StandardScaler().fit_transform(x)
    raw_dist = ((x.to_numpy() - x.to_numpy().mean(axis=0)) ** 2).mean(axis=0)
    scaled_dist = ((standardized - standardized.mean(axis=0)) ** 2).mean(axis=0)
    rows = []
    for i, feature in enumerate(FEATURE_COLUMNS):
        correlation = pointbiserialr(frame["default_status"], x[feature]).statistic
        rows.append({
            "feature": feature, "mean": x[feature].mean(), "sd": x[feature].std(),
            "variance": x[feature].var(), "median": x[feature].median(),
            "iqr": x[feature].quantile(.75) - x[feature].quantile(.25),
            "point_biserial_correlation": correlation,
            "raw_distance_share_pct": 100 * raw_dist[i] / raw_dist.sum(),
            "standardized_distance_share_pct": 100 * scaled_dist[i] / scaled_dist.sum(),
        })
    return pd.DataFrame(rows)


def clean_data() -> pd.DataFrame:
    frame = pd.read_csv(RAW_DATA_PATH)
    logging.info("Initial rows: %d", len(frame))
    frame = frame.drop_duplicates()
    logging.info("After deduplication: %d rows", len(frame))
    frame = frame.dropna(subset=FEATURE_COLUMNS)
    logging.info("After missingness removal: %d rows", len(frame))
    valid = (
        (frame["annual_revenue_usd"] > 0) & (frame["loan_principal_usd"] > 0)
        & frame["credit_utilization_ratio"].between(0, 1)
        & frame["debt_to_income_ratio"].between(0, 1)
        & frame["delinquency_rate_24m"].between(0, 1)
        & frame["payment_timeliness_index"].between(0, 1)
    )
    frame = frame.loc[valid].reset_index(drop=True)
    logging.info("Final rows: %d", len(frame))
    if frame.shape != (600, 12):
        raise RuntimeError(f"Expected (600, 12), got {frame.shape}")
    CLEAN_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    frame = frame.sort_values("borrower_id").reset_index(drop=True)
    frame.to_csv(CLEAN_DATA_PATH, index=False)
    _scale_summary(frame).to_csv(TABLES_DIR / "feature_scale_summary.csv", index=False)
    return frame


if __name__ == "__main__":
    clean_data()

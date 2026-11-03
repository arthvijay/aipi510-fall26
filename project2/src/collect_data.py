"""Generate the controlled Monte Carlo commercial-credit dataset.

The clean cohort has 360 performing and 240 defaulted borrowers. Features use
the exact Normal, Gamma, and Exponential class-conditional distributions in
the project specification, followed by domain clipping and rounding. The raw
ingestion file adds 19 missing values, 11 out-of-range corruptions, and 18
exact duplicate rows (SEED=42), yielding 648 rows.
"""
import numpy as np
import pandas as pd

from .config import DATA_DIR, FEATURE_COLUMNS, RAW_DATA_PATH, SEED


def _class_features(rng: np.random.Generator, label: int, n: int) -> dict[str, np.ndarray]:
    if label == 0:
        revenue = rng.normal(425000, 165000, n)
        principal = rng.normal(132000, 56000, n)
        age = rng.gamma(3.8, 2.6, n) + 1.2
        capital = rng.normal(54.0, 21.0, n)
        dti = rng.normal(0.26, 0.095, n)
        utilization = rng.normal(0.36, 0.165, n)
        delinquency = rng.exponential(1 / 0.045, n)
        timeliness = rng.normal(0.84, 0.088, n)
    else:
        revenue = rng.normal(398000, 170000, n)
        principal = rng.normal(141000, 59000, n)
        age = rng.gamma(2.6, 2.2, n) + 1.0
        capital = rng.normal(69.5, 23.5, n)
        dti = rng.normal(0.43, 0.105, n)
        utilization = rng.normal(0.64, 0.170, n)
        delinquency = rng.normal(0.165, 0.075, n)
        timeliness = rng.normal(0.66, 0.105, n)
    return {
        "annual_revenue_usd": np.round(np.clip(revenue, 48000, 985000), 2),
        "loan_principal_usd": np.round(np.clip(principal, 12000, 325000), 2),
        "enterprise_age_years": np.round(np.clip(age, 1.0, 35.0), 1),
        "working_capital_days": np.round(np.clip(capital, 10.0, 150.0), 1),
        "debt_to_income_ratio": np.round(np.clip(dti, 0.05, 0.78), 4),
        "credit_utilization_ratio": np.round(np.clip(utilization, 0.03, 0.99), 4),
        "delinquency_rate_24m": np.round(np.clip(delinquency, 0.0, 0.52), 4),
        "payment_timeliness_index": np.round(np.clip(timeliness, 0.28, 1.0), 4),
    }


def generate_data() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    labels = np.repeat([0, 1], [360, 240])
    order = rng.permutation(len(labels))
    labels = labels[order]
    data = {feature: np.empty(len(labels)) for feature in FEATURE_COLUMNS}
    for label in (0, 1):
        indexes = np.flatnonzero(labels == label)
        values = _class_features(rng, label, len(indexes))
        for feature in FEATURE_COLUMNS:
            data[feature][indexes] = values[feature]
    frame = pd.DataFrame(data)
    frame.insert(0, "borrower_id", [f"BRW-{10001 + i}" for i in range(len(frame))])
    frame.insert(1, "region", rng.choice(["Northeast", "Midwest", "South", "West"], len(frame)))
    frame.insert(2, "industry_sector", rng.choice(
        ["Manufacturing", "Logistics", "Healthcare Services", "Retail Trade", "B2B Software"],
        len(frame),
    ))
    frame["default_status"] = labels

    missing_rows = frame.iloc[:19].copy()
    for column, indexes in [
        ("credit_utilization_ratio", np.arange(0, 8)),
        ("annual_revenue_usd", np.arange(8, 14)),
        ("debt_to_income_ratio", np.arange(14, 19)),
    ]:
        missing_rows.loc[indexes, column] = np.nan
    missing_rows["borrower_id"] = [f"ING-MISSING-{i:02d}" for i in range(19)]
    corrupt_rows = frame.iloc[19:30].copy()
    corrupt_rows.loc[corrupt_rows.index[:6], "annual_revenue_usd"] = -99999.0
    corrupt_rows.loc[corrupt_rows.index[6:9], "credit_utilization_ratio"] = 1.85
    corrupt_rows.loc[corrupt_rows.index[9:], "debt_to_income_ratio"] = -0.45
    corrupt_rows["borrower_id"] = [f"ING-CORRUPT-{i:02d}" for i in range(11)]
    raw = pd.concat([frame, missing_rows, corrupt_rows, frame.iloc[:18]], ignore_index=True)
    return raw.sample(frac=1.0, random_state=SEED).reset_index(drop=True)


def main() -> None:
    DATA_DIR.joinpath("raw").mkdir(parents=True, exist_ok=True)
    np.random.seed(SEED)
    if not RAW_DATA_PATH.exists():
        raise FileNotFoundError(f"Canonical raw dataset not found: {RAW_DATA_PATH}")
    output = pd.read_csv(RAW_DATA_PATH)
    if len(output) != 648:
        raise RuntimeError(f"Expected 648 raw rows, got {len(output)}")
    print(f"Validated canonical raw dataset ({len(output)} rows) at {RAW_DATA_PATH}")


if __name__ == "__main__":
    main()

"""A priori and achieved power for paired two-sided t-tests."""
import math

import numpy as np
import pandas as pd
from scipy.stats import nct, t

from .config import ALPHA, RESULTS_DIR, TABLES_DIR


def power(n: int, effect_size: float = 0.5, alpha: float = ALPHA) -> float:
    df = n - 1
    critical = t.ppf(1 - alpha / 2, df)
    noncentrality = effect_size * math.sqrt(n)
    return float(nct.sf(critical, df, noncentrality) + nct.cdf(-critical, df, noncentrality))


def required_n(target: float, effect_size: float = 0.5) -> int:
    for n in range(2, 1000):
        if power(n, effect_size) >= target:
            return n
    raise RuntimeError("No sample size reached target power")


def run_power_analysis() -> dict:
    rows = []
    for n in range(5, 86):
        for effect in (0.35, 0.50, 0.80):
            rows.append({"n": n, "effect_size": effect, "power": power(n, effect)})
    curve = pd.DataFrame(rows)
    RESULTS_DIR.mkdir(exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    curve.to_csv(TABLES_DIR / "power_curve.csv", index=False)
    return {
        "alpha": ALPHA, "effect_size": 0.5,
        "required_n_80": required_n(0.80), "required_n_90": required_n(0.90),
        "power_n50": power(50), "power_n30": power(30),
    }


if __name__ == "__main__":
    print(run_power_analysis())

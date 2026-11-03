"""Leakage-free repeated-CV comparison of raw and standardized k-NN."""
import json
import math
import numpy as np
import pandas as pd
from scipy.stats import (
    friedmanchisquare, kurtosis, kstest, norm, shapiro, skew, ttest_rel,
    wilcoxon,
)
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import RepeatedStratifiedKFold, StratifiedShuffleSplit
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler

from .config import CLEAN_DATA_PATH, FEATURE_COLUMNS, RESULTS_DIR, SEED, SUMMARY_PATH, TABLES_DIR


SCALERS = {"Unscaled": None, "Z-Score": StandardScaler(), "Min-Max": MinMaxScaler(), "IQR": RobustScaler()}


def _fit_score(x_train, x_test, y_train, y_test, k=5, metric="euclidean", scaler=None):
    if scaler is not None:
        scaler = scaler.__class__()
        x_train = scaler.fit_transform(x_train)
        x_test = scaler.transform(x_test)
    model = KNeighborsClassifier(n_neighbors=k, metric=metric)
    model.fit(x_train, y_train)
    prediction = model.predict(x_test)
    probability = model.predict_proba(x_test)[:, 1]
    return {
        "accuracy": accuracy_score(y_test, prediction),
        "precision": precision_score(y_test, prediction, zero_division=0),
        "recall": recall_score(y_test, prediction, zero_division=0),
        "f1": f1_score(y_test, prediction, zero_division=0),
        "roc_auc": roc_auc_score(y_test, probability),
    }, prediction, probability


def _cv_results(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, list[float]], dict]:
    x = frame[FEATURE_COLUMNS].to_numpy()
    y = frame["default_status"].to_numpy()
    cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=10, random_state=SEED)
    rows = []
    predictions = {name: [] for name in SCALERS}
    probabilities = {name: [] for name in SCALERS}
    for fold, (train, test) in enumerate(cv.split(x, y), 1):
        for name, scaler in SCALERS.items():
            metrics, prediction, probability = _fit_score(
                x[train], x[test], y[train], y[test], scaler=scaler
            )
            rows.append({"fold": fold, "scaler": name, **metrics})
            predictions[name].extend(zip(test, prediction))
            probabilities[name].extend(zip(test, probability))
    return pd.DataFrame(rows), predictions, probabilities


def _posthoc(frame: pd.DataFrame) -> pd.DataFrame:
    x, y = frame[FEATURE_COLUMNS].to_numpy(), frame["default_status"].to_numpy()
    cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=10, random_state=SEED)
    records = []
    for metric in ("euclidean", "manhattan"):
        for k in (1, 3, 5, 7, 9, 11, 15, 21, 31):
            raw_scores, scaled_scores = [], []
            for train, test in cv.split(x, y):
                raw, _, _ = _fit_score(x[train], x[test], y[train], y[test], k, metric)
                scaled, _, _ = _fit_score(
                    x[train], x[test], y[train], y[test], k, metric, StandardScaler()
                )
                raw_scores.append(raw["accuracy"])
                scaled_scores.append(scaled["accuracy"])
            differences = np.asarray(scaled_scores) - np.asarray(raw_scores)
            p = float(ttest_rel(scaled_scores, raw_scores).pvalue)
            records.append({
                "metric": metric, "k": k, "raw_accuracy_mean": np.mean(raw_scores),
                "standardized_accuracy_mean": np.mean(scaled_scores),
                "raw_accuracy_sd": np.std(raw_scores, ddof=1),
                "standardized_accuracy_sd": np.std(scaled_scores, ddof=1),
                "mean_gain": np.mean(differences), "sd_gain": np.std(differences, ddof=1),
                "cohen_dz": np.mean(differences) / np.std(differences, ddof=1),
                "p_value": p,
            })
    result = pd.DataFrame(records)
    for metric in result["metric"].unique():
        indexes = result["metric"] == metric
        pvals = result.loc[indexes, "p_value"].to_numpy()
        order = np.argsort(pvals)
        adjusted = np.empty(len(pvals))
        adjusted[order] = np.minimum(1, np.maximum.accumulate((len(pvals) - np.arange(len(pvals))) * pvals[order]))
        result.loc[indexes, "holm_p_value"] = adjusted
        result.loc[indexes, "bonferroni_p_value"] = np.minimum(1, pvals * len(pvals))
    return result


def _holdout(frame: pd.DataFrame) -> dict:
    x, y = frame[FEATURE_COLUMNS].to_numpy(), frame["default_status"].to_numpy()
    splitter = StratifiedShuffleSplit(n_splits=30, test_size=0.2, random_state=123)
    raw, scaled = [], []
    for train, test in splitter.split(x, y):
        raw.append(_fit_score(x[train], x[test], y[train], y[test])[0]["accuracy"])
        scaled.append(_fit_score(
            x[train], x[test], y[train], y[test], scaler=StandardScaler()
        )[0]["accuracy"])
    differences = np.asarray(scaled) - np.asarray(raw)
    return {"n_splits": 30, "raw_accuracy_mean": float(np.mean(raw)),
            "standardized_accuracy_mean": float(np.mean(scaled)),
            "mean_gain": float(np.mean(differences)),
            "cohen_dz": float(np.mean(differences) / np.std(differences, ddof=1))}


def run_analysis() -> dict:
    frame = pd.read_csv(CLEAN_DATA_PATH)
    fold_results, _, _ = _cv_results(frame)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(exist_ok=True)
    fold_results.to_csv(TABLES_DIR / "paired_cv_results.csv", index=False)
    wide = fold_results.pivot(index="fold", columns="scaler", values="accuracy")
    differences = wide["Z-Score"].to_numpy() - wide["Unscaled"].to_numpy()
    test = ttest_rel(wide["Z-Score"], wide["Unscaled"])
    sd = np.std(differences, ddof=1)
    mean_gain = float(np.mean(differences))
    standard_error = sd / math.sqrt(len(differences))
    nb_se = math.sqrt((1 / len(differences) + 0.25) * sd**2)
    nb_t = mean_gain / nb_se
    ci = (mean_gain - 1.96 * standard_error, mean_gain + 1.96 * standard_error)
    nb_ci = (mean_gain - 1.96 * nb_se, mean_gain + 1.96 * nb_se)
    wilcoxon_result = wilcoxon(differences)
    friedman = friedmanchisquare(*(wide[name] for name in SCALERS))
    posthoc = _posthoc(frame)
    posthoc.to_csv(TABLES_DIR / "posthoc_k_sensitivity.csv", index=False)
    summary = {
        "study": {"seed": SEED, "n_rows": len(frame), "n_folds": 50, "k": 5},
        "primary": {
            "raw_accuracy_mean": float(wide["Unscaled"].mean()),
            "standardized_accuracy_mean": float(wide["Z-Score"].mean()),
            "mean_gain": mean_gain, "mean_gain_percentage_points": mean_gain * 100,
            "paired_t": {"t": float(test.statistic), "df": 49, "p_value": float(test.pvalue),
                         "ci_95": [float(v) for v in ci]},
            "nadeau_bengio": {"t": float(nb_t), "p_value": float(2 * norm.sf(abs(nb_t))),
                              "ci_95": [float(v) for v in nb_ci]},
            "wilcoxon": {"statistic": float(wilcoxon_result.statistic),
                         "p_value": float(wilcoxon_result.pvalue)},
            "effect_sizes": {
                "paired_cohen_dz": float(mean_gain / sd),
                "pooled_cohen_d": float((wide["Z-Score"].mean() - wide["Unscaled"].mean()) /
                    math.sqrt((wide["Z-Score"].var(ddof=1) + wide["Unscaled"].var(ddof=1)) / 2)),
                "hedges_g": float((mean_gain / math.sqrt(
                    (wide["Z-Score"].var(ddof=1) + wide["Unscaled"].var(ddof=1)) / 2
                )) * (1 - 3 / (4 * 98 - 1))),
            },
            "assumptions": {
                "shapiro_w": float(shapiro(differences).statistic),
                "shapiro_p": float(shapiro(differences).pvalue),
                "ks_d": float(kstest((differences - differences.mean()) / sd, "norm").statistic),
                "ks_p": float(kstest((differences - differences.mean()) / sd, "norm").pvalue),
                "skewness": float(skew(differences)), "kurtosis": float(kurtosis(differences)),
            },
            "friedman": {"chi_square": float(friedman.statistic), "p_value": float(friedman.pvalue)},
        },
        "holdout_replication": _holdout(frame),
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    print(json.dumps(run_analysis(), indent=2))

"""Create six publication-quality diagnostic figures from pipeline outputs."""
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.metrics import RocCurveDisplay
from sklearn.model_selection import StratifiedKFold
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler

from .config import (
    BLUE, CLEAN_DATA_PATH, FEATURE_COLUMNS, FIGURES_DIR, LABELS, NAVY,
    SEED, SUMMARY_PATH, TABLES_DIR, TEAL, AMBER, SLATE,
)
from .power_analysis import power


def _save(fig, name):
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / name, dpi=200, bbox_inches="tight")
    plt.close(fig)


def generate_figures() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    summary = json.loads(SUMMARY_PATH.read_text())
    scale = pd.read_csv(TABLES_DIR / "feature_scale_summary.csv")
    cv = pd.read_csv(TABLES_DIR / "paired_cv_results.csv")
    posthoc = pd.read_csv(TABLES_DIR / "posthoc_k_sensitivity.csv")

    fig, axes = plt.subplots(1, 2, figsize=(13, 6))
    labels = [LABELS[x] for x in scale["feature"]]
    axes[0].barh(labels, np.log10(scale["variance"]), color=BLUE)
    axes[0].set_title("Raw feature variance (log10)")
    axes[0].set_xlabel("log10 variance")
    axes[1].barh(labels, scale["raw_distance_share_pct"], color=AMBER, label="Raw")
    axes[1].barh(labels, scale["standardized_distance_share_pct"], color=TEAL, alpha=.85, label="Z-score")
    axes[1].set_title("Mean share of squared Euclidean distance")
    axes[1].set_xlabel("Contribution (%)")
    axes[1].legend()
    _save(fig, "chart_1_scale_dominance.png")

    fig, ax = plt.subplots(figsize=(8, 5))
    ns = np.arange(5, 86)
    for effect, color in zip((.35, .50, .80), (SLATE, BLUE, TEAL)):
        ax.plot(ns, [power(n, effect) for n in ns], label=f"d = {effect:.2f}", color=color)
    ax.axhline(.8, color=AMBER, linestyle="--", label="80% power")
    ax.axhline(.9, color=NAVY, linestyle=":", label="90% power")
    ax.scatter([50], [power(50)], color=AMBER, zorder=3)
    ax.annotate(f"N=50: {power(50):.1%}", (50, power(50)),
                xytext=(8, -18), textcoords="offset points", color=AMBER)
    ax.set(xlabel="Paired folds (N)", ylabel="Power", title="A priori power curves", ylim=(0, 1.02))
    ax.legend()
    _save(fig, "chart_2_power_curve.png")

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    order = ["Unscaled", "Z-Score", "Min-Max", "IQR"]
    axes[0].boxplot([cv.loc[cv.scaler == name, "accuracy"] for name in order], tick_labels=order)
    axes[0].set_ylabel("Accuracy")
    axes[0].set_title("Matched-fold accuracy distributions")
    wide = cv.pivot(index="fold", columns="scaler", values="accuracy")
    for name, color in zip(order, (SLATE, BLUE, TEAL, AMBER)):
        axes[1].plot(np.arange(len(wide)), wide[name], color=color, alpha=.25)
    axes[1].set(xlabel="Matched fold", ylabel="Accuracy", title="Fold trajectories")
    _save(fig, "chart_3_paired_accuracy_distributions.png")

    differences = (wide["Z-Score"] - wide["Unscaled"]).to_numpy()
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    axes[0].hist(differences, bins=10, density=True, color=BLUE, alpha=.75)
    grid = np.linspace(differences.min(), differences.max(), 100)
    axes[0].plot(grid, norm.pdf(grid, differences.mean(), differences.std(ddof=1)), color=NAVY)
    axes[0].set_title("Paired accuracy gains")
    stats = summary["primary"]["assumptions"]
    axes[0].text(.03, .95, f"Shapiro p={stats['shapiro_p']:.3g}", transform=axes[0].transAxes, va="top")
    axes[1].scatter(np.sort(norm.ppf((np.arange(1, len(differences) + 1) - .5) / len(differences))),
                    np.sort((differences - differences.mean()) / differences.std(ddof=1)), color=TEAL)
    axes[1].plot([-3, 3], [-3, 3], color=NAVY)
    axes[1].set_title("Normal Q-Q plot")
    _save(fig, "chart_4_normality_diagnostics.png")

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for metric, color in (("euclidean", BLUE), ("manhattan", TEAL)):
        subset = posthoc[posthoc.metric == metric]
        axes[0].errorbar(
            subset.k, subset.standardized_accuracy_mean,
            yerr=subset.standardized_accuracy_sd,
            marker="o", color=color, capsize=3, label=metric,
        )
    axes[0].set(xlabel="k", ylabel="Mean standardized accuracy", title="k sensitivity")
    axes[0].legend()
    for metric, color in (("euclidean", BLUE), ("manhattan", TEAL)):
        subset = posthoc[posthoc.metric == metric]
        axes[1].bar(
            subset.k + (-0.8 if metric == "euclidean" else 0.8),
            subset.cohen_dz, width=1.5, color=color, alpha=.85, label=metric,
        )
    axes[1].set(xlabel="k", ylabel="Paired Cohen's d", title="Effect-size stability")
    axes[1].legend()
    _save(fig, "chart_5_k_sensitivity_curve.png")

    frame = pd.read_csv(CLEAN_DATA_PATH)
    x, y = frame[FEATURE_COLUMNS].to_numpy(), frame["default_status"].to_numpy()
    train, test = next(StratifiedKFold(5, shuffle=True, random_state=SEED).split(x, y))
    raw = KNeighborsClassifier(5).fit(x[train], y[train])
    scaler = StandardScaler().fit(x[train])
    scaled = KNeighborsClassifier(5).fit(scaler.transform(x[train]), y[train])
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for model, xx, label in ((raw, x[test], "Unscaled"), (scaled, scaler.transform(x[test]), "Z-score")):
        RocCurveDisplay.from_estimator(model, xx, y[test], ax=axes[0], name=label)
    axes[0].set_title("Out-of-fold ROC curves")
    metrics = ["accuracy", "precision", "recall", "f1", "roc_auc"]
    axes[1].bar(
        np.arange(5) - .18,
        [cv.loc[cv.scaler == "Unscaled", metric].mean() for metric in metrics],
        width=.36, color=SLATE, label="Unscaled",
    )
    axes[1].bar(
        np.arange(5) + .18,
        [cv.loc[cv.scaler == "Z-Score", metric].mean() for metric in metrics],
        width=.36, color=TEAL, label="Z-score",
    )
    axes[1].set_xticks(np.arange(5), ["Accuracy", "Precision", "Recall", "F1", "ROC-AUC"])
    axes[1].set_ylim(0, 1)
    axes[1].set_title("Mean classification metrics")
    axes[1].tick_params(axis="x", rotation=35)
    axes[1].legend()
    _save(fig, "chart_6_confusion_matrices_roc.png")


if __name__ == "__main__":
    generate_figures()

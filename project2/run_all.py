"""Run every reproducible study stage in order."""
from pathlib import Path

from src.clean_data import clean_data
from src.collect_data import main as collect_data
from src.power_analysis import run_power_analysis
from src.statistical_analysis import run_analysis
from src.visualize_results import generate_figures


def main() -> None:
    collect_data()
    clean_data()
    power = run_power_analysis()
    summary = run_analysis()
    generate_figures()
    required = [
        Path("data/raw/commercial_credit_underwriting_raw.csv"),
        Path("data/processed/commercial_credit_underwriting_cleaned.csv"),
        Path("results/tables/paired_cv_results.csv"),
        Path("results/tables/posthoc_k_sensitivity.csv"),
        Path("results/tables/feature_scale_summary.csv"),
        Path("results/experiment_summary.json"),
    ] + [Path("results/figures") / f"chart_{i}_{name}.png" for i, name in enumerate([
        "scale_dominance", "power_curve", "paired_accuracy_distributions",
        "normality_diagnostics", "k_sensitivity_curve", "confusion_matrices_roc",
    ], 1)]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise RuntimeError(f"Missing outputs: {missing}")
    print("\nStatistical summary")
    print("-------------------")
    print(f"{'Metric':<30}{'Value':>16}")
    print(f"{'Mean accuracy gain (pp)':<30}{summary['primary']['mean_gain_percentage_points']:>16.2f}")
    print(f"{'Paired t-test p-value':<30}{summary['primary']['paired_t']['p_value']:>16.3e}")
    print(f"{'Power at N=50':<30}{power['power_n50']:>16.2%}")
    print(f"{'Verified outputs':<30}{len(required):>16d}")


if __name__ == "__main__":
    main()

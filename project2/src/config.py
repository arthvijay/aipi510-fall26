"""Shared configuration for the reproducible study."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_PATH = DATA_DIR / "raw" / "commercial_credit_underwriting_raw.csv"
CLEAN_DATA_PATH = DATA_DIR / "processed" / "commercial_credit_underwriting_cleaned.csv"
RESULTS_DIR = PROJECT_ROOT / "results"
TABLES_DIR = RESULTS_DIR / "tables"
FIGURES_DIR = RESULTS_DIR / "figures"
SUMMARY_PATH = RESULTS_DIR / "experiment_summary.json"

AUTHOR = "Arth Vijaywargia"
COURSE = "AIPI 510 — Module Project 2: Statistical Analysis"
SEED = 42
ALPHA = 0.05
N_FOLDS = 5
N_REPEATS = 10

TARGET = "default_status"
FEATURE_COLUMNS = [
    "annual_revenue_usd", "loan_principal_usd", "enterprise_age_years",
    "working_capital_days", "debt_to_income_ratio",
    "credit_utilization_ratio", "delinquency_rate_24m",
    "payment_timeliness_index",
]
CATEGORICAL_COLUMNS = ["borrower_id", "region", "industry_sector"]
LABELS = {
    "annual_revenue_usd": "Annual revenue",
    "loan_principal_usd": "Loan principal",
    "enterprise_age_years": "Enterprise age",
    "working_capital_days": "Working capital days",
    "debt_to_income_ratio": "Debt-to-income ratio",
    "credit_utilization_ratio": "Credit utilization ratio",
    "delinquency_rate_24m": "24-month delinquency rate",
    "payment_timeliness_index": "Payment timeliness index",
}
NAVY = "#0F172A"
BLUE = "#1D4ED8"
TEAL = "#0D9488"
AMBER = "#D97706"
SLATE = "#64748B"

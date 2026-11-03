"""Create analysis-ready features from the cleaned datasets."""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
OUTPUT = ROOT / "data" / "clean" / "analysis_dataset.csv"


def build_stackoverflow_features() -> pd.DataFrame:
    questions = pd.read_csv(CLEAN / "stackoverflow_monthly_questions.csv", parse_dates=["month"])
    questions = questions.sort_values("month").reset_index(drop=True)
    questions["year"] = questions["month"].dt.year
    questions["month_name"] = questions["month"].dt.strftime("%b")
    questions["year_over_year_change_pct"] = questions["questions"].pct_change(12) * 100
    questions["post_chatgpt"] = questions["month"] >= pd.Timestamp("2022-12-01")
    questions["log_questions"] = np.log(questions["questions"])
    questions["rolling_12_month_median"] = questions["questions"].rolling(12, min_periods=12).median()
    return questions


def build_survey_features() -> pd.DataFrame:
    survey = pd.read_csv(CLEAN / "survey_ai_and_stackoverflow.csv")
    survey["uses_ai_binary"] = survey["uses_ai"].eq("uses AI")
    survey["daily_stackoverflow_visitor"] = survey["visits_so_daily"].eq(True)
    return survey


def build_analysis_dataset() -> pd.DataFrame:
    questions = build_stackoverflow_features()
    announcements = pd.read_csv(CLEAN / "chatgpt_weekly_users.csv", parse_dates=["date", "month"])
    announcements["weekly_users_growth_pct"] = announcements["weekly_users_millions"].pct_change() * 100
    questions.to_csv(OUTPUT, index=False)
    announcements.to_csv(CLEAN / "chatgpt_weekly_users_features.csv", index=False)
    build_survey_features().to_csv(CLEAN / "survey_ai_and_stackoverflow_features.csv", index=False)
    return questions


if __name__ == "__main__":
    result = build_analysis_dataset()
    print(f"saved {OUTPUT} ({len(result)} rows)")
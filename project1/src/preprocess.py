"""Run the cleaning stage of the reproducible analysis pipeline."""

from pathlib import Path

from clean import (
    clean_chatgpt_weekly_users,
    clean_developer_survey,
    clean_stackoverflow_questions,
)


if __name__ == "__main__":
    clean_stackoverflow_questions()
    clean_chatgpt_weekly_users()
    raw_survey = Path(__file__).resolve().parents[1] / "data" / "raw" / "survey"
    if all((raw_survey / f"survey_{year}_results.csv").exists() for year in [2023, 2024, 2025]):
        clean_developer_survey()
    else:
        print("survey raw files not found; retaining the committed cleaned survey snapshot")
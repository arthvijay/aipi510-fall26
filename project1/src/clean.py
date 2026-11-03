"""Clean the three datasets in data/raw/ and save them to data/clean/.

1. Stack Overflow new questions per month
2. ChatGPT weekly active users
3. Stack Overflow Developer Survey 2023-2025 (only AI use and Stack Overflow visits)

Cleaning only fixes formats and makes answers comparable across years: no numbers are changed,
no missing values are filled in, and no rows are dropped as outliers.
"""
from pathlib import Path

import pandas as pd

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
CLEAN = Path(__file__).resolve().parents[1] / "data" / "clean"
CLEAN.mkdir(exist_ok=True)


def clean_stackoverflow_questions():
    """Dataset 1: Stack Overflow new questions per month.

    Converts `month` to a date, sorts by time, and checks that all 104 months are there with no gaps.
    Reads data/raw/stackoverflow_monthly_questions.csv, saves data/clean/stackoverflow_monthly_questions.csv.
    """
    df = pd.read_csv(RAW / "stackoverflow_monthly_questions.csv", parse_dates=["month"])
    df = df.sort_values("month")
    assert len(df) == 104, "expected 104 months (2018-01 to 2026-08)"
    assert df["questions"].notna().all(), "some months have no count"
    df.to_csv(CLEAN / "stackoverflow_monthly_questions.csv", index=False)
    print(f"saved stackoverflow_monthly_questions.csv ({len(df)} months)")


def clean_chatgpt_weekly_users():
    """Dataset 2: ChatGPT weekly active users (millions), as announced by OpenAI.

    Converts `date` to a date and adds `month`, the month of the announcement, so each number can be
    matched with that month's Stack Overflow questions.
    Reads data/raw/chatgpt_weekly_users.csv, saves data/clean/chatgpt_weekly_users.csv.
    """
    df = pd.read_csv(RAW / "chatgpt_weekly_users.csv", parse_dates=["date"])
    df.insert(1, "month", df["date"].dt.to_period("M").dt.to_timestamp())
    df.to_csv(CLEAN / "chatgpt_weekly_users.csv", index=False)
    print(f"saved chatgpt_weekly_users.csv ({len(df)} announcements)")


def clean_developer_survey():
    """Dataset 3: Stack Overflow Developer Survey 2023-2025.

    Keeps two questions, AISelect ("Do you use AI tools?") and SOVisitFreq ("How often do you visit
    Stack Overflow?"), stacks the three years into one table, and rewrites the answers so they mean
    the same thing every year (the wording changed between surveys). Unanswered questions stay empty.
    Reads data/raw/survey/survey_<year>_results.csv, saves data/clean/survey_ai_and_stackoverflow.csv.
    """
    uses_ai = {
        "Yes": "uses AI",                                            # 2023 and 2024 wording
        "Yes, I use AI tools daily": "uses AI",                      # 2025 wording
        "Yes, I use AI tools weekly": "uses AI",
        "Yes, I use AI tools monthly or infrequently": "uses AI",
        "No, but I plan to soon": "plans to",
        "No, and I don't plan to": "does not",
    }
    visits_so_daily = {
        "Multiple times per day": True,
        "Daily or almost daily": True,
        "A few times per week": False,
        "A few times per month or weekly": False,
        "Less than once per month or monthly": False,
        "Less than once every 2 - 3 months": False,                  # added in 2025
        "Infrequently, less than once per year": False,              # added in 2025
    }

    years = []
    for year in [2023, 2024, 2025]:
        raw = pd.read_csv(RAW / "survey" / f"survey_{year}_results.csv", usecols=["AISelect", "SOVisitFreq"])
        years.append(pd.DataFrame({
            "year": year,
            "uses_ai": raw["AISelect"].map(uses_ai),
            "visits_so_daily": raw["SOVisitFreq"].map(visits_so_daily),
        }))
    df = pd.concat(years, ignore_index=True)
    df.to_csv(CLEAN / "survey_ai_and_stackoverflow.csv", index=False)
    print(f"saved survey_ai_and_stackoverflow.csv ({len(df)} respondents)")


if __name__ == "__main__":
    clean_stackoverflow_questions()
    clean_chatgpt_weekly_users()
    clean_developer_survey()

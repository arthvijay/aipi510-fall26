"""Download the three datasets into data/raw/.

1. Stack Overflow new questions per month, 2018-2026 (Stack Exchange API)
2. ChatGPT weekly active users (OpenAI announcements, compiled by hand)
3. Stack Overflow Developer Survey 2023-2025
"""
import os
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
RAW = Path(__file__).resolve().parents[1] / "data" / "raw"


def download_stackoverflow_questions():
    """Dataset 1: how many new questions Stack Overflow got each month, 2018-01 to 2026-08.

    Source: Stack Exchange API, 104 requests. Needs a free key from stackapps.com in .env.
    Saves data/raw/stackoverflow_monthly_questions.csv.
    """
    rows = []
    for month in pd.date_range("2018-01-01", "2026-08-01", freq="MS"):
        next_month = month + pd.DateOffset(months=1)
        params = {
            "site": "stackoverflow",
            "fromdate": int(month.timestamp()),
            "todate": int(next_month.timestamp()) - 1,
            "sort": "creation",
            "filter": "total",
        }
        if os.getenv("STACKEXCHANGE_KEY"):
            params["key"] = os.environ["STACKEXCHANGE_KEY"]
        data = requests.get("https://api.stackexchange.com/2.3/questions", params=params).json()
        if "total" not in data:
            print(f"Stack Exchange API stopped: {data['error_message']}")
            return
        rows.append({"month": month.date(), "questions": data["total"]})
    pd.DataFrame(rows).to_csv(RAW / "stackoverflow_monthly_questions.csv", index=False)
    print("saved stackoverflow_monthly_questions.csv")


def save_chatgpt_weekly_users():
    """Dataset 2: ChatGPT weekly active users (millions), from OpenAI's public announcements.

    OpenAI publishes no downloadable dataset, so these were compiled by hand. Each row keeps its
    source and how the number was phrased ("about", "more than", "on track for").
    Saves data/raw/chatgpt_weekly_users.csv.
    """
    rows = [
        ("2023-11-06", 100, "about", "https://techcrunch.com/2023/11/06/openais-chatgpt-now-has-100-million-weekly-active-users/"),
        ("2024-08-29", 200, "more than", "https://www.axios.com/2024/08/29/openai-chatgpt-200-million-weekly-active-users"),
        ("2024-10-29", 250, "about", "https://finance.yahoo.com/news/openai-cfo-says-75-revenue-175831132.html"),
        ("2024-12-04", 300, "about", "https://www.cnbc.com/2024/12/04/openais-active-user-count-soars-to-300-million-people-per-week.html"),
        ("2025-02-20", 400, "more than", "https://x.com/bradlightcap/status/1892579908179882057"),
        ("2025-03-31", 500, "about", "https://openai.com/index/march-funding-updates/"),
        ("2025-08-04", 700, "on track for", "https://techcrunch.com/2025/08/04/openai-says-chatgpt-is-on-track-to-reach-700m-weekly-users/"),
        ("2025-10-06", 800, "more than", "https://techcrunch.com/2025/10/06/sam-altman-says-chatgpt-has-hit-800m-weekly-active-users/"),
        ("2026-02-27", 900, "more than", "https://openai.com/index/scaling-ai-for-everyone/"),
        ("2026-03-31", 900, "more than", "https://openai.com/index/accelerating-the-next-phase-ai/"),
        ("2026-08-31", 1000, "more than", "https://openai.com/index/expanding-access-to-ai-with-chatgpt-ads/"),
    ]
    df = pd.DataFrame(rows, columns=["date", "weekly_users_millions", "qualifier", "source"])
    df.to_csv(RAW / "chatgpt_weekly_users.csv", index=False)
    print("saved chatgpt_weekly_users.csv")


def download_developer_survey():
    """Dataset 3: Stack Overflow Developer Survey 2023-2025 (AI use, Stack Overflow visits, languages).

    Source: github.com/StackExchange/Survey, about 150 MB per year.
    Saves data/raw/survey/survey_<year>_results.csv.
    """
    url ="https://media.githubusercontent.com/media/StackExchange/Survey/main/packages/archive/{year}/results.csv"
    for year in [2023, 2024, 2025]:
        path = RAW / "survey" / f"survey_{year}_results.csv"
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(requests.get(url.format(year=year)).content)
        print(f"saved survey/{path.name}")


if __name__ == "__main__":
    download_stackoverflow_questions()
    save_chatgpt_weekly_users()
    download_developer_survey()

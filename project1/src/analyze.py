"""Calculate the numeric source of truth used in the project narrative."""

from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
TABLES = ROOT / "outputs" / "tables"
TABLES.mkdir(parents=True, exist_ok=True)


def metric(rows: list[dict], name: str, value: float, unit: str, definition: str) -> None:
    rows.append({"metric": name, "value": value, "unit": unit, "definition": definition})


def main() -> None:
    so = pd.read_csv(CLEAN / "analysis_dataset.csv", parse_dates=["month"])
    survey = pd.read_csv(CLEAN / "survey_ai_and_stackoverflow_features.csv")
    rows: list[dict] = []

    metric(rows, "raw_stackoverflow_months", len(so), "months", "Rows in the raw monthly Stack Overflow series")
    metric(rows, "stackoverflow_first_month_questions", int(so.iloc[0].questions), "questions", "January 2018")
    metric(rows, "stackoverflow_last_month_questions", int(so.iloc[-1].questions), "questions", "August 2026")
    metric(rows, "stackoverflow_first_to_last_change_pct", round((so.iloc[-1].questions / so.iloc[0].questions - 1) * 100, 2), "%", "Change from January 2018 to August 2026")

    annual = so[so.month.dt.year <= 2025].groupby(so.month.dt.year).questions.sum()
    yoy = annual.pct_change() * 100
    metric(rows, "largest_pre_chatgpt_annual_decline_pct", round(float(yoy.loc[:2022].min()), 2), "%", "Largest year-over-year decline through 2022")
    metric(rows, "2023_annual_change_pct", round(float(yoy.loc[2023]), 2), "%", "2023 versus 2022")
    metric(rows, "2024_annual_change_pct", round(float(yoy.loc[2024]), 2), "%", "2024 versus 2023")
    metric(rows, "2025_annual_change_pct", round(float(yoy.loc[2025]), 2), "%", "2025 versus 2024")

    pre = so[so.month < "2022-12-01"].copy()
    pre["t"] = np.arange(len(pre)) / 12
    pre["month_of_year"] = pre.month.dt.month
    pre["covid"] = pre.month.between("2020-03-01", "2020-06-01").astype(int)
    model = smf.ols("np.log(questions) ~ t + covid + C(month_of_year)", data=pre).fit()
    metric(rows, "pre_chatgpt_modeled_annual_change_pct", round(float((np.exp(model.params["t"]) - 1) * 100), 2), "%", "Annualized modeled trend before December 2022, controlling for month and early-pandemic months")

    ai = survey.dropna(subset=["uses_ai", "visits_so_daily"])
    ai = ai[ai.uses_ai.isin(["uses AI", "does not"])]
    daily = ai.groupby(["year", "uses_ai"]).daily_stackoverflow_visitor.mean().mul(100)
    for year in sorted(ai.year.unique()):
        for group in ["uses AI", "does not"]:
            value = daily.get((year, group), np.nan)
            metric(rows, f"daily_visitors_{group.replace(' ', '_')}_{year}", round(float(value), 2), "%", f"Survey respondents in {year} reporting daily or almost-daily visits")
    metric(rows, "survey_cleaned_rows", len(survey), "respondents", "Rows across the three cleaned survey extracts")

    pd.DataFrame(rows).to_csv(TABLES / "key_metrics.csv", index=False)
    print(pd.DataFrame(rows).to_string(index=False))


if __name__ == "__main__":
    main()
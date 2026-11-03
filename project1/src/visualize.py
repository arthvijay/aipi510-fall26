"""Generate final figures from cleaned data and the feature table."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
FIGURES = ROOT / "outputs" / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)
BLUE, ORANGE, INK, MUTED = "#1769aa", "#d95f02", "#20252b", "#7b8794"
plt.rcParams.update({"figure.dpi": 120, "savefig.dpi": 220, "font.size": 10, "axes.titleweight": "bold"})


def save(fig: plt.Figure, name: str) -> None:
    fig.tight_layout()
    fig.savefig(FIGURES / name, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    so = pd.read_csv(CLEAN / "analysis_dataset.csv", parse_dates=["month"])
    wau = pd.read_csv(CLEAN / "chatgpt_weekly_users_features.csv", parse_dates=["date", "month"])
    survey = pd.read_csv(CLEAN / "survey_ai_and_stackoverflow_features.csv")

    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.plot(so.month, so.questions / 1000, color=BLUE, lw=2)
    ax.axvline(pd.Timestamp("2022-11-30"), color=INK, ls="--", lw=1)
    ax.annotate("ChatGPT launch", (pd.Timestamp("2022-11-30"), ax.get_ylim()[1] * .92), xytext=(6, 0), textcoords="offset points", color=INK)
    ax.set(title="Stack Overflow question volume fell across the study period", ylabel="New questions per month (thousands)", xlabel="")
    save(fig, "01_stackoverflow_questions.png")

    annual = so[so.month.dt.year <= 2025].groupby(so.month.dt.year).questions.sum()
    yoy = annual.pct_change().dropna() * 100
    fig, ax = plt.subplots(figsize=(8, 4.5))
    colors = [MUTED if year <= 2022 else BLUE for year in yoy.index]
    ax.bar(yoy.index.astype(str), yoy, color=colors)
    ax.axhline(0, color=INK, lw=.8)
    ax.set(title="The decline was underway before ChatGPT", ylabel="Change in annual questions vs. prior year (%)", xlabel="Year")
    for index, value in enumerate(yoy): ax.text(index, value + (1 if value >= 0 else -1), f"{value:+.0f}%", ha="center", va="bottom" if value >= 0 else "top", fontsize=9)
    save(fig, "02_year_over_year_change.png")

    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    axes[0].plot(wau.date, wau.weekly_users_millions, color=ORANGE, marker="o", lw=2)
    axes[0].set(title="ChatGPT grew rapidly, based on public announcements", ylabel="Weekly users (millions)")
    axes[1].plot(so[so.month >= "2021-01-01"].month, so[so.month >= "2021-01-01"].questions / 1000, color=BLUE, lw=2)
    axes[1].set(title="Stack Overflow questions moved in the opposite direction", ylabel="Questions (thousands)")
    save(fig, "03_chatgpt_and_stackoverflow_trends.png")

    daily = survey.dropna(subset=["uses_ai", "visits_so_daily"])
    daily = daily[daily.uses_ai.isin(["uses AI", "does not"])]
    values = daily.groupby(["year", "uses_ai"]).daily_stackoverflow_visitor.mean().mul(100).unstack()
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for group, color in [("uses AI", BLUE), ("does not", MUTED)]: ax.plot(values.index, values[group], marker="o", lw=2, color=color, label=group)
    ax.set(title="Daily Stack Overflow visits changed among AI users", ylabel="Respondents visiting daily (%)", xlabel="Survey year", xticks=values.index)
    ax.legend(frameon=False)
    save(fig, "04_daily_visits_by_ai_use.png")

    pre = so[so.month < "2022-12-01"].copy()
    pre["t"] = np.arange(len(pre)) / 12
    pre["month_of_year"] = pre.month.dt.month
    pre["covid"] = pre.month.between("2020-03-01", "2020-06-01").astype(int)
    model = smf.ols("np.log(questions) ~ t + covid + C(month_of_year)", data=pre).fit()
    prediction = model.get_prediction(so.assign(t=np.arange(len(so)) / 12, month_of_year=so.month.dt.month, covid=0)).summary_frame()
    post = so.month >= "2022-12-01"
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.fill_between(so.loc[post, "month"], np.exp(prediction.loc[post, "mean_ci_lower"]) / 1000, np.exp(prediction.loc[post, "mean_ci_upper"]) / 1000, color=MUTED, alpha=.2)
    ax.plot(so.month, so.questions / 1000, color=BLUE, lw=2, label="Observed")
    ax.plot(so.month, np.exp(prediction["mean"]) / 1000, color=MUTED, ls="--", label="Pre-ChatGPT trend projected")
    ax.set(title="Observed questions fell below the earlier trend", ylabel="New questions per month (thousands)", xlabel="")
    ax.legend(frameon=False)
    save(fig, "05_pre_chatgpt_trend_projection.png")

    fig, ax = plt.subplots(figsize=(8, 4.5))
    counts = survey.groupby(["year", "uses_ai"]).size().unstack(fill_value=0)
    counts.div(counts.sum(axis=1), axis=0).plot(kind="bar", stacked=True, ax=ax, color=[MUTED, ORANGE, BLUE])
    ax.set(title="AI-use categories shifted in the developer survey", ylabel="Share of respondents", xlabel="Survey year")
    ax.legend(title="Reported AI use", frameon=False, bbox_to_anchor=(1, 1))
    save(fig, "06_survey_ai_use_categories.png")


if __name__ == "__main__":
    main()
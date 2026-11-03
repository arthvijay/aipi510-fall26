# The Untold Story of Public Programming Help

Stack Overflow questions fell sharply as ChatGPT usage expanded, but the decline was already underway before ChatGPT launched.

## Overview

This project examines how public signals of programming help-seeking changed from 2018 through August 2026. It combines monthly Stack Overflow question counts, publicly announced ChatGPT weekly-user milestones, and Stack Overflow Developer Survey responses from 2023–2025.

## Why This Matters

Students, programmers, educators, and online knowledge-community participants often treat platform activity as a proxy for where people learn. The project shows why that proxy needs context: platform volume, AI adoption, and self-reported behavior move together in time, but the data does not establish that one caused another.

## Research Question

How did Stack Overflow question volume and developers' reported Stack Overflow habits change as generative AI became more widely used?

## Dataset

- **Stack Overflow questions:** Stack Exchange API 2.3 `/questions`, `site=stackoverflow`, `sort=creation`, `filter=total`, one request per month from January 2018 through August 2026. The unit is one month; the value is the API's total number of questions created in that month.
- **ChatGPT users:** 11 public OpenAI or reputable news announcements compiled in `data/raw/chatgpt_weekly_users.csv`. Values are weekly active users in millions as phrased by the source, so they are milestones, not a continuous series.
- **Developer survey:** Stack Overflow Developer Survey 2023, 2024, and 2025, using `AISelect` and `SOVisitFreq`. The unit is one survey respondent. Source: [Stack Overflow Survey repository](https://github.com/StackExchange/Survey).

The analysis snapshot was prepared on 2026-09-20. The monthly series contains 104 observations; the cleaned survey projection contains 203,812 respondent rows. Survey raw files are intentionally ignored because each is larger than GitHub's 100 MB file limit. They can be regenerated with the download command below.

## Repository Structure

```text
data/raw/       API and compiled source snapshots; large survey CSVs are ignored
data/clean/     cleaned inputs and feature tables
src/download.py collection functions
src/preprocess.py cleaning entry point
src/feature_engineering.py derived analysis variables
src/analyze.py verified metrics table
src/visualize.py publication figures
outputs/        figures and key_metrics.csv
docs/           project dossier and communication plan
```

## Data Pipeline

1. `src/download.py` collects Stack Exchange counts and downloads survey source files. It also records the public sources for the ChatGPT milestones.
2. `src/preprocess.py` runs the cleaning functions in `src/clean.py`. Dates are parsed, rows are sorted, survey response labels are harmonized, and missing survey responses remain missing.
3. `src/feature_engineering.py` creates year, month name, year-over-year change, post-launch indicator, log count, rolling median, and binary survey indicators.
4. `src/analyze.py` writes `outputs/tables/key_metrics.csv`, the numeric source of truth for the narrative.
5. `src/visualize.py` regenerates six final PNG figures.

## Key Findings

1. Monthly Stack Overflow questions fell from 160,440 in January 2018 to 1,130 in August 2026, a 99.30% decrease across the snapshot.
2. The decline predates ChatGPT: the largest year-over-year decline through 2022 was 17.29%, while the pre-December-2022 modeled trend was -7.71% per year after month and early-pandemic adjustments.
3. The decline accelerated after 2022: annual questions fell 41.00% in 2023, 49.42% in 2024, and 72.45% in 2025.
4. Among survey respondents who reported AI use and answered the visit question, daily or almost-daily Stack Overflow visits fell from 40.73% in 2023 to 23.19% in 2025. This is an association across survey snapshots, not a causal estimate.

## Reproducing the Analysis

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env

# Optional: put a real Stack Exchange API key in .env.
# Download survey source CSVs and refresh the public snapshots:
python src/download.py

python src/preprocess.py
python src/feature_engineering.py
python src/analyze.py
python src/visualize.py
```

When the large survey downloads are absent, `src/preprocess.py` retains the committed cleaned survey snapshot and prints that decision. This makes the committed analysis runnable without silently pretending that the raw survey files are present.

## Outputs

The final figures are in `outputs/figures/`; the validated narrative numbers are in `outputs/tables/key_metrics.csv`. The full analysis, chart catalog, presentation outline, infographic hierarchy, and written explanation are in [docs/project_dossier.md](docs/project_dossier.md).

## Limitations and Ethics

The data is observational, platform-specific, and affected by API definitions, changing site behavior, survey nonresponse, and the fact that older posts have had more time to accumulate activity. ChatGPT user milestones are irregular public announcements, not a comparable time series. Public availability does not make individual behavior fair game for targeting, so this project reports aggregate patterns only. Views, scores, answers, and visits should not be treated as direct measures of developer ability or content quality.

## Audit Status

Dataset documentation, preprocessing scripts, feature engineering, EDA, figures, raw/clean data instructions, README, reproduction instructions, limitations, ethics, presentation material, and infographic material are **READY**. Branch and pull-request evidence is **ACTION REQUIRED**: the repository currently has one commit, one branch, and one contributor. Each collaborator must create and review a genuine feature branch and pull request before submission.

## Contributors

- [Shenwei Zhang](https://github.com/sz381)
- [Arthvijay](https://github.com/arthvijay)

Any additional group member should be added after their GitHub identity is verified and their genuine contribution is recorded.

## Data Citation

Stack Exchange. *Stack Overflow questions API*, API version 2.3, site `stackoverflow`, accessed 2026-09-20. Stack Overflow. *Annual Developer Survey 2023–2025*, [StackExchange/Survey](https://github.com/StackExchange/Survey). ChatGPT milestone sources are recorded row-by-row in `data/raw/chatgpt_weekly_users.csv`.

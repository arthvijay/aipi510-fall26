# k-NN Standardization Statistical Study

**Author:** Arth Vijaywargia  
**Course:** AIPI 510 — Module Project 2: Statistical Analysis

## Study

This reproducible study tests whether within-fold Z-score standardization
improves k-nearest-neighbor classification of commercial-credit defaults when
features have heterogeneous scales. The canonical analysis CSVs are stored in
`data/raw/` and `data/processed/`. The data are a controlled Monte Carlo
simulation (`SEED = 42`), not sensitive borrower records. The clean cohort has
600 records (360 performing, 240 defaulted) and eight quantitative features.

The exact data-generating process is: revenue is Normal(425000, 165000²) for
performing and Normal(398000, 170000²) for defaulted borrowers; principal is
Normal(132000, 56000²) and Normal(141000, 59000²); enterprise age is
Gamma(3.8, 2.6)+1.2 and Gamma(2.6, 2.2)+1.0; working-capital days is
Normal(54.0, 21.0²) and Normal(69.5, 23.5²); debt-to-income is
Normal(0.26, 0.095²) and Normal(0.43, 0.105²); utilization is
Normal(0.36, 0.165²) and Normal(0.64, 0.170²); delinquency is
Exponential(rate=0.045) and Normal(0.165, 0.075²); and timeliness is
Normal(0.84, 0.088²) and Normal(0.66, 0.105²). Values are clipped to
documented financial bounds and rounded to the specified precision.
The raw ingestion file adds 19 missing values, 11 corrupted out-of-range values,
and 18 exact duplicates (648 rows). Cleaning deduplicates, removes missing
required features, validates domains, and verifies the supplied 600-row clean
cohort.

The primary experiment uses 50 matched folds, k=5, Euclidean distance, and
within-training-fold scaling. It reports accuracy, precision, recall, F1,
ROC-AUC, paired t, Nadeau-Bengio correction, Wilcoxon, Shapiro-Wilk,
Kolmogorov-Smirnov, Cohen's d, Hedges' g, Friedman, and corrected post-hoc
comparisons. The current run found a 40.07 percentage-point mean accuracy gain
for Z-score scaling (paired p < 0.001).

## Reproduction

```bash
python3 -m pip install -r requirements.txt
python3 run_all.py
```

All analysis is implemented in Python scripts under `src/`; no notebooks are
required. Scaling objects are fit only on each training partition, preventing
test-fold leakage. The primary design is 10 repeats of 5-fold stratified
cross-validation (50 paired folds), with paired t, Nadeau-Bengio corrected t,
Wilcoxon, normality diagnostics, effect sizes, sensitivity across k and metric,
and Friedman comparison of four scaling methods.

Outputs are written to `results/`, including CSV tables, JSON summary, and six
200-DPI figures. The raw and processed datasets are in `data/`.

## Solo Git workflow

The project is organized as two reviewable feature branches: a data-pipeline
change and a statistical-analysis/visualization change. The pull-request
template records checks for deterministic simulation, leakage prevention, row
counts, and statistical validation. A solo researcher can use the same
branch-and-self-review workflow to preserve reproducible history.

## Data-pipeline PR review record

- [x] Canonical raw and processed CSVs are stored under `data/`.
- [x] Raw input has 648 rows; the cleaned cohort has 600 rows and 12 columns.
- [x] Cleaning stages reproduce the supplied cohort deterministically.
- [x] Missingness and domain checks are applied after exact deduplication.
- [x] `python3 run_all.py` validates the required data outputs.

## Statistical-analysis PR review record

- [x] Repeated stratified CV uses 10 repeats and 5 folds with seed 42.
- [x] Every scaler is fitted within each training fold only.
- [x] Paired t, Nadeau-Bengio, Wilcoxon, normality, effect-size, and Friedman
  diagnostics are exported in `results/experiment_summary.json`.
- [x] Holm-Bonferroni and Bonferroni corrections cover all requested k values
  and both distance metrics.
- [x] Six 200-DPI figures and all result tables are regenerated successfully.

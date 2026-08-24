# AutoQuant V2: Eredivisie 70/30 Statistical Audit

❌ VERDICT: This result does not hold up to scrutiny — treat as a false positive, do not deploy. It fails at least one of the strict audit constraints (Precision, Bonferroni, or Consistency).

## 1 & 2. Significance & Multiple-Comparisons (Bonferroni) Audit
Bootstrap Method: Percentile Bootstrap (1,000 resampled means with replacement). Fixed Seed: `np.random.seed(42)`.
- **Nominal 95% CI Lower Bound**: `0.007739%`
- **Nominal 95% CI Upper Bound**: `0.346497%`
- **Bonferroni-Corrected (99.29%) Lower Bound**: `-0.072508%`
- **Bonferroni-Corrected (99.29%) Upper Bound**: `0.402755%`

## 3. Fold-by-Fold CLV Breakdown (Weight_70_30)
Aggregate edge was positive, but only 4 of 5 seasons were individually positive.
| Season | Bets Placed | Avg CLV |
|---|---|---|
| 2019-2020 | 129 | 0.5586% |
| 2020-2021 | 246 | 0.4825% |
| 2021-2022 | 269 | 0.0064% |
| 2022-2023 | 266 | 0.1242% |
| 2023-2024 | 229 | -0.1232% |

## 4. Pinnacle Closing Odds Data Quality
Total Matches Evaluated: 1403
Matches Missing PSCH: 0
Matches Missing PSCA: 0
No missing or interpolated lines were used in the CLV calculation; if a match lacked closing lines, it was strictly excluded from the CLV array.
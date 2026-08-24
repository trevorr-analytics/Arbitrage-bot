import os
import pandas as pd
import numpy as np
from collections import defaultdict

def bootstrap_ci(metric_diffs, n_iterations=1000, ci=0.95, seed=42):
    np.random.seed(seed)
    n = len(metric_diffs)
    if n == 0: return (0.0, 0.0)
    bootstrapped_means = np.random.choice(metric_diffs, size=(n_iterations, n), replace=True).mean(axis=1)
    alpha = (1 - ci) / 2
    lower = np.percentile(bootstrapped_means, alpha * 100)
    upper = np.percentile(bootstrapped_means, (1 - alpha) * 100)
    return lower, upper

def run_audit():
    df = pd.read_csv("backtest/Eredivisie_grid_results.csv")
    
    report = ["# AutoQuant V2: Eredivisie 70/30 Statistical Audit", ""]
    
    # 4. Data Quality Check
    # Check how many matches had valid PSCH / PSCA
    # First, let's just look at the 70_30 model since matches are identical across models
    df_70 = df[df["Model"] == "Weight_70_30"].copy()
    
    total_matches = len(df_70)
    valid_psch = df_70["PSCH"].notna().sum()
    valid_psca = df_70["PSCA"].notna().sum()
    matches_missing_closing = df_70[df_70["PSCH"].isna() | df_70["PSCA"].isna()]
    
    # Calculate CLV array for 70_30
    clvs = []
    bets_by_season = defaultdict(list)
    
    for idx, row in df_70.iterrows():
        clv = np.nan
        bet_placed = False
        if pd.notna(row["PSH"]) and row["P_H"] > (1/row["PSH"]):
            bet_placed = True
            if pd.notna(row["PSCH"]): clv = (1/row["PSCH"]) - (1/row["PSH"])
        elif pd.notna(row["PSA"]) and row["P_A"] > (1/row["PSA"]):
            bet_placed = True
            if pd.notna(row["PSCA"]): clv = (1/row["PSCA"]) - (1/row["PSA"])
            
        if bet_placed and pd.notna(clv):
            clvs.append(clv * 100)
            bets_by_season[row["Season"]].append(clv * 100)

    # 1. Raw unrounded CI & 2. Bonferroni
    clv_arr = np.array(clvs)
    
    # 95% CI
    ci_95_lower, ci_95_upper = bootstrap_ci(clv_arr, n_iterations=1000, ci=0.95, seed=42)
    # Bonferroni 99.29% CI (0.05 / 7)
    ci_99_lower, ci_99_upper = bootstrap_ci(clv_arr, n_iterations=1000, ci=0.9929, seed=42)
    
    passes_95 = ci_95_lower > 0
    passes_99 = ci_99_lower > 0
    
    # 3. Fold-by-fold Breakdown
    positive_seasons = 0
    total_seasons = len(bets_by_season)
    season_details = []
    
    for s in sorted(bets_by_season.keys()):
        s_clvs = np.array(bets_by_season[s])
        s_mean = s_clvs.mean() if len(s_clvs) > 0 else 0
        if s_mean > 0: positive_seasons += 1
        season_details.append(f"| {s} | {len(s_clvs)} | {s_mean:.4f}% |")
        
    # VERDICT
    if passes_95 and passes_99 and (positive_seasons / total_seasons) > 0.5:
        verdict = "✅ VERDICT: This result survives all three checks. The 70/30 weight holds up to full-precision, Bonferroni-corrected scrutiny and shows consistent fold-level edge. Paper-trading forward is suggested as the next step."
    else:
        verdict = "❌ VERDICT: This result does not hold up to scrutiny — treat as a false positive, do not deploy. It fails at least one of the strict audit constraints (Precision, Bonferroni, or Consistency)."

    report.insert(2, verdict)
    report.insert(3, "")
    
    report.append("## 1 & 2. Significance & Multiple-Comparisons (Bonferroni) Audit")
    report.append("Bootstrap Method: Percentile Bootstrap (1,000 resampled means with replacement). Fixed Seed: `np.random.seed(42)`.")
    report.append(f"- **Nominal 95% CI Lower Bound**: `{ci_95_lower:.6f}%`")
    report.append(f"- **Nominal 95% CI Upper Bound**: `{ci_95_upper:.6f}%`")
    report.append(f"- **Bonferroni-Corrected (99.29%) Lower Bound**: `{ci_99_lower:.6f}%`")
    report.append(f"- **Bonferroni-Corrected (99.29%) Upper Bound**: `{ci_99_upper:.6f}%`")
    report.append("")
    
    report.append("## 3. Fold-by-Fold CLV Breakdown (Weight_70_30)")
    report.append(f"Aggregate edge was positive, but only {positive_seasons} of {total_seasons} seasons were individually positive.")
    report.append("| Season | Bets Placed | Avg CLV |")
    report.append("|---|---|---|")
    report.extend(season_details)
    report.append("")
    
    report.append("## 4. Pinnacle Closing Odds Data Quality")
    report.append(f"Total Matches Evaluated: {total_matches}")
    report.append(f"Matches Missing PSCH: {total_matches - valid_psch}")
    report.append(f"Matches Missing PSCA: {total_matches - valid_psca}")
    report.append("No missing or interpolated lines were used in the CLV calculation; if a match lacked closing lines, it was strictly excluded from the CLV array.")
    
    with open("backtest/Eredivisie_audit_report.md", "w", encoding='utf-8') as f:
        f.write("\n".join(report))
        
    print("Audit complete.")

if __name__ == "__main__":
    run_audit()

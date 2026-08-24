import pandas as pd
from dixon_coles import DixonColesModel, load_league_data

# Grab one league to test, e.g. Eredivisie
df = load_league_data("Eredivisie")
print(f"Loaded {len(df)} matches. Fitting model...")

model = DixonColesModel(use_xg=True, xg_weight=0.7)
model.fit(df, "Eredivisie")

elo_coef = model.params_[-1]
print(f"Elo Coefficient learned by Poisson GLM: {elo_coef:.4f}")
print("Top 5 current Elos:")
sorted_elos = sorted(model.current_elos_.items(), key=lambda x: x[1], reverse=True)
for k, v in sorted_elos[:5]:
    print(f"  {k}: {v:.1f}")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from helper_functions import fit_bass_nls, adopters_between, bass_F, peak_time
from plot_style import apply_style, BLUE, ORANGE, TEXT_2

LAUNCH = pd.Timestamp("2017-03-03")
DAYS_PER_YEAR = 365.25

df = pd.read_csv("data/nintendo_switch_hardware_units.csv",
                 parse_dates=["period_start", "period_end"])
df["t_end"] = ((df["period_end"] - LAUNCH).dt.days + 1) / DAYS_PER_YEAR
df["t_start"] = np.r_[0.0, df["t_end"].values[:-1]]
sales = df["units_million"]

fit = fit_bass_nls(df["t_start"], df["t_end"], sales)
# 8 significant digits, so later rounding happens only once (in the report)
pd.DataFrame([fit]).to_csv("data/bass_parameters.csv", index=False, float_format="%.8g")

p, q, M = fit["p"], fit["q"], fit["M"]
t_star = peak_time(p, q)
peak_date = LAUNCH + pd.Timedelta(days=t_star * DAYS_PER_YEAR)
print(f"p = {p:.4f} (95% CI {fit['p_low95']:.4f} to {fit['p_high95']:.4f})")
print(f"q = {q:.4f} (95% CI {fit['q_low95']:.4f} to {fit['q_high95']:.4f})")
print(f"M = {M:.1f}M units (95% CI {fit['M_low95']:.1f} to {fit['M_high95']:.1f})")
print(f"Correlation between the p and q estimates = {fit['corr_pq']:.2f}")
print(f"R^2 = {fit['r2']:.4f}, n = {fit['n_obs']}")
print(f"Peak: t* = {t_star:.2f} years -> {peak_date:%B %Y}")
print(f"Model cumulative to 31 Mar 2026: {M * bass_F(df['t_end'].iloc[-1], p, q):.1f}M "
      f"(actual {sales.sum():.2f}M)")

fitted = adopters_between(df["t_start"], df["t_end"], p, q, M)
out = df[["fiscal_year", "units_million"]].copy()
out["fitted_million"] = fitted.round(2)
out.to_csv("data/switch_actual_vs_fitted.csv", index=False)
print(out.to_string(index=False))

# ---- Robustness: does the answer depend on how the periods are set up? ----
te = df["t_end"].values
y = sales.values
n = len(y)
versions = [
    ("Main fit: each period keeps its real length", df["t_start"].values, te, y),
    ("Launch month treated as a full year (t = 1, 2, ..., 10)", np.arange(n), np.arange(1, n + 1), y),
    ("Launch month merged into FY2018", np.r_[0.0, te[1:-1]], te[1:], np.r_[y[0] + y[1], y[2:]]),
    ("Without FY2026 (the year Switch 2 launched)", df["t_start"].values[:-1], te[:-1], y[:-1]),
]
rob = []
for label, t0, t1, yy in versions:
    f = fit_bass_nls(t0, t1, yy)
    rob.append({"version": label, "p": f["p"], "q": f["q"], "M": f["M"],
                "r2": f["r2"], "n_obs": f["n_obs"]})
rob = pd.DataFrame(rob)
rob.to_csv("data/robustness_fits.csv", index=False, float_format="%.4f")
print("\nRobustness checks:\n", rob.round(4).to_string(index=False))

# ---- Figure: actual vs fitted sales per fiscal year ----
apply_style()
labels = [fy.replace("FY3/", "FY") for fy in df["fiscal_year"]]
labels[0] += "*"
x = np.arange(len(df))
fig, ax = plt.subplots(figsize=(9, 4.6))
ax.bar(x, sales, width=0.7, color=BLUE, label="Actual (Nintendo reports)", zorder=2)
ax.plot(x, fitted, color=ORANGE, lw=2.2, marker="o", ms=4, label="Bass model fit", zorder=3)
ax.set_xticks(x, labels)
ax.set_title("Nintendo Switch units sold per fiscal year vs. Bass model fit", loc="left")
ax.set_ylabel("Units sold (millions)")
ax.set_ylim(0, 33)
handles, labels_ = ax.get_legend_handles_labels()
ax.legend(handles[::-1], labels_[::-1], loc="upper right", frameon=False)
ax.text(0.02, 0.93, f"p = {p:.3f}   q = {q:.3f}   M = {M:.0f}M   R² = {fit['r2']:.2f}",
        transform=ax.transAxes, color=TEXT_2, fontsize=10)
ax.set_xlabel("Nintendo fiscal years run April to March (FY2021 = Apr 2020 to Mar 2021).  "
              "* FY2017 = launch month only (3-31 Mar 2017)", fontsize=8, color=TEXT_2)
fig.tight_layout()
fig.savefig("img/switch_bass_fit.png", dpi=200)
print("Saved img/switch_bass_fit.png")

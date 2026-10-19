import calendar
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from helper_functions import adopters_between, bass_F, peak_time
from plot_style import apply_style, BLUE, BLUE_LIGHT, TEXT_2

LAUNCH = pd.Timestamp("2025-10-16")
DAYS_PER_YEAR = 365.25
YEARS = list(range(2025, 2035))
N_DRAWS = 10_000
SEED = 2025


def t_years(date):
    """Years from the launch to the end of `date` (the end date is included)."""
    return ((pd.Timestamp(date) - LAUNCH).days + 1) / DAYS_PER_YEAR


def to_date(t):
    """Calendar date that is t years after the launch."""
    return LAUNCH + pd.Timedelta(days=float(t) * DAYS_PER_YEAR)


# ---- Parameters from the look-alike ----
fit = pd.read_csv("data/bass_parameters.csv").iloc[0]
p, q = fit["p"], fit["q"]

# ---- Fermi estimate of M ----
inp = pd.read_csv("data/market_potential_inputs.csv").set_index("input")["value"]
s2025, s2029 = inp["pc_handheld_sales_2025"], inp["pc_handheld_sales_2029"]
window = int(inp["selling_window_years"])
growth = (s2029 / s2025) ** (1 / 4) - 1          # constant growth 2025 -> 2029 (Omdia's two points)
window_end = LAUNCH + pd.DateOffset(years=window) - pd.Timedelta(days=1)   # 15 Oct 2033

path = []
for y in range(LAUNCH.year, window_end.year + 1):
    annual = s2025 * (1 + growth) ** (y - 2025) if y <= 2029 else s2029   # flat after Omdia's horizon
    start = max(LAUNCH, pd.Timestamp(f"{y}-01-01"))
    end = min(window_end, pd.Timestamp(f"{y}-12-31"))
    days = (end - start).days + 1
    share_of_year = days / (366 if calendar.isleap(y) else 365)
    path.append({"year": y, "annual_pc_handheld_sales_million": annual,
                 "days_in_window": days, "sales_in_window_million": annual * share_of_year})
path = pd.DataFrame(path)
market_total = path["sales_in_window_million"].sum()
path.to_csv("data/pc_handheld_market_path.csv", index=False, float_format="%.3f")

shares = {"low": inp["allyx_share_low"], "base": inp["allyx_share_base"], "high": inp["allyx_share_high"]}
M = {k: market_total * v for k, v in shares.items()}  # millions of units

print(f"p = {p:.4f}, q = {q:.4f}")
print(f"Selling window: {LAUNCH:%d %b %Y} to {window_end:%d %b %Y}; Omdia path growth {growth:.1%}/yr")
print(path.round(3).to_string(index=False))
print(f"PC-handheld sales inside the window = {market_total:.2f}M")
for k, v in M.items():
    print(f"M_{k} = {market_total:.2f}M x {shares[k]:.0%} = {v:.2f}M units")

# ---- Adopters per calendar year ----
t_end = np.array([t_years(f"{y}-12-31") for y in YEARS])
t_start = np.r_[0.0, t_end[:-1]]
rows = {"year": YEARS, "years_since_launch_end": t_end.round(3)}
for k, m in M.items():
    rows[f"new_adopters_{k}"] = adopters_between(t_start, t_end, p, q, m * 1e6).round(0).astype(int)
for k, m in M.items():
    rows[f"cumulative_adopters_{k}"] = (m * 1e6 * bass_F(t_end, p, q)).round(0).astype(int)
fc = pd.DataFrame(rows)
fc.to_csv("data/allyx_forecast.csv", index=False)

t_star = peak_time(p, q)
f_window = bass_F(t_years(window_end), p, q)
print(f"\nPeak adoption rate at t* = {t_star:.2f} years -> {to_date(t_star):%B %Y}")
print(f"Share of M reached by the end of the selling window ({window_end:%d %b %Y}): {f_window:.1%}")
print(fc.to_string(index=False))

# ---- Uncertainty in p and q (base M) ----
# The p and q estimates move in opposite directions (negative correlation), so
# they are drawn together from their estimated joint distribution instead of
# being set to the ends of their separate 95% intervals at the same time.
cov = np.array([[fit["se_p"] ** 2, fit["cov_pq"]],
                [fit["cov_pq"], fit["se_q"] ** 2]])
rng = np.random.default_rng(SEED)
draws = rng.multivariate_normal([p, q], cov, size=N_DRAWS)
draws = draws[(draws > 0).all(axis=1)]
ps, qs = draws[:, 0], draws[:, 1]
t27, t30 = t_years("2027-12-31"), t_years("2030-12-31")
measures = {
    "Peak of the adoption rate": (t_star, peak_time(ps, qs)),
    "Cumulative adopters by end of 2027": (M["base"] * 1e6 * bass_F(t27, p, q),
                                           M["base"] * 1e6 * bass_F(t27, ps, qs)),
    "Cumulative adopters by end of 2030": (M["base"] * 1e6 * bass_F(t30, p, q),
                                           M["base"] * 1e6 * bass_F(t30, ps, qs)),
}
sens = []
for name, (main, sims) in measures.items():
    lo, hi = np.percentile(sims, [2.5, 97.5])
    if name.startswith("Peak"):
        sens.append({"measure": name, "main_estimate": f"{to_date(main):%b %Y}",
                     "low_2.5pct": f"{to_date(lo):%b %Y}", "high_97.5pct": f"{to_date(hi):%b %Y}"})
    else:
        sens.append({"measure": name, "main_estimate": round(main),
                     "low_2.5pct": round(lo), "high_97.5pct": round(hi)})
sens = pd.DataFrame(sens)
sens.to_csv("data/sensitivity_pq.csv", index=False)
print(f"\nJoint p-q uncertainty ({len(ps):,} draws, correlation {fit['corr_pq']:.2f}), base M:")
print(sens.to_string(index=False))

# ---- Cross-checks against outside data ----
cc = pd.read_csv("data/cross_check_inputs.csv").set_index("input")["value"]
price = cc["allyx_price"]
q4_low = cc["ally_line_revenue_q4_2025_low"] * 1e6 / price
q4_high = cc["ally_line_revenue_q4_2025_high"] * 1e6 / price
yr_low = 4 * cc["ally_line_revenue_per_quarter_low"] * 1e6 / price
yr_high = 4 * cc["ally_line_revenue_per_quarter_high"] * 1e6 / price
deck = cc["steam_deck_shipments_2022_2024"] * 1e6
by_year = fc.set_index("year")
checks = pd.DataFrame([
    {"check": "2025 launch period: base forecast vs ASUS Q4 2025 Ally-line revenue / $999.99",
     "model": by_year.loc[2025, "new_adopters_base"],
     "benchmark_low": round(q4_low), "benchmark_high": round(q4_high)},
    {"check": "2026: base forecast vs ASUS Ally-line revenue per quarter x 4 / $999.99",
     "model": by_year.loc[2026, "new_adopters_base"],
     "benchmark_low": round(yr_low), "benchmark_high": round(yr_high)},
    {"check": "Base share vs Ally-line revenue ceiling as a share of 2025 PC-handheld sales",
     "model": shares["base"],
     "benchmark_low": round(yr_low / (s2025 * 1e6), 3), "benchmark_high": round(yr_high / (s2025 * 1e6), 3)},
    {"check": "Cumulative by end of 2028 (base) vs Steam Deck shipments 2022-2024 (IDC)",
     "model": by_year.loc[2028, "cumulative_adopters_base"],
     "benchmark_low": round(deck), "benchmark_high": round(deck)},
])
checks.to_csv("data/cross_checks.csv", index=False, float_format="%.10g")
print("\nCross-checks:")
print(checks.to_string(index=False))
print(f"Ally X by end of 2028 = {by_year.loc[2028, 'cumulative_adopters_base'] / deck:.0%} of Steam Deck 2022-2024")

# ---- Figures ----
apply_style()
x = np.arange(len(YEARS))
for kind, fname, title, ylab, scale, fmt in [
    ("new_adopters", "img/allyx_new_adopters.png",
     "ROG Xbox Ally X: predicted new adopters per year (worldwide)",
     "Units per year (thousands)", 1e3, "{:,.0f}k"),
    ("cumulative_adopters", "img/allyx_cumulative_adopters.png",
     "ROG Xbox Ally X: predicted cumulative adopters (worldwide)",
     "Units (millions)", 1e6, "{:,.1f}M"),
]:
    fig, ax = plt.subplots(figsize=(9, 4.4))
    ax.fill_between(x, fc[f"{kind}_low"] / scale, fc[f"{kind}_high"] / scale,
                    color=BLUE_LIGHT, lw=0, label="Low to high M scenario")
    ax.plot(x, fc[f"{kind}_base"] / scale, color=BLUE, lw=2.2, marker="o", ms=4,
            label=f"Base scenario (M = {M['base']:.1f}M)")
    labels = ["2025*"] + [str(y) for y in YEARS[1:]]
    ax.set_xticks(x, labels)
    ax.set_title(title, loc="left")
    ax.set_ylabel(ylab)
    ax.set_ylim(bottom=0)
    ax.legend(loc="upper left" if kind == "cumulative_adopters" else "upper right", frameon=False)
    ax.set_xlabel("* 2025 = launch period only (16 Oct to 31 Dec 2025)", fontsize=8, color=TEXT_2)
    if kind == "new_adopters":
        i = int(np.argmax(fc["new_adopters_base"]))
        ax.annotate(f"Peak year {YEARS[i]}: " + fmt.format(fc[f"{kind}_base"][i] / scale),
                    (i, fc[f"{kind}_base"][i] / scale), xytext=(0, 10), textcoords="offset points",
                    ha="center", fontsize=9, color=TEXT_2)
    else:
        ax.annotate(fmt.format(fc[f"{kind}_base"].iloc[-1] / scale), (x[-1], fc[f"{kind}_base"].iloc[-1] / scale),
                    xytext=(6, 0), textcoords="offset points", va="center", fontsize=9, color=TEXT_2)
    fig.tight_layout()
    fig.savefig(fname, dpi=200)
    print("Saved", fname)

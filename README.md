# Bass Model Homework: ROG Xbox Ally X

Forecasting the worldwide diffusion of the **ROG Xbox Ally X** (TIME Best Inventions 2025, Entertainment and Gaming) using the **Nintendo Switch** as the look-alike innovation.

- Innovation: <https://time.com/collections/best-inventions-2025/7318306/xbox-rog-ally-x/>
- Full report: [`report/report.pdf`](report/report.pdf) (source: [`report/report_source.md`](report/report_source.md))

## Key results

| | Value |
|---|---|
| Look-alike data | Nintendo Switch units sold per fiscal year, FY2017–FY2026 (all values from Nintendo's official results; no estimates) |
| Coefficient of innovation *p* | 0.063 (95% CI 0.043–0.083) |
| Coefficient of imitation *q* | 0.494 (95% CI 0.356–0.631) |
| Fit (R²) | 0.94 |
| Scope | Worldwide |
| Market potential *M* (Fermi) | 3.3M / **4.9M** / 8.2M units (low / base / high) |
| Units in 2026 (base) | ~418,000 |
| Peak year | 2029 (~771,000 units) |
| Cumulative units by 2034 (base) | ~4.7 million |

## Project structure

```
├── README.md                  This file
├── requirements.txt           Python packages (versions used to produce the results)
├── helper_functions.py        Bass model functions (F(t), f(t), NLS fitting with uneven periods)
├── plot_style.py              Shared chart colors and style
├── fit_lookalike.py           Step 4: estimates p, q, M on Nintendo Switch data, robustness checks, fit chart
├── forecast_allyx.py          Steps 5–7: Fermi estimate of M, adopters per year, uncertainty, cross-checks
├── data/
│   ├── nintendo_switch_hardware_units.csv  Look-alike data with a source for every row
│   ├── market_potential_inputs.csv         Inputs to the Fermi estimate of M, with sources
│   ├── cross_check_inputs.csv              Outside data used to check the forecast, with sources
│   ├── bass_parameters.csv                 Output: p, q, M with standard errors, 95% intervals, p-q covariance
│   ├── switch_actual_vs_fitted.csv         Output: actual vs fitted Switch sales
│   ├── robustness_fits.csv                 Output: p, q, M under three other ways of setting up the data
│   ├── pc_handheld_market_path.csv         Output: PC-handheld sales inside the 8-year selling life (used for M)
│   ├── allyx_forecast.csv                  Output: new and cumulative adopters, 2025–2034
│   ├── sensitivity_pq.csv                  Output: 95% range of the forecast from joint p-q uncertainty
│   └── cross_checks.csv                    Output: forecast vs ASUS revenue guidance and Steam Deck shipments
├── img/
│   ├── switch_bass_fit.png                 Actual vs fitted Switch sales
│   ├── allyx_new_adopters.png              Predicted new adopters per year
│   └── allyx_cumulative_adopters.png       Predicted cumulative adopters
├── report/
│   ├── report_source.md                    Report source (Markdown)
│   └── report.pdf                          Final report
└── references/
    └── references.md                       All sources with links
```

## How to run

Tested with Python 3.13 and the package versions in `requirements.txt`. Run from the project root:

```bash
pip install -r requirements.txt
python fit_lookalike.py     # writes data/bass_parameters.csv, data/robustness_fits.csv and img/switch_bass_fit.png
python forecast_allyx.py    # writes data/allyx_forecast.csv, the uncertainty and cross-check tables, and the two forecast charts
```

To rebuild the PDF (needs pandoc and a LaTeX engine):

```bash
cd report
pandoc report_source.md -o report.pdf --pdf-engine=xelatex \
  -V fontfamily=fontspec -V mainfont="DejaVu Serif" -V sansfont="DejaVu Sans" -V monofont="DejaVu Sans Mono"
```

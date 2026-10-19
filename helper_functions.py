import numpy as np
from scipy import stats
from scipy.optimize import least_squares


def bass_F(t, p, q):
    """Cumulative fraction of the market that has adopted by time t (years)."""
    t = np.asarray(t, dtype=float)
    e = np.exp(-(p + q) * t)
    return (1 - e) / (1 + (q / p) * e)


def bass_f(t, p, q):
    """Adoption rate (density) at time t."""
    t = np.asarray(t, dtype=float)
    e = np.exp(-(p + q) * t)
    return ((p + q) ** 2 / p) * e / (1 + (q / p) * e) ** 2


def adopters_between(t_start, t_end, p, q, M):
    """New adopters between t_start and t_end (years since launch)."""
    return M * (bass_F(t_end, p, q) - bass_F(t_start, p, q))


def peak_time(p, q):
    """Time (years since launch) when the adoption rate peaks: ln(q/p)/(p+q)."""
    return np.log(q / p) / (p + q)


def fit_bass_nls(t_start, t_end, sales, x0=(0.03, 0.4)):
    """Estimate p, q, M by nonlinear least squares on per-period sales.

    t_start, t_end : start and end of each period, in years since launch
    sales          : sales (new adopters) in each period

    Returns dict with p, q, M, standard errors, 95% intervals and R^2.
    """
    t_start = np.asarray(t_start, dtype=float)
    t_end = np.asarray(t_end, dtype=float)
    sales = np.asarray(sales, dtype=float)

    def residuals(theta):
        p, q, M = theta
        return adopters_between(t_start, t_end, p, q, M) - sales

    sol = least_squares(
        residuals,
        x0=[x0[0], x0[1], sales.sum() * 1.2],
        bounds=([1e-6, 1e-4, sales.sum()], [1.0, 3.0, sales.sum() * 20]),
    )
    p, q, M = sol.x
    dof = len(sol.fun) - 3
    sigma2 = (sol.fun ** 2).sum() / dof
    cov = np.linalg.inv(sol.jac.T @ sol.jac) * sigma2
    se = np.sqrt(np.diag(cov))
    tcrit = stats.t.ppf(0.975, dof)

    fitted = adopters_between(t_start, t_end, p, q, M)
    r2 = 1 - ((sales - fitted) ** 2).sum() / ((sales - sales.mean()) ** 2).sum()
    out = {"p": p, "q": q, "M": M, "r2": r2, "n_obs": len(sales)}
    for name, val, s_ in zip(["p", "q", "M"], [p, q, M], se):
        out[f"se_{name}"] = s_
        out[f"{name}_low95"] = val - tcrit * s_
        out[f"{name}_high95"] = val + tcrit * s_
    # p and q are estimated together, so their errors are linked: keep the
    # covariance to simulate them jointly (see forecast_allyx.py)
    out["cov_pq"] = cov[0, 1]
    out["corr_pq"] = cov[0, 1] / (se[0] * se[1])
    return out

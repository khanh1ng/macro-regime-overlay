"""Small statistics toolkit in numpy: OLS with Newey-West errors and Wald tests."""
import numpy as np
from scipy import stats as st


def ols_hac(y, X, lags):
    """OLS coefficients and Newey-West (Bartlett kernel) covariance."""
    y = np.asarray(y, float)
    X = np.asarray(X, float)
    n, k = X.shape
    XtX_inv = np.linalg.inv(X.T @ X)
    b = XtX_inv @ X.T @ y
    u = y - X @ b
    g = X * u[:, None]
    S = g.T @ g
    for L in range(1, lags + 1):
        w = 1 - L / (lags + 1)
        G = g[L:].T @ g[:-L]
        S += w * (G + G.T)
    V = XtX_inv @ S @ XtX_inv
    return b, V


def wald(b, V, Rm, q=None):
    """Chi-square Wald test of Rm b = q. Returns (statistic, p-value)."""
    Rm = np.atleast_2d(Rm)
    q = np.zeros(Rm.shape[0]) if q is None else q
    d = Rm @ b - q
    stat = float(d @ np.linalg.inv(Rm @ V @ Rm.T) @ d)
    return stat, float(st.chi2.sf(stat, Rm.shape[0]))


def contrast(b, V, c):
    """Estimate and t-statistic of the linear combination c'b."""
    c = np.asarray(c, float)
    est = float(c @ b)
    return est, est / float(np.sqrt(c @ V @ c))

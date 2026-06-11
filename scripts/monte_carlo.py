"""
Bluestock MF Capstone — Monte Carlo NAV Projection (B3 bonus)

Projects NAV growth over 5 years using Geometric Brownian Motion
with median path and 5th/95th percentile uncertainty bands.

Usage:
    python scripts/monte_carlo.py
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go

logging.basicConfig(level=logging.INFO, format="%(asctime)s — %(levelname)s — %(message)s")
log = logging.getLogger(__name__)

BASE = Path(__file__).resolve().parent.parent
PROCESSED = BASE / "data" / "processed"
CHARTS = BASE / "charts"
CHARTS.mkdir(parents=True, exist_ok=True)


def monte_carlo_nav(nav_series, n_simulations=1000, n_days=252 * 5):
    """
    Projects NAV growth over n_days using Geometric Brownian Motion.
    Returns array of shape (n_simulations, n_days).
    """
    daily_returns = nav_series.pct_change().dropna()
    mu = daily_returns.mean()
    sigma = daily_returns.std()
    last_nav = nav_series.iloc[-1]

    simulations = np.zeros((n_simulations, n_days))
    for i in range(n_simulations):
        shocks = np.random.normal(mu, sigma, n_days)
        price_path = last_nav * np.cumprod(1 + shocks)
        simulations[i] = price_path

    return simulations


def main():
    log.info("Loading NAV data...")
    nav = pd.read_csv(PROCESSED / "nav_history.csv")
    nav["date"] = pd.to_datetime(nav["date_id"])

    fund = pd.read_csv(PROCESSED / "fund_master.csv")
    scheme = fund.iloc[0]["scheme_name"]
    code = fund.iloc[0]["amfi_code"]

    series = nav[nav["amfi_code"] == code].sort_values("date")["nav"]
    if len(series) < 100:
        log.error("Insufficient NAV data for %s", scheme)
        return

    log.info("Running Monte Carlo for %s (code %d)...", scheme, code)
    sims = monte_carlo_nav(series, n_simulations=1000, n_days=252 * 5)

    median = np.percentile(sims, 50, axis=0)
    lower = np.percentile(sims, 5, axis=0)
    upper = np.percentile(sims, 95, axis=0)

    days = list(range(len(median)))

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=days, y=median, mode="lines", name="Median",
        line=dict(color="steelblue", width=2)
    ))
    fig.add_trace(go.Scatter(
        x=days, y=upper, mode="lines", name="95th Percentile",
        line=dict(color="rgba(0,100,200,0.3)", width=0),
        showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=days, y=lower, mode="lines", name="5th Percentile",
        line=dict(color="rgba(0,100,200,0.3)", width=0),
        showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=days + days[::-1], y=upper.tolist() + lower[::-1].tolist(),
        fill="toself", fillcolor="rgba(0,100,200,0.1)",
        line=dict(color="rgba(0,0,0,0)", width=0),
        name="Uncertainty Band"
    ))
    fig.update_layout(
        title=f"5-Year NAV Projection: {scheme}",
        xaxis_title="Trading Days",
        yaxis_title="NAV (INR)",
        template="plotly_white",
        legend=dict(x=0.01, y=0.99),
        height=600,
    )
    path = CHARTS / "monte_carlo.png"
    fig.write_image(str(path), width=1400, height=700, scale=2)
    log.info("Monte Carlo chart saved to %s", path)
    print(f"\nMonte Carlo Simulation: {scheme}")
    print(f"  Last NAV: {series.iloc[-1]:.2f}")
    print(f"  Median projection (5yr): {median[-1]:.2f}")
    print(f"  5th percentile: {lower[-1]:.2f}")
    print(f"  95th percentile: {upper[-1]:.2f}")


if __name__ == "__main__":
    main()

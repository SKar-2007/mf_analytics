"""
Bluestock MF Capstone — Portfolio Optimizer

Mean-Variance optimization using scipy.
Computes the efficient frontier, optimal portfolio weights,
tangency portfolio, and generates allocation reports.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import config
from utils.logging_setup import setup_logger
from utils.db import db

logger = setup_logger("portfolio_optimizer")


class PortfolioOptimizer:
    def __init__(self, risk_free_rate: float = 0.065) -> None:
        self.rf = risk_free_rate
        self.returns: Optional[pd.DataFrame] = None
        self.mean_returns: Optional[pd.Series] = None
        self.cov_matrix: Optional[pd.DataFrame] = None
        self.fund_names: Dict[str, str] = {}

    def load_data(self, amfi_codes: Optional[List[str]] = None) -> None:
        df = db.query("SELECT date_id, amfi_code, nav FROM fact_nav ORDER BY date_id")
        if df.empty:
            logger.error("No NAV data in database")
            return

        pivot = df.pivot(index="date_id", columns="amfi_code", values="nav").ffill()
        self.returns = pivot.pct_change().dropna()

        if amfi_codes:
            available = [c for c in amfi_codes if c in self.returns.columns]
            self.returns = self.returns[available]

        self.mean_returns = self.returns.mean() * 252
        self.cov_matrix = self.returns.cov() * 252

        fund_df = db.query("SELECT amfi_code, scheme_name FROM dim_fund")
        self.fund_names = dict(
            zip(fund_df["amfi_code"].astype(str), fund_df["scheme_name"])
        )

        logger.info(
            "Loaded %d funds, %d trading days",
            len(self.returns.columns),
            len(self.returns),
        )

    def random_portfolios(
        self, n_portfolios: int = 5000
    ) -> Tuple[pd.DataFrame, np.ndarray]:
        if self.mean_returns is None or self.cov_matrix is None:
            raise ValueError("No data loaded. Call load_data() first.")

        n_assets = len(self.mean_returns)
        results = np.zeros((3, n_portfolios))
        weights_record = []

        for i in range(n_portfolios):
            w = np.random.random(n_assets)
            w /= w.sum()
            weights_record.append(w)
            results[0, i] = np.dot(w, self.mean_returns)
            results[1, i] = np.sqrt(np.dot(w.T, np.dot(self.cov_matrix, w)))
            results[2, i] = (results[0, i] - self.rf) / results[1, i]

        portfolios = pd.DataFrame(
            {"Return": results[0], "Risk": results[1], "Sharpe": results[2]}
        )
        return portfolios, np.array(weights_record)

    def optimal_portfolio(self) -> Dict:
        if self.mean_returns is None or self.cov_matrix is None:
            raise ValueError("No data loaded")

        n = len(self.mean_returns)
        from scipy.optimize import minimize

        def neg_sharpe(weights):
            w = np.array(weights)
            ret = np.dot(w, self.mean_returns)
            risk = np.sqrt(np.dot(w.T, np.dot(self.cov_matrix, w)))
            return -(ret - self.rf) / risk if risk > 0 else 0

        constraints = {"type": "eq", "fun": lambda x: np.sum(x) - 1}
        bounds = tuple((0.0, 0.5) for _ in range(n))
        init = np.array([1.0 / n] * n)

        result = minimize(
            neg_sharpe, init, method="SLSQP",
            bounds=bounds, constraints=constraints,
            options={"maxiter": 1000, "ftol": 1e-9},
        )

        w = result.x
        ret = np.dot(w, self.mean_returns)
        risk = np.sqrt(np.dot(w.T, np.dot(self.cov_matrix, w)))
        sharpe = (ret - self.rf) / risk if risk > 0 else 0

        return {
            "weights": dict(zip(self.mean_returns.index, w)),
            "return": ret,
            "risk": risk,
            "sharpe": sharpe,
            "success": result.success,
        }

    def min_variance_portfolio(self) -> Dict:
        if self.mean_returns is None or self.cov_matrix is None:
            raise ValueError("No data loaded")

        n = len(self.mean_returns)
        from scipy.optimize import minimize

        def portfolio_vol(weights):
            w = np.array(weights)
            return np.sqrt(np.dot(w.T, np.dot(self.cov_matrix, w)))

        constraints = {"type": "eq", "fun": lambda x: np.sum(x) - 1}
        bounds = tuple((0.0, 0.5) for _ in range(n))
        init = np.array([1.0 / n] * n)

        result = minimize(
            portfolio_vol, init, method="SLSQP",
            bounds=bounds, constraints=constraints,
            options={"maxiter": 1000, "ftol": 1e-9},
        )

        w = result.x
        risk = portfolio_vol(w)
        ret = np.dot(w, self.mean_returns)

        return {
            "weights": dict(zip(self.mean_returns.index, w)),
            "return": ret,
            "risk": risk,
            "sharpe": (ret - self.rf) / risk if risk > 0 else 0,
        }

    def efficient_frontier(self, n_points: int = 50) -> pd.DataFrame:
        if self.mean_returns is None or self.cov_matrix is None:
            raise ValueError("No data loaded")

        from scipy.optimize import minimize

        n = len(self.mean_returns)
        target_returns = np.linspace(
            self.mean_returns.min(), self.mean_returns.max(), n_points
        )
        frontier = []

        def portfolio_vol(weights):
            w = np.array(weights)
            return np.sqrt(np.dot(w.T, np.dot(self.cov_matrix, w)))

        constraints = [{"type": "eq", "fun": lambda x: np.sum(x) - 1}]
        bounds = tuple((0.0, 0.5) for _ in range(n))
        init = np.array([1.0 / n] * n)

        for target in target_returns:
            constraints[0] = {
                "type": "eq",
                "fun": lambda x: np.sum(x) - 1,
            }
            constraints.append(
                {"type": "eq", "fun": lambda x, t=target: np.dot(x, self.mean_returns) - t}
            )
            result = minimize(
                portfolio_vol, init, method="SLSQP",
                bounds=bounds, constraints=constraints,
                options={"maxiter": 1000, "ftol": 1e-9},
            )
            constraints.pop()
            if result.success:
                frontier.append(
                    {"Return": target, "Risk": portfolio_vol(result.x)}
                )

        return pd.DataFrame(frontier)

    def chart_efficient_frontier(
        self, save: bool = True
    ) -> Optional[go.Figure]:
        if self.returns is None:
            return None

        rand_portfolios, _ = self.random_portfolios(8000)
        optimal = self.optimal_portfolio()
        min_var = self.min_variance_portfolio()
        frontier = self.efficient_frontier()

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=rand_portfolios["Risk"],
                y=rand_portfolios["Return"],
                mode="markers",
                marker=dict(
                    color=rand_portfolios["Sharpe"],
                    colorscale="Viridis",
                    size=4,
                    colorbar=dict(title="Sharpe Ratio"),
                ),
                name="Random Portfolios",
            )
        )

        if not frontier.empty:
            fig.add_trace(
                go.Scatter(
                    x=frontier["Risk"],
                    y=frontier["Return"],
                    mode="lines",
                    line=dict(color="black", width=3),
                    name="Efficient Frontier",
                )
            )

        fig.add_trace(
            go.Scatter(
                x=[optimal["risk"]],
                y=[optimal["return"]],
                mode="markers+text",
                marker=dict(color="red", size=14, symbol="star"),
                text=["Tangency (Max Sharpe)"],
                textposition="top center",
                name="Optimal Portfolio",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=[min_var["risk"]],
                y=[min_var["return"]],
                mode="markers+text",
                marker=dict(color="blue", size=12, symbol="diamond"),
                text=["Min Variance"],
                textposition="bottom right",
                name="Min Variance Portfolio",
            )
        )

        fig.update_layout(
            title="Mean-Variance Efficient Frontier",
            xaxis_title="Risk (Annualised Std Dev)",
            yaxis_title="Return (Annualised)",
            template="plotly_white",
            height=700,
        )

        if save:
            path = config.charts_dir / "efficient_frontier.png"
            path.parent.mkdir(parents=True, exist_ok=True)
            fig.write_image(str(path), width=1400, height=800, scale=2)
            logger.info("Efficient frontier saved to %s", path)

        return fig

    def allocation_report(self, portfolio: Dict) -> pd.DataFrame:
        records = []
        for code, weight in portfolio["weights"].items():
            if weight > 0.001:
                name = self.fund_names.get(str(code), str(code))
                records.append(
                    {
                        "AMFI Code": code,
                        "Scheme Name": name[:50],
                        "Allocation %": round(weight * 100, 2),
                    }
                )
        df = pd.DataFrame(records).sort_values("Allocation %", ascending=False)
        df["Cumulative %"] = df["Allocation %"].cumsum()
        return df

    def full_report(self) -> Dict:
        optimal = self.optimal_portfolio()
        min_var = self.min_variance_portfolio()

        return {
            "optimal_portfolio": {
                "expected_return": round(optimal["return"] * 100, 2),
                "expected_risk": round(optimal["risk"] * 100, 2),
                "sharpe_ratio": round(optimal["sharpe"], 4),
                "allocation": self.allocation_report(optimal).to_dict("records"),
            },
            "min_variance_portfolio": {
                "expected_return": round(min_var["return"] * 100, 2),
                "expected_risk": round(min_var["risk"] * 100, 2),
                "sharpe_ratio": round(min_var["sharpe"], 4),
                "allocation": self.allocation_report(min_var).to_dict("records"),
            },
        }


if __name__ == "__main__":
    optimizer = PortfolioOptimizer()
    optimizer.load_data()

    report = optimizer.full_report()
    print("\n=== Optimal Portfolio (Max Sharpe) ===")
    opt = report["optimal_portfolio"]
    print(f"Expected Return: {opt['expected_return']}%")
    print(f"Expected Risk:   {opt['expected_risk']}%")
    print(f"Sharpe Ratio:    {opt['sharpe_ratio']}")
    print("\nTop Allocations:")
    for a in opt["allocation"][:10]:
        print(f"  {a['Scheme Name']:45s} {a['Allocation %']:6.2f}%")

    print(f"\n=== Min Variance Portfolio ===")
    mv = report["min_variance_portfolio"]
    print(f"Expected Return: {mv['expected_return']}%")
    print(f"Expected Risk:   {mv['expected_risk']}%")
    print(f"Sharpe Ratio:    {mv['sharpe_ratio']}")
    print("\nTop Allocations:")
    for a in mv["allocation"][:10]:
        print(f"  {a['Scheme Name']:45s} {a['Allocation %']:6.2f}%")

    fig = optimizer.chart_efficient_frontier()
    if fig:
        fig.show()

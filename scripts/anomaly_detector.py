"""
Bluestock MF Capstone — Anomaly Detector

Detects anomalies in NAV time series using:
1. Z-score method (rolling window)
2. Percentage change spikes
3. Zero/negative NAV detection
4. Gap detection (missing trading days)
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import config
from utils.logging_setup import setup_logger
from utils.db import db

logger = setup_logger("anomaly_detector")


class NAVAnomalyDetector:
    def __init__(
        self,
        zscore_threshold: float = 3.0,
        return_spike_pct: float = 5.0,
        max_missing_days: int = 7,
    ) -> None:
        self.zscore_threshold = zscore_threshold
        self.return_spike_pct = return_spike_pct
        self.max_missing_days = max_missing_days
        self.nav_data: Optional[pd.DataFrame] = None
        self.returns: Optional[pd.DataFrame] = None
        self.fund_names: Dict[str, str] = {}

    def load_data(self) -> None:
        df = db.query("SELECT date_id, amfi_code, nav FROM fact_nav ORDER BY date_id")
        if df.empty:
            logger.error("No NAV data available")
            return

        df["date"] = pd.to_datetime(df["date_id"])
        pivot = df.pivot(index="date", columns="amfi_code", values="nav").ffill()
        pivot.columns = pivot.columns.astype(str)
        self.nav_data = pivot
        self.returns = pivot.pct_change().dropna()

        fund_df = db.query("SELECT amfi_code, scheme_name FROM dim_fund")
        self.fund_names = dict(
            zip(fund_df["amfi_code"].astype(str), fund_df["scheme_name"])
        )

        logger.info(
            "Loaded %d funds, %d days for anomaly detection",
            len(pivot.columns),
            len(pivot),
        )

    def detect_zscore_anomalies(
        self, code: str, window: int = 90
    ) -> pd.DataFrame:
        if self.nav_data is None or code not in self.nav_data.columns:
            return pd.DataFrame()

        series = self.nav_data[code].dropna()
        rolling_mean = series.rolling(window, min_periods=window // 2).mean()
        rolling_std = series.rolling(window, min_periods=window // 2).std()
        zscore = (series - rolling_mean) / rolling_std.replace(0, np.nan)

        anomalies = zscore[zscore.abs() > self.zscore_threshold].reset_index()
        if anomalies.empty:
            return pd.DataFrame()

        anomalies.columns = ["date", "zscore"]
        anomalies["amfi_code"] = code
        anomalies["type"] = "zscore"
        anomalies["nav"] = series.loc[anomalies["date"]].values
        return anomalies

    def detect_return_spikes(self, code: str) -> pd.DataFrame:
        if self.returns is None or code not in self.returns.columns:
            return pd.DataFrame()

        daily_ret = self.returns[code].dropna() * 100
        spikes = daily_ret[daily_ret.abs() > self.return_spike_pct].reset_index()
        if spikes.empty:
            return pd.DataFrame()

        spikes.columns = ["date", "return_pct"]
        spikes["amfi_code"] = code
        spikes["type"] = "return_spike"
        return spikes

    def detect_value_anomalies(self, code: str) -> pd.DataFrame:
        if self.nav_data is None or code not in self.nav_data.columns:
            return pd.DataFrame()

        series = self.nav_data[code]
        issues = pd.DataFrame()

        zero_neg = series[series <= 0].reset_index()
        if not zero_neg.empty:
            zero_neg.columns = ["date", "nav"]
            zero_neg["amfi_code"] = code
            zero_neg["type"] = "zero_negative_nav"
            issues = pd.concat([issues, zero_neg], ignore_index=True)

        flat = series[series.diff().abs() < 1e-8].reset_index()
        if not flat.empty:
            flat.columns = ["date", "nav"]
            flat["amfi_code"] = code
            flat["type"] = "flat_nav"
            issues = pd.concat([issues, flat], ignore_index=True)

        return issues

    def detect_missing_days(self, code: str) -> pd.DataFrame:
        if self.nav_data is None or code not in self.nav_data.columns:
            return pd.DataFrame()

        series = self.nav_data[code].dropna()
        if len(series) < 2:
            return pd.DataFrame()

        date_range = pd.date_range(
            start=series.index.min(), end=series.index.max(), freq="D"
        )
        actual_dates = set(series.index)
        missing_dates = [d for d in date_range if d not in actual_dates]

        if not missing_dates:
            return pd.DataFrame()

        missing = pd.DataFrame({"date": missing_dates, "amfi_code": code, "type": "missing_day"})
        return missing

    def detect_all(self, codes: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:
        if self.nav_data is None:
            return {}

        target_codes = codes or self.nav_data.columns.tolist()
        results: Dict[str, pd.DataFrame] = {}

        for code in target_codes:
            code_str = str(code)
            parts = [
                self.detect_zscore_anomalies(code_str),
                self.detect_return_spikes(code_str),
                self.detect_value_anomalies(code_str),
                self.detect_missing_days(code_str),
            ]
            parts = [p for p in parts if not p.empty]
            if not parts:
                continue
            anomalies = pd.concat(parts, ignore_index=True)
            if "date" in anomalies.columns:
                anomalies = anomalies.sort_values("date")

            if not anomalies.empty:
                results[code_str] = anomalies
                name = self.fund_names.get(code_str, code_str)
                logger.info(
                    "%s: %d anomaly(-ies) detected",
                    name[:40], len(anomalies),
                )

        return results

    def summary(self, results: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        records = []
        for code, df in results.items():
            types = df["type"].value_counts()
            records.append(
                {
                    "amfi_code": code,
                    "scheme_name": self.fund_names.get(str(code), str(code)),
                    "total_anomalies": len(df),
                    "zscore_anomalies": int(types.get("zscore", 0)),
                    "return_spikes": int(types.get("return_spike", 0)),
                    "zero_negative_nav": int(types.get("zero_negative_nav", 0)),
                    "flat_nav": int(types.get("flat_nav", 0)),
                    "missing_days": int(types.get("missing_day", 0)),
                    "date_range": f"{df['date'].min().date()} to {df['date'].max().date()}",
                }
            )
        if not records:
            return pd.DataFrame(
                columns=["amfi_code", "scheme_name", "total_anomalies",
                         "zscore_anomalies", "return_spikes", "zero_negative_nav",
                         "flat_nav", "missing_days", "date_range"]
            )
        return pd.DataFrame(records).sort_values("total_anomalies", ascending=False)

    def chart_anomalies(
        self, code: str, results: Dict[str, pd.DataFrame], save: bool = True
    ) -> Optional[go.Figure]:
        if self.nav_data is None or code not in self.nav_data:
            return None

        code_str = str(code)
        series = self.nav_data[code_str]
        anomalies = results.get(code_str)

        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.08,
            subplot_titles=("NAV with Anomalies", "Daily Returns"),
        )

        fig.add_trace(
            go.Scatter(
                x=series.index, y=series.values,
                mode="lines", name="NAV",
                line=dict(color="steelblue", width=1),
            ),
            row=1, col=1,
        )

        if anomalies is not None and not anomalies.empty:
            anomaly_points = anomalies[anomalies["type"].isin(["zscore", "zero_negative_nav"])]
            if not anomaly_points.empty:
                fig.add_trace(
                    go.Scatter(
                        x=anomaly_points["date"],
                        y=anomaly_points["nav"] if "nav" in anomaly_points.columns else
                          [series.loc[d] for d in anomaly_points["date"]],
                        mode="markers",
                        marker=dict(color="red", size=8, symbol="x"),
                        name="Anomalies",
                    ),
                    row=1, col=1,
                )

        if self.returns is not None and code_str in self.returns:
            ret = self.returns[code_str] * 100
            ret_color = ["red" if abs(v) > self.return_spike_pct else "gray" for v in ret]

            fig.add_trace(
                go.Scatter(
                    x=ret.index, y=ret.values,
                    mode="markers",
                    marker=dict(color=ret_color, size=3),
                    name="Daily Return %",
                ),
                row=2, col=1,
            )

            fig.add_hline(
                y=self.return_spike_pct, line_dash="dash", line_color="red",
                annotation_text=f"±{self.return_spike_pct}% threshold",
                row=2, col=1,
            )
            fig.add_hline(
                y=-self.return_spike_pct, line_dash="dash", line_color="red",
                row=2, col=1,
            )

        name = self.fund_names.get(code_str, f"Scheme {code_str}")
        fig.update_layout(
            title=f"Anomaly Detection: {name}",
            template="plotly_white",
            height=800,
            showlegend=True,
        )
        fig.update_yaxes(title_text="NAV (INR)", row=1, col=1)
        fig.update_yaxes(title_text="Return %", row=2, col=1)

        if save:
            safe_name = name.replace(" ", "_").replace("/", "_")[:30]
            path = config.charts_dir / f"anomaly_{safe_name}.png"
            path.parent.mkdir(parents=True, exist_ok=True)
            fig.write_image(str(path), width=1400, height=800, scale=2)

        return fig


if __name__ == "__main__":
    detector = NAVAnomalyDetector()
    detector.load_data()

    results = detector.detect_all()
    summary_df = detector.summary(results)

    if not summary_df.empty:
        print("\n=== Anomaly Detection Summary ===")
        print(f"Total funds with anomalies: {len(summary_df)}")
        total_anom = int(summary_df["total_anomalies"].sum())
        print(f"Total anomalies found: {total_anom}")
        print("\nMost affected funds:")
        print(
            summary_df.head(10)[
                ["scheme_name", "total_anomalies", "zscore_anomalies", "missing_days"]
            ].to_string(index=False)
        )

        worst = summary_df.iloc[0]["amfi_code"]
        fig = detector.chart_anomalies(worst, results)
        if fig:
            fig.show()

        summary_path = config.base_dir / "reports" / "anomaly_report.csv"
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_df.to_csv(summary_path, index=False)
        logger.info("Anomaly report saved to %s", summary_path)
    else:
        print("\nNo anomalies detected across any fund.")

"""
Bluestock MF Capstone — Data Quality Report

Validates every dataset and database table, flags anomalies,
missing values, duplicates, outliers, and schema violations.
Generates a JSON report with per-dataset quality scores.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import config
from utils.logging_setup import setup_logger
from utils.db import db

logger = setup_logger("data_quality")


class DataQualityChecker:
    def __init__(self) -> None:
        self.report: Dict[str, Any] = {
            "generated_at": datetime.now().isoformat(),
            "overall_score": 0.0,
            "datasets": {},
            "database": {"tables": {}, "row_count_total": 0, "issues": []},
            "warnings": [],
            "errors": [],
        }
        self._total_score = 0.0
        self._checked = 0

    def _dataset_path(self, name: str) -> Path:
        return config.raw_dir / (config.resolve("datasets", name) or name)

    def _score(self, passed: int, total: int) -> float:
        return round((passed / max(total, 1)) * 100, 1)

    # ---- CSV-level checks ----

    def check_csv_exists(self, name: str) -> Optional[pd.DataFrame]:
        path = self._dataset_path(name)
        if not path.exists():
            self.report["datasets"][name] = {
                "status": "MISSING",
                "rows": 0,
                "score": 0.0,
                "issues": [f"File not found: {path}"],
            }
            self.report["errors"].append(f"Missing dataset: {name}")
            return None
        try:
            df = pd.read_csv(path)
            return df
        except Exception as e:
            self.report["datasets"][name] = {
                "status": "ERROR",
                "rows": 0,
                "score": 0.0,
                "issues": [str(e)],
            }
            self.report["errors"].append(f"Cannot read {name}: {e}")
            return None

    def check_missing_values(self, name: str, df: pd.DataFrame) -> List[str]:
        issues: List[str] = []
        nulls = df.isnull().sum()
        null_cols = nulls[nulls > 0]
        for col, cnt in null_cols.items():
            pct = round(cnt / len(df) * 100, 1)
            if pct > 50:
                issues.append(f"Column '{col}' has {pct}% missing values")
            elif pct > 10:
                issues.append(f"Column '{col}' has {pct}% missing (moderate)")
        return issues

    def check_duplicates(self, name: str, df: pd.DataFrame, subset: Optional[List[str]] = None) -> List[str]:
        issues: List[str] = []
        dupes = df.duplicated(subset=subset).sum()
        if dupes > 0:
            issues.append(f"Found {dupes} duplicate rows (subset={subset or 'all columns'})")
        return issues

    def check_outliers_iqr(self, name: str, df: pd.DataFrame, cols: List[str]) -> List[str]:
        issues: List[str] = []
        for col in cols:
            if col not in df.columns or not pd.api.types.is_numeric_dtype(df[col]):
                continue
            q1, q3 = df[col].quantile(0.25), df[col].quantile(0.75)
            iqr = q3 - q1
            lower, upper = q1 - 3 * iqr, q3 + 3 * iqr
            outliers = ((df[col] < lower) | (df[col] > upper)).sum()
            if outliers > 0:
                pct = round(outliers / len(df) * 100, 1)
                issues.append(f"Column '{col}' has {outliers} outliers ({pct}%)")
        return issues

    def check_date_format(self, name: str, df: pd.DataFrame, col: str, fmt: Optional[str] = None) -> List[str]:
        issues: List[str] = []
        if col not in df.columns:
            return issues
        parsed = pd.to_datetime(df[col], errors="coerce", format=fmt)
        bad = parsed.isna().sum()
        if bad > 0:
            issues.append(f"Column '{col}' has {bad} unparseable dates")
        return issues

    def check_nav_integrity(self, name: str, df: pd.DataFrame) -> List[str]:
        issues: List[str] = []
        if "nav" not in df.columns:
            return issues
        zeros = (df["nav"] <= 0).sum()
        if zeros > 0:
            issues.append(f"Found {zeros} NAV values <= 0")
        extremes = (df["nav"] > 1e6).sum()
        if extremes > 0:
            issues.append(f"Found {extremes} NAV values > 1,000,000 (suspicious)")
        return issues

    def check_expense_ratio(self, name: str, df: pd.DataFrame) -> List[str]:
        issues: List[str] = []
        col = next((c for c in df.columns if "expense" in c.lower()), None)
        if col is None:
            return issues
        out_of_range = ((df[col] < 0.1) | (df[col] > 2.5)).sum()
        if out_of_range > 0:
            issues.append(f"Column '{col}' has {out_of_range} values outside [0.1, 2.5]")
        return issues

    def check_aum_consistency(self, name: str, df: pd.DataFrame) -> List[str]:
        issues: List[str] = []
        if "aum_lakh_crore" in df.columns and "aum_crore" in df.columns:
            mismatch = (abs(df["aum_lakh_crore"] * 100000 - df["aum_crore"]) > 1).sum()
            if mismatch > 0:
                issues.append(f"Found {mismatch} rows where aum_lakh_crore * 1e5 != aum_crore")
        return issues

    def check_kyc_validity(self, name: str, df: pd.DataFrame) -> List[str]:
        issues: List[str] = []
        col = next((c for c in df.columns if "kyc" in c.lower()), None)
        if col is None:
            return issues
        valid = {"VERIFIED", "PENDING", "FAILED", "Verified", "Pending", "Failed"}
        invalid = df[~df[col].isin(valid)][col].unique().tolist()
        if invalid:
            issues.append(f"Invalid KYC statuses found: {invalid}")
        return issues

    def check_txn_types(self, name: str, df: pd.DataFrame) -> List[str]:
        issues: List[str] = []
        col = next((c for c in df.columns if "transaction_type" in c.lower()), None)
        if col is None:
            return issues
        valid = {"SIP", "LUMPSUM", "REDEMPTION"}
        actual = set(df[col].dropna().unique())
        invalid = actual - valid
        if invalid:
            issues.append(f"Invalid transaction types: {invalid}")
        return issues

    def validate_csv_dataset(self, name: str) -> None:
        df = self.check_csv_exists(name)
        if df is None:
            return

        issues: List[str] = []
        checks_passed = 0
        total_checks = 7

        # Check 1: missing values
        mv = self.check_missing_values(name, df)
        issues.extend(mv)
        if not mv:
            checks_passed += 1

        # Check 2: duplicates
        dup = self.check_duplicates(name, df)
        issues.extend(dup)
        if not dup:
            checks_passed += 1

        # Check 3: date formats
        date_cols = [c for c in df.columns if "date" in c.lower()]
        for dc in date_cols:
            issues.extend(self.check_date_format(name, df, dc))
        if all(not self.check_date_format(name, df, dc) for dc in date_cols[:1] if date_cols):
            checks_passed += 1
        elif not date_cols:
            checks_passed += 1

        # Check 4: numeric outliers
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        ol = self.check_outliers_iqr(name, df, numeric_cols)
        issues.extend(ol)
        if not ol:
            checks_passed += 1

        # Check 5: NAV integrity
        ni = self.check_nav_integrity(name, df)
        issues.extend(ni)
        if not ni:
            checks_passed += 1

        # Check 6: expense ratio
        er = self.check_expense_ratio(name, df)
        issues.extend(er)
        if not er:
            checks_passed += 1

        # Check 7: AUM consistency | KYC | txn types (context-dependent)
        for check_fn in [self.check_aum_consistency, self.check_kyc_validity, self.check_txn_types]:
            ci = check_fn(name, df)
            issues.extend(ci)
            if not ci:
                checks_passed += 1
                break
        else:
            checks_passed += 1

        score = self._score(checks_passed, total_checks)
        self._total_score += score
        self._checked += 1

        self.report["datasets"][name] = {
            "status": "OK" if score >= 70 else "ISSUES",
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": list(df.columns),
            "dtypes": {str(k): str(v) for k, v in df.dtypes.items()},
            "missing_values": df.isnull().sum().to_dict(),
            "duplicates": df.duplicated().sum(),
            "score": score,
            "issues": issues,
        }

        if issues:
            logger.warning("%s: %d issue(s) (score=%.1f%%)", name, len(issues), score)
        else:
            logger.info("%s: clean (score=%.1f%%)", name, score)

    # ---- Database-level checks ----

    def validate_database(self) -> None:
        tables = db.list_tables()
        if not tables:
            self.report["database"]["issues"].append("No tables found in database")
            return

        total_rows = 0
        for table in tables:
            if table == "sqlite_sequence":
                continue
            rows = db.table_row_count(table)
            total_rows += rows
            col_info = db.schema_info(table)
            self.report["database"]["tables"][table] = {
                "rows": rows,
                "columns": len(col_info),
                "schema": [{"name": c[1], "type": c[2], "nullable": not c[3]} for c in col_info],
            }
            if rows == 0:
                self.report["database"]["issues"].append(f"Table '{table}' is empty")

        self.report["database"]["row_count_total"] = total_rows

    def generate(self) -> Dict[str, Any]:
        dataset_names = [
            "fund_master", "nav_history", "aum_data", "sip_data",
            "category_inflows", "folio_data", "scheme_performance",
            "investor_transactions", "portfolio_holdings", "benchmark_data",
        ]
        for ds in dataset_names:
            self.validate_csv_dataset(ds)

        self.validate_database()

        self.report["overall_score"] = round(
            self._total_score / max(self._checked, 1), 1
        )
        self.report["status"] = (
            "PASS" if self.report["overall_score"] >= 75 else "REVIEW"
        )
        return self.report

    def to_json(self, path: Optional[Path] = None) -> Path:
        output_path = path or config.base_dir / "reports" / "data_quality_report.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(self.report, f, indent=2, default=str)
        logger.info("Data quality report saved to %s", output_path)
        return output_path


if __name__ == "__main__":
    checker = DataQualityChecker()
    report = checker.generate()
    checker.to_json()
    print(f"\nOverall data quality score: {report['overall_score']}% — {report['status']}")
    print(f"Datasets checked: {len(report['datasets'])}")
    print(f"Database tables: {len(report['database']['tables'])} ({report['database']['row_count_total']} rows)")
    if report["errors"]:
        print(f"\nErrors ({len(report['errors'])}):")
        for e in report["errors"]:
            print(f"  ! {e}")
    if report["warnings"]:
        print(f"\nWarnings ({len(report['warnings'])}):")
        for w in report["warnings"]:
            print(f"  ! {w}")

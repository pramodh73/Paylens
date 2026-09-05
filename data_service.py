"""Data service for PayLens.
Loads, validates, caches, and provides high-performance analytics on the payment transaction dataset.
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import pandas as pd
import numpy as np

from models.schemas import (
    SummaryKPIs,
    BreakdownItem,
    ErrorCodeItem,
    TrendItem,
    DashboardSummary,
    TransactionItem,
    TransactionListResponse
)

REQUIRED_COLUMNS = [
    "transaction_id",
    "timestamp",
    "amount",
    "payment_method",
    "bank",
    "status",
    "error_code",
    "processing_time_seconds",
    "customer_id"
]

class DataService:
    def __init__(self, data_path: Optional[str] = None):
        if data_path:
            self.data_path = Path(data_path)
        else:
            # Default to backend/data/paylens_transactions.csv
            base_dir = Path(__file__).resolve().parent.parent
            self.data_path = base_dir / "data" / "paylens_transactions.csv"

        self._df: Optional[pd.DataFrame] = None
        self._load_error: Optional[str] = None

    @property
    def is_loaded(self) -> bool:
        return self._df is not None and not self._df.empty

    @property
    def load_error(self) -> Optional[str]:
        return self._load_error

    def get_df(self) -> pd.DataFrame:
        """Return the cached dataframe, loading it if not yet in memory."""
        if self._df is not None:
            return self._df

        if not self.data_path.exists():
            # Check fallback in project root or relative path
            alt_path = Path("backend/data/paylens_transactions.csv")
            if alt_path.exists():
                self.data_path = alt_path.resolve()
            else:
                self._load_error = "Transaction dataset not found. Please place paylens_transactions.csv in backend/data/."
                raise FileNotFoundError(self._load_error)

        try:
            df = pd.read_csv(self.data_path)
            
            # Validate required columns
            missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
            if missing_cols:
                self._load_error = f"Malformed CSV. Missing required columns: {', '.join(missing_cols)}"
                raise ValueError(self._load_error)

            # Parse timestamps
            df["parsed_timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
            if df["parsed_timestamp"].isna().all():
                self._load_error = "Malformed CSV: Unable to parse any timestamps."
                raise ValueError(self._load_error)

            # Clean and standardize string columns
            df["status"] = df["status"].astype(str).str.strip().str.lower()
            df["bank"] = df["bank"].astype(str).str.strip()
            df["payment_method"] = df["payment_method"].astype(str).str.strip()
            df["error_code"] = df["error_code"].fillna("").astype(str).str.strip()
            df.loc[df["error_code"] == "", "error_code"] = None

            # Numeric columns
            df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
            df["processing_time_seconds"] = pd.to_numeric(df["processing_time_seconds"], errors="coerce").fillna(0.0)

            # Sort chronologically
            df = df.sort_values("parsed_timestamp").reset_index(drop=True)

            self._df = df
            self._load_error = None
            return self._df

        except Exception as e:
            self._load_error = f"Error loading dataset: {str(e)}"
            raise

    def reload(self) -> pd.DataFrame:
        """Force reloading the dataset from disk."""
        self._df = None
        self._load_error = None
        return self.get_df()

    def get_summary_kpis(self, estimated_at_risk: float = 0.0) -> SummaryKPIs:
        """Calculate overall platform KPI metrics."""
        df = self.get_df()
        total_txns = int(len(df))
        if total_txns == 0:
            return SummaryKPIs(
                total_transactions=0,
                successful_transactions=0,
                failed_transactions=0,
                success_rate=0.0,
                failure_rate=0.0,
                total_transaction_value=0.0,
                failed_transaction_value=0.0,
                estimated_transaction_value_at_risk=0.0,
                average_processing_time=0.0,
                active_incident_count=0,
                date_range_start="",
                date_range_end=""
            )

        success_mask = df["status"] == "success"
        failed_mask = df["status"] == "failed"

        successful_txns = int(success_mask.sum())
        failed_txns = int(failed_mask.sum())
        success_rate = round(successful_txns / total_txns, 4)
        failure_rate = round(failed_txns / total_txns, 4)

        total_value = round(float(df["amount"].sum()), 2)
        failed_value = round(float(df.loc[failed_mask, "amount"].sum()), 2)
        avg_processing_time = round(float(df["processing_time_seconds"].mean()), 2)

        start_time_str = df["timestamp"].min()
        end_time_str = df["timestamp"].max()

        return SummaryKPIs(
            total_transactions=total_txns,
            successful_transactions=successful_txns,
            failed_transactions=failed_txns,
            success_rate=success_rate,
            failure_rate=failure_rate,
            total_transaction_value=total_value,
            failed_transaction_value=failed_value,
            estimated_transaction_value_at_risk=round(estimated_at_risk, 2),
            average_processing_time=avg_processing_time,
            active_incident_count=0,
            date_range_start=str(start_time_str),
            date_range_end=str(end_time_str)
        )

    def get_payment_method_breakdown(self) -> List[BreakdownItem]:
        """Aggregate performance across all payment methods."""
        df = self.get_df()
        items = []
        for method, group in df.groupby("payment_method"):
            total = len(group)
            succ = int((group["status"] == "success").sum())
            fail = int((group["status"] == "failed").sum())
            sr = round(succ / total, 4) if total > 0 else 0.0
            fr = round(fail / total, 4) if total > 0 else 0.0
            tot_amt = round(float(group["amount"].sum()), 2)
            fail_amt = round(float(group.loc[group["status"] == "failed", "amount"].sum()), 2)
            items.append(BreakdownItem(
                name=str(method),
                total=total,
                successful=succ,
                failed=fail,
                success_rate=sr,
                failure_rate=fr,
                total_amount=tot_amt,
                failed_amount=fail_amt
            ))
        items.sort(key=lambda x: x.total, reverse=True)
        return items

    def get_bank_breakdown(self) -> List[BreakdownItem]:
        """Aggregate performance across all banks."""
        df = self.get_df()
        items = []
        for bank, group in df.groupby("bank"):
            total = len(group)
            succ = int((group["status"] == "success").sum())
            fail = int((group["status"] == "failed").sum())
            sr = round(succ / total, 4) if total > 0 else 0.0
            fr = round(fail / total, 4) if total > 0 else 0.0
            tot_amt = round(float(group["amount"].sum()), 2)
            fail_amt = round(float(group.loc[group["status"] == "failed", "amount"].sum()), 2)
            items.append(BreakdownItem(
                name=str(bank),
                total=total,
                successful=succ,
                failed=fail,
                success_rate=sr,
                failure_rate=fr,
                total_amount=tot_amt,
                failed_amount=fail_amt
            ))
        items.sort(key=lambda x: x.total, reverse=True)
        return items

    def get_error_code_breakdown(self) -> List[ErrorCodeItem]:
        """Aggregate failure distribution by error code."""
        df = self.get_df()
        failed_df = df[df["status"] == "failed"]
        total_failed = len(failed_df)
        if total_failed == 0:
            return []

        items = []
        for err, group in failed_df.groupby("error_code"):
            count = len(group)
            pct = round(count / total_failed, 4)
            affected_amt = round(float(group["amount"].sum()), 2)
            items.append(ErrorCodeItem(
                error_code=str(err),
                count=count,
                percentage=pct,
                affected_amount=affected_amt
            ))
        items.sort(key=lambda x: x.count, reverse=True)
        return items

    def get_daily_trends(self) -> List[TrendItem]:
        """Calculate daily trend metrics across the dataset."""
        df = self.get_df()
        temp = df.copy()
        temp["date"] = temp["parsed_timestamp"].dt.date
        items = []
        for date, group in temp.groupby("date"):
            total = len(group)
            succ = int((group["status"] == "success").sum())
            fail = int((group["status"] == "failed").sum())
            sr = round(succ / total, 4) if total > 0 else 0.0
            avg_proc = round(float(group["processing_time_seconds"].mean()), 2)
            items.append(TrendItem(
                timestamp=str(date),
                label=str(date.strftime("%b %d") if hasattr(date, "strftime") else date),
                total=total,
                success=succ,
                failed=fail,
                success_rate=sr,
                avg_processing_time=avg_proc
            ))
        items.sort(key=lambda x: x.timestamp)
        return items

    def get_hourly_trends(self, days_limit: Optional[int] = None) -> List[TrendItem]:
        """Calculate hourly trend metrics, optionally limited to recent days."""
        df = self.get_df()
        temp = df.copy()
        temp["hour_bucket"] = temp["parsed_timestamp"].dt.floor("h")

        if days_limit:
            max_ts = temp["parsed_timestamp"].max()
            min_ts = max_ts - pd.Timedelta(days=days_limit)
            temp = temp[temp["parsed_timestamp"] >= min_ts]

        items = []
        for ts, group in temp.groupby("hour_bucket"):
            total = len(group)
            succ = int((group["status"] == "success").sum())
            fail = int((group["status"] == "failed").sum())
            sr = round(succ / total, 4) if total > 0 else 0.0
            avg_proc = round(float(group["processing_time_seconds"].mean()), 2)
            items.append(TrendItem(
                timestamp=str(ts),
                label=ts.strftime("%d %b %H:00"),
                total=total,
                success=succ,
                failed=fail,
                success_rate=sr,
                avg_processing_time=avg_proc
            ))
        items.sort(key=lambda x: x.timestamp)
        return items

    def get_paginated_transactions(
        self,
        page: int = 1,
        page_size: int = 25,
        payment_method: Optional[str] = None,
        bank: Optional[str] = None,
        status: Optional[str] = None,
        error_code: Optional[str] = None,
        search: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        sort_by: str = "timestamp",
        sort_order: str = "desc"
    ) -> TransactionListResponse:
        """Filter and paginate transactions from the cached dataframe."""
        df = self.get_df()
        filtered = df

        if payment_method and payment_method != "ALL":
            filtered = filtered[filtered["payment_method"].str.lower() == payment_method.lower()]

        if bank and bank != "ALL":
            filtered = filtered[filtered["bank"].str.lower() == bank.lower()]

        if status and status != "ALL":
            filtered = filtered[filtered["status"].str.lower() == status.lower()]

        if error_code and error_code != "ALL":
            filtered = filtered[filtered["error_code"].fillna("").str.lower() == error_code.lower()]

        if start_date:
            try:
                start_dt = pd.to_datetime(start_date)
                filtered = filtered[filtered["parsed_timestamp"] >= start_dt]
            except Exception:
                pass

        if end_date:
            try:
                end_dt = pd.to_datetime(end_date)
                filtered = filtered[filtered["parsed_timestamp"] <= end_dt]
            except Exception:
                pass

        if search:
            s = search.strip().lower()
            mask = (
                filtered["transaction_id"].str.lower().str.contains(s, na=False) |
                filtered["customer_id"].str.lower().str.contains(s, na=False) |
                filtered["bank"].str.lower().str.contains(s, na=False) |
                filtered["payment_method"].str.lower().str.contains(s, na=False) |
                filtered["error_code"].fillna("").str.lower().str.contains(s, na=False)
            )
            filtered = filtered[mask]

        # Sorting
        ascending = sort_order.lower() == "asc"
        sort_col = "parsed_timestamp" if sort_by == "timestamp" else sort_by
        if sort_col in filtered.columns:
            filtered = filtered.sort_values(sort_col, ascending=ascending)
        else:
            filtered = filtered.sort_values("parsed_timestamp", ascending=False)

        total_count = len(filtered)
        total_pages = max(1, (total_count + page_size - 1) // page_size)
        page = max(1, min(page, total_pages))

        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_slice = filtered.iloc[start_idx:end_idx]

        items = []
        for _, row in page_slice.iterrows():
            items.append(TransactionItem(
                transaction_id=str(row["transaction_id"]),
                timestamp=str(row["timestamp"]),
                amount=float(row["amount"]),
                payment_method=str(row["payment_method"]),
                bank=str(row["bank"]),
                status=str(row["status"]),
                error_code=str(row["error_code"]) if pd.notna(row["error_code"]) and row["error_code"] else None,
                processing_time_seconds=float(row["processing_time_seconds"]),
                customer_id=str(row["customer_id"])
            ))

        return TransactionListResponse(
            items=items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    def get_transactions_slice(
        self,
        start_time: str,
        end_time: str,
        bank: Optional[str] = None,
        payment_method: Optional[str] = None
    ) -> pd.DataFrame:
        """Extract a filtered slice of transactions during a specific incident window."""
        df = self.get_df()
        start_dt = pd.to_datetime(start_time)
        end_dt = pd.to_datetime(end_time)

        mask = (df["parsed_timestamp"] >= start_dt) & (df["parsed_timestamp"] <= end_dt)
        if bank and bank != "ALL":
            mask = mask & (df["bank"].str.lower() == bank.lower())
        if payment_method and payment_method != "ALL":
            mask = mask & (df["payment_method"].str.lower() == payment_method.lower())

        return df[mask].copy()


# Global singleton
data_service = DataService()

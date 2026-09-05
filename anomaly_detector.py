"""Anomaly Detection Engine for PayLens.
Detects payment incidents across banks, payment methods, and gateways using
statistical variance, multi-scale time-window analysis, and error-concentration models.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

from models.schemas import Incident
from services.data_service import data_service

class AnomalyDetector:
    def __init__(self):
        self._cached_incidents: Optional[List[Incident]] = None
        self._last_evaluated: Optional[datetime] = None

    def detect_incidents(self, force_refresh: bool = False) -> List[Incident]:
        """Detect and return structured payment incidents across the dataset."""
        if self._cached_incidents is not None and not force_refresh:
            return self._cached_incidents

        df = data_service.get_df().copy()
        if df.empty:
            self._cached_incidents = []
            return []

        # Baselines
        overall_total = len(df)
        overall_success = int((df["status"] == "success").sum())
        global_baseline_sr = round(overall_success / overall_total, 4) if overall_total > 0 else 0.92
        global_mean_proc = float(df["processing_time_seconds"].mean())
        global_std_proc = float(df["processing_time_seconds"].std())

        # Granular baselines
        bank_baselines = df.groupby("bank")["status"].apply(
            lambda s: round(float((s == "success").mean()), 4)
        ).to_dict()

        method_baselines = df.groupby("payment_method")["status"].apply(
            lambda s: round(float((s == "success").mean()), 4)
        ).to_dict()

        combo_baselines = df.groupby(["bank", "payment_method"])["status"].apply(
            lambda s: round(float((s == "success").mean()), 4)
        ).to_dict()

        bank_proc_baselines = df.groupby("bank")["processing_time_seconds"].mean().to_dict()

        raw_candidates = []

        # Analyze over multiple window sizes: 6 hours and 12 hours
        for window_size, win_freq, win_delta in [("6h", "6h", timedelta(hours=6)), ("12h", "12h", timedelta(hours=12))]:
            df["time_bucket"] = df["parsed_timestamp"].dt.floor(win_freq)

            # 1. Bank + Payment Method combinations (finest grain)
            for (bucket, bank, method), group in df.groupby(["time_bucket", "bank", "payment_method"]):
                tot = len(group)
                if tot < 8:
                    continue

                succ = int((group["status"] == "success").sum())
                fail = int((group["status"] == "failed").sum())
                sr = round(succ / tot, 4)
                base_sr = combo_baselines.get((bank, method), bank_baselines.get(bank, global_baseline_sr))
                drop = round(base_sr - sr, 4)
                avg_proc = round(float(group["processing_time_seconds"].mean()), 2)
                base_proc = round(float(bank_proc_baselines.get(bank, global_mean_proc)), 2)

                # Anomaly triggers: significant drop in success rate or high latency with failures
                is_sr_anomaly = drop >= 0.14 and fail >= 3
                is_latency_anomaly = (avg_proc > base_proc + 1.5 * global_std_proc) and (drop >= 0.10 and fail >= 2)

                if is_sr_anomaly or is_latency_anomaly:
                    failed_subset = group[group["status"] == "failed"]
                    amt_at_risk = round(float(failed_subset["amount"].sum()), 2)
                    
                    err_counts = failed_subset["error_code"].dropna().value_counts()
                    dom_err = str(err_counts.index[0]) if not err_counts.empty else "UNKNOWN_ERROR"

                    start_str = str(bucket)
                    end_str = str(bucket + win_delta)

                    raw_candidates.append({
                        "bank": bank,
                        "payment_method": method,
                        "start_dt": bucket,
                        "end_dt": bucket + win_delta,
                        "start_time": start_str,
                        "end_time": end_str,
                        "total": tot,
                        "failed": fail,
                        "sr": sr,
                        "base_sr": base_sr,
                        "drop": drop,
                        "amt_at_risk": amt_at_risk,
                        "dom_err": dom_err,
                        "avg_proc": avg_proc,
                        "base_proc": base_proc,
                        "window_type": window_size
                    })

            # 2. Bank-wide incidents (aggregated across all methods for that bank)
            for (bucket, bank), group in df.groupby(["time_bucket", "bank"]):
                tot = len(group)
                if tot < 20:
                    continue

                succ = int((group["status"] == "success").sum())
                fail = int((group["status"] == "failed").sum())
                sr = round(succ / tot, 4)
                base_sr = bank_baselines.get(bank, global_baseline_sr)
                drop = round(base_sr - sr, 4)
                avg_proc = round(float(group["processing_time_seconds"].mean()), 2)
                base_proc = round(float(bank_proc_baselines.get(bank, global_mean_proc)), 2)

                if drop >= 0.10 and fail >= 5:
                    failed_subset = group[group["status"] == "failed"]
                    amt_at_risk = round(float(failed_subset["amount"].sum()), 2)
                    
                    err_counts = failed_subset["error_code"].dropna().value_counts()
                    dom_err = str(err_counts.index[0]) if not err_counts.empty else "UNKNOWN_ERROR"

                    raw_candidates.append({
                        "bank": bank,
                        "payment_method": "All Methods",
                        "start_dt": bucket,
                        "end_dt": bucket + win_delta,
                        "start_time": str(bucket),
                        "end_time": str(bucket + win_delta),
                        "total": tot,
                        "failed": fail,
                        "sr": sr,
                        "base_sr": base_sr,
                        "drop": drop,
                        "amt_at_risk": amt_at_risk,
                        "dom_err": dom_err,
                        "avg_proc": avg_proc,
                        "base_proc": base_proc,
                        "window_type": window_size
                    })

        # Deduplicate and merge overlapping or identical incidents
        incidents = self._cluster_and_rank_incidents(raw_candidates)
        self._cached_incidents = incidents
        self._last_evaluated = datetime.now()
        return self._cached_incidents

    def _cluster_and_rank_incidents(self, candidates: List[Dict[str, Any]]) -> List[Incident]:
        """Cluster adjacent candidate windows and assign severity."""
        if not candidates:
            return []

        # Sort by drop and amount at risk descending
        candidates.sort(key=lambda x: (x["drop"], x["amt_at_risk"]), reverse=True)

        clustered: List[Dict[str, Any]] = []

        for cand in candidates:
            # Check if this candidate overlaps significantly with an already accepted cluster
            overlap_found = False
            for c in clustered:
                same_bank = c["bank"] == cand["bank"]
                same_method = (
                    c["payment_method"] == cand["payment_method"] or
                    c["payment_method"] == "All Methods" or
                    cand["payment_method"] == "All Methods"
                )
                time_overlap = not (cand["end_dt"] <= c["start_dt"] or cand["start_dt"] >= c["end_dt"])

                if same_bank and same_method and time_overlap:
                    overlap_found = True
                    # If this candidate has higher drop or higher value, update cluster window
                    if cand["amt_at_risk"] > c["amt_at_risk"]:
                        c["amt_at_risk"] = max(c["amt_at_risk"], cand["amt_at_risk"])
                    if cand["drop"] > c["drop"]:
                        c["sr"] = cand["sr"]
                        c["drop"] = cand["drop"]
                    break

            if not overlap_found:
                clustered.append(cand.copy())

        # Build Incident schemas and assign severity
        result: List[Incident] = []
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}

        for idx, item in enumerate(clustered[:10]):  # Top distinct incidents
            drop = item["drop"]
            amt = item["amt_at_risk"]
            
            # Severity logic
            if drop >= 0.22 or (drop >= 0.18 and amt >= 25000):
                severity = "CRITICAL"
            elif drop >= 0.16 or (drop >= 0.12 and amt >= 15000):
                severity = "HIGH"
            elif drop >= 0.10:
                severity = "MEDIUM"
            else:
                severity = "LOW"

            fail_pct_change = f"+{round(drop * 100, 1)}%"
            bank_tag = item["bank"].upper().replace(" ", "")
            meth_tag = item["payment_method"].upper().replace(" ", "")
            date_tag = item["start_dt"].strftime("%m%d%H")
            inc_id = f"INC-{date_tag}-{bank_tag}-{meth_tag[:4]}"

            title = f"Elevated Failures on {item['bank']} ({item['payment_method']})"
            desc = (
                f"Success rate dropped to {round(item['sr'] * 100, 1)}% (baseline {round(item['base_sr'] * 100, 1)}%) "
                f"with {item['failed']} failed transactions and ₹{item['amt_at_risk']:,.2f} Estimated Transaction Value at Risk."
            )

            result.append(Incident(
                incident_id=inc_id,
                title=title,
                severity=severity,
                payment_method=item["payment_method"],
                bank=item["bank"],
                start_time=item["start_time"],
                end_time=item["end_time"],
                success_rate=item["sr"],
                baseline_success_rate=item["base_sr"],
                failure_rate_change=fail_pct_change,
                affected_transactions=item["failed"],
                total_window_transactions=item["total"],
                estimated_transaction_value_at_risk=item["amt_at_risk"],
                dominant_error=item["dom_err"],
                avg_processing_time=item["avg_proc"],
                baseline_processing_time=item["base_proc"],
                description=desc
            ))

        # Sort by severity rank, then by estimated transaction value at risk
        result.sort(key=lambda x: (severity_order.get(x.severity, 4), -x.estimated_transaction_value_at_risk))
        return result

    def get_incident_by_id(self, incident_id: str) -> Optional[Incident]:
        """Fetch an incident by its ID."""
        incidents = self.detect_incidents()
        for inc in incidents:
            if inc.incident_id.lower() == incident_id.lower():
                return inc
        return None

    def get_total_value_at_risk(self) -> float:
        """Calculate the total Estimated Transaction Value at Risk across all active incidents."""
        incidents = self.detect_incidents()
        return round(float(sum(inc.estimated_transaction_value_at_risk for inc in incidents)), 2)


# Global singleton
anomaly_detector = AnomalyDetector()

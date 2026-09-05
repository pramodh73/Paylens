"""AI Payment Investigator Service for PayLens.
Coordinates structured evidence generation and invokes Google Gemini (or deterministic fallback)
to provide root-cause analysis, observed evidence vs AI interpretation, business impact,
and merchant recommendations.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd

from models.schemas import Incident, InvestigationResult
from services.data_service import data_service

logger = logging.getLogger("paylens.ai_investigator")

class AIInvestigator:
    def __init__(self):
        self._api_key: Optional[str] = None
        self._client = None
        self._init_client()

    def _init_client(self):
        """Initialize Google GenAI client if API key is provided."""
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if api_key and api_key != "YOUR_KEY_HERE":
            self._api_key = api_key
            try:
                from google import genai
                self._client = genai.Client(api_key=api_key)
            except Exception as e:
                logger.warning(f"Could not initialize google-genai Client: {e}")
                self._client = None
        else:
            self._api_key = None
            self._client = None

    def build_structured_evidence(self, incident: Incident) -> Dict[str, Any]:
        """Extract factual evidence metrics for the incident without sending raw rows."""
        df_slice = data_service.get_transactions_slice(
            start_time=incident.start_time,
            end_time=incident.end_time
        )
        
        # Calculate comparison stats across other banks during the same timeframe
        other_banks_stats = {}
        if not df_slice.empty:
            for bank, bg in df_slice.groupby("bank"):
                if bank != incident.bank:
                    bg_tot = len(bg)
                    bg_succ = int((bg["status"] == "success").sum())
                    other_banks_stats[bank] = {
                        "total": bg_tot,
                        "success_rate": round(bg_succ / bg_tot, 3) if bg_tot > 0 else 0.0
                    }

        # Error distribution in affected group
        affected_slice = df_slice
        if incident.bank != "ALL":
            affected_slice = affected_slice[affected_slice["bank"] == incident.bank]
        if incident.payment_method != "All Methods":
            affected_slice = affected_slice[affected_slice["payment_method"] == incident.payment_method]

        error_counts = {}
        if not affected_slice.empty:
            failed_subset = affected_slice[affected_slice["status"] == "failed"]
            error_counts = failed_subset["error_code"].value_counts().to_dict()

        latency_delta_pct = 0.0
        if incident.baseline_processing_time > 0:
            latency_delta_pct = round(
                ((incident.avg_processing_time - incident.baseline_processing_time) / incident.baseline_processing_time) * 100,
                1
            )

        return {
            "incident_id": incident.incident_id,
            "bank": incident.bank,
            "payment_method": incident.payment_method,
            "time_window": f"{incident.start_time} to {incident.end_time}",
            "incident_success_rate": round(incident.success_rate * 100, 1),
            "baseline_success_rate": round(incident.baseline_success_rate * 100, 1),
            "success_rate_drop": round((incident.baseline_success_rate - incident.success_rate) * 100, 1),
            "total_transactions_in_window": incident.total_window_transactions,
            "affected_failed_transactions": incident.affected_transactions,
            "estimated_transaction_value_at_risk_inr": incident.estimated_transaction_value_at_risk,
            "dominant_error_code": incident.dominant_error,
            "error_distribution": error_counts,
            "average_processing_time_seconds": round(incident.avg_processing_time, 2),
            "baseline_processing_time_seconds": round(incident.baseline_processing_time, 2),
            "latency_change_percentage": latency_delta_pct,
            "other_banks_performance_in_same_window": other_banks_stats
        }

    def investigate(self, incident: Incident) -> InvestigationResult:
        """Run AI investigation using Google Gemini or deterministic fallback."""
        # Refresh key check
        self._init_client()
        evidence = self.build_structured_evidence(incident)

        if self._client is not None:
            try:
                ai_result = self._call_gemini(incident, evidence)
                if ai_result:
                    return ai_result
            except Exception as e:
                logger.error(f"Gemini API invocation failed, falling back to deterministic: {e}")

        # Deterministic Fallback
        return self._run_deterministic_investigation(incident, evidence)

    def _call_gemini(self, incident: Incident, evidence: Dict[str, Any]) -> Optional[InvestigationResult]:
        """Invoke Gemini using structured evidence."""
        prompt = f"""
You are the senior AI Payment Investigator for PayLens, an advanced payment intelligence platform for merchants.
Analyze the following structured evidence from an anomalous payment incident.

RULES:
- Never invent numbers or evidence. Use only the provided evidence.
- Strictly refer to the financial risk as "Estimated Transaction Value at Risk". Never call it actual lost revenue.
- Clearly distinguish observed facts from AI inferences.
- Return ONLY a valid JSON object with the exact keys specified below.

EVIDENCE DATA:
{json.dumps(evidence, indent=2)}

JSON SCHEMA REQUIRED:
{{
  "incident_summary": "Concise 1-2 sentence executive summary of what occurred.",
  "likely_root_cause": "Specific technical assessment of the likely root cause (e.g. gateway timeout degradation, issuer authorization declines, socket connection drops).",
  "observed_evidence": [
    "Observed fact 1 with exact numbers",
    "Observed fact 2 with exact numbers",
    "Observed fact 3 comparing with other banks or baselines"
  ],
  "ai_interpretation": "Detailed explanation of WHY the evidence leads to this conclusion, distinguishing observed facts from inference.",
  "business_impact": "Impact statement referencing the ₹{incident.estimated_transaction_value_at_risk:,.2f} Estimated Transaction Value at Risk and customer transaction drop.",
  "recommended_action": "Actionable, concrete steps for the merchant operations team (e.g. routing adjustments, bank contact, retry policies).",
  "confidence": "High | Medium | Low"
}}
"""
        response = self._client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        text = response.text.strip()
        # Clean markdown code blocks if present
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        data = json.loads(text)

        return InvestigationResult(
            incident_id=incident.incident_id,
            incident_summary=data.get("incident_summary", f"Payment degradation detected on {incident.bank} ({incident.payment_method})."),
            likely_root_cause=data.get("likely_root_cause", "Bank/Gateway connectivity degradation."),
            observed_evidence=data.get("observed_evidence", [
                f"Success rate dropped to {evidence['incident_success_rate']}% vs baseline {evidence['baseline_success_rate']}%.",
                f"Dominant error code: {evidence['dominant_error_code']}.",
                f"{evidence['affected_failed_transactions']} transactions failed with ₹{evidence['estimated_transaction_value_at_risk_inr']:,.2f} Estimated Transaction Value at Risk."
            ]),
            ai_interpretation=data.get("ai_interpretation", "Correlated failure spikes and latency shifts indicate technical degradation."),
            business_impact=data.get("business_impact", f"₹{incident.estimated_transaction_value_at_risk:,.2f} Estimated Transaction Value at Risk across {incident.affected_transactions} affected transactions."),
            recommended_action=data.get("recommended_action", "Contact acquiring bank support and reroute eligible transactions."),
            confidence=data.get("confidence", "High"),
            is_ai_generated=True,
            engine="Google Gemini (gemini-2.5-flash)",
            generated_at=datetime.now().isoformat()
        )

    def _run_deterministic_investigation(
        self,
        incident: Incident,
        evidence: Dict[str, Any]
    ) -> InvestigationResult:
        """Robust deterministic rule-based investigation based on calculated facts."""
        sr_drop = evidence["success_rate_drop"]
        dom_err = evidence["dominant_error_code"]
        affected_count = evidence["affected_failed_transactions"]
        val_at_risk = evidence["estimated_transaction_value_at_risk_inr"]
        bank = incident.bank
        method = incident.payment_method
        avg_proc = evidence["average_processing_time_seconds"]
        base_proc = evidence["baseline_processing_time_seconds"]
        latency_change = evidence["latency_change_percentage"]

        observed_facts = [
            f"Success rate dropped by {sr_drop}% (from {evidence['baseline_success_rate']}% baseline to {evidence['incident_success_rate']}%).",
            f"A total of {affected_count} transactions failed out of {evidence['total_transactions_in_window']} attempted in this window.",
            f"Dominant failure reason was {dom_err} ({evidence['error_distribution'].get(dom_err, affected_count)} occurrences).",
            f"Average processing time measured at {avg_proc}s compared to {base_proc}s baseline ({latency_change:+.1f}% change)."
        ]

        # Other banks contrast
        other_banks = evidence.get("other_banks_performance_in_same_window", {})
        if other_banks:
            other_sr_list = [v["success_rate"] * 100 for v in other_banks.values() if v.get("total", 0) > 0]
            if other_sr_list:
                avg_other_sr = round(sum(other_sr_list) / len(other_sr_list), 1)
                observed_facts.append(
                    f"Other banks maintained an average success rate of {avg_other_sr}% during the same timeframe, confirming an isolated incident."
                )

        if dom_err == "GATEWAY_TIMEOUT":
            likely_cause = f"Acquiring gateway connectivity degradation or upstream timeout on {bank} acquiring servers."
            interpretation = (
                f"The sharp surge in GATEWAY_TIMEOUT errors coupled with elevated processing latency "
                f"({avg_proc}s vs normal {base_proc}s) strongly points to upstream server exhaustion or "
                f"unresponsive socket endpoints at {bank}'s payment processing node."
            )
            recommendation = (
                f"1. Divert non-essential traffic away from {bank} gateway via smart routing.\n"
                f"2. Escalate high-priority ticket with {bank} acquiring operations citing {dom_err} spike.\n"
                f"3. Enable automatic fallback to secondary payment gateways for eligible transactions."
            )
            confidence = "High" if affected_count >= 5 else "Medium"

        elif dom_err == "BANK_DECLINED":
            likely_cause = f"Aggressive issuer authorization policy or core banking validation failure at {bank}."
            interpretation = (
                f"Transactions were rapidly rejected by {bank} with BANK_DECLINED while latency remained stable, "
                f"indicating rejection at the authorization layer (e.g. temporary risk filter tightening, "
                f"nightly batch maintenance, or issuer limits)."
            )
            recommendation = (
                f"1. Prompt customers using {bank} {method} to verify daily transaction limits or use alternate cards.\n"
                f"2. Contact {bank} merchant desk to verify if strict velocity filters were enacted.\n"
                f"3. Trigger soft-retry notifications for affected customers."
            )
            confidence = "High"

        elif dom_err == "NETWORK_ERROR":
            likely_cause = f"Intermittent network packet drop or TLS handshake termination on the {bank} connection pool."
            interpretation = (
                f"Surge in NETWORK_ERROR indicates network-layer disconnects before an HTTP acknowledgment "
                f"could be received from {bank}."
            )
            recommendation = (
                f"1. Inspect edge gateway health and firewall connection pools.\n"
                f"2. Verify DNS resolution and SSL handshake latencies to {bank}'s endpoints."
            )
            confidence = "Medium"

        elif dom_err == "INSUFFICIENT_FUNDS":
            likely_cause = f"Customer account balance exhaustion clustered in {method} checkouts."
            interpretation = (
                f"No infrastructure or bank downtime detected. The drop was driven by customer-side "
                f"INSUFFICIENT_FUNDS declines, typical of end-of-month or high-ticket purchase clusters."
            )
            recommendation = (
                f"1. Present split-payment, Buy Now Pay Later (BNPL), or EMI options at checkout.\n"
                f"2. Trigger an automated payment reminder SMS/WhatsApp with one-click payment link."
            )
            confidence = "High"

        else:
            likely_cause = f"Unclassified payment anomalies on {bank} ({method})."
            interpretation = "Insufficient evidence to determine root cause conclusively; multi-factor review recommended."
            recommendation = "Review transaction logs and contact gateway support."
            confidence = "Low"

        summary = (
            f"{method} transactions via {bank} experienced a {sr_drop}% success rate decline "
            f"between {incident.start_time} and {incident.end_time} primarily due to {dom_err}."
        )

        impact = (
            f"₹{val_at_risk:,.2f} Estimated Transaction Value at Risk across {affected_count} failed transactions. "
            f"(Note: Estimated from transaction value associated with affected failed transactions during this incident, not actual lost revenue)."
        )

        return InvestigationResult(
            incident_id=incident.incident_id,
            incident_summary=summary,
            likely_root_cause=likely_cause,
            observed_evidence=observed_facts,
            ai_interpretation=interpretation,
            business_impact=impact,
            recommended_action=recommendation,
            confidence=confidence,
            is_ai_generated=False,
            engine="Deterministic Statistical Engine (Rule-based Fallback)",
            generated_at=datetime.now().isoformat()
        )

    def chat_with_assistant(self, user_message: str, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """Merchant AI Assistant answering questions strictly based on calculated dataset evidence."""
        # Refresh key check
        self._init_client()
        kpis = data_service.get_summary_kpis()
        bank_breakdown = data_service.get_bank_breakdown()
        method_breakdown = data_service.get_payment_method_breakdown()
        incidents = anomaly_detector.detect_incidents()
        error_breakdown = data_service.get_error_code_breakdown()

        context_data = {
            "platform_kpis": {
                "total_transactions": kpis.total_transactions,
                "overall_success_rate": f"{kpis.success_rate * 100:.1f}%",
                "overall_failure_rate": f"{kpis.failure_rate * 100:.1f}%",
                "total_volume_inr": f"₹{kpis.total_transaction_value:,.2f}",
                "failed_volume_inr": f"₹{kpis.failed_transaction_value:,.2f}",
                "active_incidents_count": len(incidents),
                "total_estimated_transaction_value_at_risk": f"₹{sum(inc.estimated_transaction_value_at_risk for inc in incidents):,.2f}"
            },
            "bank_rankings_by_failure_rate": [
                {"bank": b.name, "failure_rate": f"{b.failure_rate*100:.1f}%", "total_txns": b.total, "failed_txns": b.failed}
                for b in sorted(bank_breakdown, key=lambda x: x.failure_rate, reverse=True)
            ],
            "payment_methods_by_failure_rate": [
                {"method": m.name, "failure_rate": f"{m.failure_rate*100:.1f}%", "total_txns": m.total, "failed_txns": m.failed}
                for m in sorted(method_breakdown, key=lambda x: x.failure_rate, reverse=True)
            ],
            "top_errors": [
                {"error": e.error_code, "count": e.count, "share": f"{e.percentage*100:.1f}%"}
                for e in error_breakdown
            ],
            "active_incidents": [
                {
                    "id": inc.incident_id,
                    "severity": inc.severity,
                    "bank": inc.bank,
                    "method": inc.payment_method,
                    "drop": inc.failure_rate_change,
                    "estimated_value_at_risk": f"₹{inc.estimated_transaction_value_at_risk:,.2f}",
                    "dominant_error": inc.dominant_error
                }
                for inc in incidents[:5]
            ]
        }

        if self._client is not None:
            try:
                chat_prompt = f"""
You are the PayLens AI Payment Assistant for merchants.
Answer the merchant's question strictly using the calculated platform evidence below.
Do not hallucinate or invent data. If the information is not in the data, state clearly what is available.
Always refer to financial exposure as "Estimated Transaction Value at Risk".

MERCHANT QUESTION:
"{user_message}"

PLATFORM EVIDENCE:
{json.dumps(context_data, indent=2)}

Provide a concise, highly professional response with bullet points and clear takeaways.
"""
                response = self._client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=chat_prompt
                )
                return {
                    "response": response.text.strip(),
                    "sources": ["PayLens Anomaly Detector", "Transaction Dataset Analytics"],
                    "is_ai_generated": True,
                    "engine": "Google Gemini (gemini-2.5-flash)"
                }
            except Exception as e:
                logger.error(f"Gemini chat failed: {e}")

        # Deterministic Assistant Response
        q_lower = user_message.lower()
        if "highest failure rate" in q_lower or "which bank" in q_lower:
            worst_bank = sorted(bank_breakdown, key=lambda x: x.failure_rate, reverse=True)[0]
            resp = (
                f"**Bank with Highest Failure Rate:**\n\n"
                f"- **{worst_bank.name}** currently has the highest failure rate at **{worst_bank.failure_rate * 100:.2f}%** "
                f"({worst_bank.failed:,} failed transactions out of {worst_bank.total:,} total).\n"
                f"- Most common error code across banks is **{error_breakdown[0].error_code}** ({error_breakdown[0].count} incidents)."
            )
        elif "biggest" in q_lower or "issue" in q_lower or "first" in q_lower or "incident" in q_lower:
            top_inc = incidents[0] if incidents else None
            if top_inc:
                resp = (
                    f"**Most Critical Payment Issue Detected:**\n\n"
                    f"- **Incident ID:** `{top_inc.incident_id}` [{top_inc.severity}]\n"
                    f"- **Entity:** {top_inc.bank} ({top_inc.payment_method})\n"
                    f"- **Success Rate Drop:** {top_inc.failure_rate_change} (fell to {top_inc.success_rate*100:.1f}% vs {top_inc.baseline_success_rate*100:.1f}% baseline)\n"
                    f"- **Estimated Transaction Value at Risk:** ₹{top_inc.estimated_transaction_value_at_risk:,.2f}\n"
                    f"- **Dominant Error:** `{top_inc.dominant_error}`\n\n"
                    f"**Immediate Recommendation:** Check the Investigation tab for `{top_inc.incident_id}` to review routing diversion options."
                )
            else:
                resp = "All payment rails are currently operating within normal baseline tolerance thresholds."
        elif "value at risk" in q_lower or "how much" in q_lower or "money" in q_lower:
            total_risk = sum(inc.estimated_transaction_value_at_risk for inc in incidents)
            resp = (
                f"**Total Estimated Transaction Value at Risk:**\n\n"
                f"- Current active exposure: **₹{total_risk:,.2f}** across {len(incidents)} anomalous incidents.\n"
                f"- *Clarification:* This metric represents the Estimated Transaction Value at Risk from affected failed transactions, not guaranteed lost revenue."
            )
        else:
            resp = (
                f"**PayLens Current Payment Status:**\n\n"
                f"- Overall platform success rate is **{kpis.success_rate*100:.1f}%** across {kpis.total_transactions:,} transactions.\n"
                f"- {len(incidents)} active incidents are currently flagged by the anomaly detection engine.\n"
                f"- Estimated Transaction Value at Risk is **₹{sum(inc.estimated_transaction_value_at_risk for inc in incidents):,.2f}**."
            )

        return {
            "response": resp,
            "sources": ["PayLens Deterministic Engine", "paylens_transactions.csv"],
            "is_ai_generated": False,
            "engine": "Deterministic Merchant Intelligence (Rule-based Fallback)"
        }


# Global singleton
from services.anomaly_detector import anomaly_detector
ai_investigator = AIInvestigator()

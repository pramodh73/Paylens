"""Pydantic schemas for PayLens API."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class SummaryKPIs(BaseModel):
    total_transactions: int = Field(..., description="Total count of transactions in dataset")
    successful_transactions: int = Field(..., description="Count of successful transactions")
    failed_transactions: int = Field(..., description="Count of failed transactions")
    success_rate: float = Field(..., description="Success rate percentage as a decimal (0-1)")
    failure_rate: float = Field(..., description="Failure rate percentage as a decimal (0-1)")
    total_transaction_value: float = Field(..., description="Gross transaction volume in INR")
    failed_transaction_value: float = Field(..., description="Total volume of failed transactions in INR")
    estimated_transaction_value_at_risk: float = Field(
        ...,
        description="Estimated transaction value at risk from affected anomalous transactions (estimate, not actual lost revenue)"
    )
    average_processing_time: float = Field(..., description="Average processing latency in seconds")
    active_incident_count: int = Field(0, description="Total active payment incidents detected")
    date_range_start: str = Field(..., description="Earliest transaction timestamp")
    date_range_end: str = Field(..., description="Latest transaction timestamp")

class BreakdownItem(BaseModel):
    name: str
    total: int
    successful: int
    failed: int
    success_rate: float
    failure_rate: float
    total_amount: float
    failed_amount: float

class ErrorCodeItem(BaseModel):
    error_code: str
    count: int
    percentage: float
    affected_amount: float

class TrendItem(BaseModel):
    timestamp: str
    label: str
    total: int
    success: int
    failed: int
    success_rate: float
    avg_processing_time: float

class DashboardSummary(BaseModel):
    kpis: SummaryKPIs
    payment_methods: List[BreakdownItem]
    banks: List[BreakdownItem]
    error_codes: List[ErrorCodeItem]
    daily_trends: List[TrendItem]
    hourly_trends: List[TrendItem]

class Incident(BaseModel):
    incident_id: str
    title: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    payment_method: str
    bank: str
    start_time: str
    end_time: str
    success_rate: float
    baseline_success_rate: float
    failure_rate_change: str
    affected_transactions: int
    total_window_transactions: int
    estimated_transaction_value_at_risk: float
    dominant_error: str
    avg_processing_time: float
    baseline_processing_time: float
    description: str

class InvestigationRequest(BaseModel):
    incident_id: Optional[str] = None
    incident_data: Optional[Incident] = None

class InvestigationResult(BaseModel):
    incident_id: str
    incident_summary: str
    likely_root_cause: str
    observed_evidence: List[str]
    ai_interpretation: str
    business_impact: str
    recommended_action: str
    confidence: str  # High, Medium, Low
    is_ai_generated: bool
    engine: str
    generated_at: str

class TransactionItem(BaseModel):
    transaction_id: str
    timestamp: str
    amount: float
    payment_method: str
    bank: str
    status: str
    error_code: Optional[str] = None
    processing_time_seconds: float
    customer_id: str

class TransactionListResponse(BaseModel):
    items: List[TransactionItem]
    total_count: int
    page: int
    page_size: int
    total_pages: int

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = []

class ChatResponse(BaseModel):
    response: str
    sources: Optional[List[str]] = []
    is_ai_generated: bool
    engine: str

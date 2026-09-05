"""PayLens - AI Payment Investigator & Analytics Platform
FastAPI Backend API
"""

import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
from fastapi import FastAPI, Query, HTTPException, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

from models.schemas import (
    SummaryKPIs,
    DashboardSummary,
    Incident,
    InvestigationRequest,
    InvestigationResult,
    TransactionListResponse,
    ChatRequest,
    ChatResponse
)
from services.data_service import data_service
from services.anomaly_detector import anomaly_detector
from services.ai_investigator import ai_investigator

app = FastAPI(
    title="PayLens API",
    description="AI-powered payment investigation and analytics platform for merchants (Razorpay Buildathon).",
    version="1.0.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(request: Request, exc: FileNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc), "type": "DATASET_NOT_FOUND"}
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "type": "DATASET_VALIDATION_ERROR"}
    )

# Router for reusable endpoints (supports both root and /api prefixes)
router = APIRouter()

@router.get("/")
def get_root():
    """Basic application information."""
    return {
        "name": "PayLens",
        "tagline": "AI-powered payment intelligence for merchants",
        "version": "1.0.0",
        "track": "Razorpay Buildathon - Open Track",
        "status": "operational",
        "dataset_loaded": data_service.is_loaded,
        "docs_url": "/docs"
    }

@router.get("/health")
def health_check():
    """Check backend health and dataset load status."""
    try:
        df = data_service.get_df()
        return {
            "status": "healthy",
            "service": "PayLens Backend",
            "timestamp": datetime.now().isoformat(),
            "dataset": {
                "loaded": True,
                "total_rows": len(df),
                "columns": list(df.columns)
            },
            "gemini_api_configured": bool(os.getenv("GEMINI_API_KEY", "").strip() and os.getenv("GEMINI_API_KEY") != "YOUR_KEY_HERE")
        }
    except Exception as e:
        return {
            "status": "degraded",
            "service": "PayLens Backend",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "dataset": {
                "loaded": False,
                "message": "Transaction dataset not found. Please place paylens_transactions.csv in backend/data/."
            }
        }

@router.get("/transactions/summary", response_model=DashboardSummary)
def get_summary():
    """Return platform KPIs, payment method breakdown, bank breakdown, error distribution, and trends."""
    try:
        incidents = anomaly_detector.detect_incidents()
        total_value_at_risk = sum(inc.estimated_transaction_value_at_risk for inc in incidents)
        
        kpis = data_service.get_summary_kpis(estimated_at_risk=total_value_at_risk)
        kpis.active_incident_count = len(incidents)

        methods = data_service.get_payment_method_breakdown()
        banks = data_service.get_bank_breakdown()
        error_codes = data_service.get_error_code_breakdown()
        daily_trends = data_service.get_daily_trends()
        hourly_trends = data_service.get_hourly_trends(days_limit=7)

        return DashboardSummary(
            kpis=kpis,
            payment_methods=methods,
            banks=banks,
            error_codes=error_codes,
            daily_trends=daily_trends,
            hourly_trends=hourly_trends
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {str(e)}")

@router.get("/transactions", response_model=TransactionListResponse)
def get_transactions(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    payment_method: Optional[str] = Query(None, description="Filter by payment method"),
    bank: Optional[str] = Query(None, description="Filter by bank"),
    status: Optional[str] = Query(None, description="Filter by status (success/failed)"),
    error_code: Optional[str] = Query(None, description="Filter by error code"),
    search: Optional[str] = Query(None, description="Search transaction_id, customer_id, or bank"),
    start_date: Optional[str] = Query(None, description="Filter starting timestamp"),
    end_date: Optional[str] = Query(None, description="Filter ending timestamp"),
    sort_by: str = Query("timestamp", description="Sort field"),
    sort_order: str = Query("desc", description="Sort direction (asc/desc)")
):
    """Paginated, searchable, and filterable transaction ledger."""
    try:
        return data_service.get_paginated_transactions(
            page=page,
            page_size=page_size,
            payment_method=payment_method,
            bank=bank,
            status=status,
            error_code=error_code,
            search=search,
            start_date=start_date,
            end_date=end_date,
            sort_by=sort_by,
            sort_order=sort_order
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch transactions: {str(e)}")

@router.get("/anomalies", response_model=List[Incident])
def get_anomalies(force_refresh: bool = False):
    """Return all detected payment incidents ranked by severity."""
    try:
        return anomaly_detector.detect_incidents(force_refresh=force_refresh)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to detect anomalies: {str(e)}")

@router.get("/anomalies/{incident_id}", response_model=Incident)
def get_anomaly_detail(incident_id: str):
    """Fetch details of a single incident."""
    incident = anomaly_detector.get_incident_by_id(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found")
    return incident

@router.post("/investigate", response_model=InvestigationResult)
def investigate_incident(payload: InvestigationRequest):
    """Run an AI-powered investigation for a specific incident with deterministic fallback."""
    try:
        target_incident: Optional[Incident] = None

        if payload.incident_data:
            target_incident = payload.incident_data
        elif payload.incident_id:
            target_incident = anomaly_detector.get_incident_by_id(payload.incident_id)

        if not target_incident:
            raise HTTPException(status_code=404, detail="Incident not found. Please provide a valid incident_id or incident_data.")

        result = ai_investigator.investigate(target_incident)
        return result
    except HTTPException:
        raise
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Investigation failed: {str(e)}")

@router.post("/assistant/chat", response_model=ChatResponse)
def chat_with_assistant(request: ChatRequest):
    """Merchant AI Assistant for answering payment health questions based on real dataset evidence."""
    try:
        data = ai_investigator.chat_with_assistant(request.message, request.history)
        return ChatResponse(
            response=data["response"],
            sources=data.get("sources", []),
            is_ai_generated=data.get("is_ai_generated", False),
            engine=data.get("engine", "PayLens Intelligence")
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Assistant request failed: {str(e)}")

# Mount both root and /api prefixes
app.include_router(router)
app.include_router(router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

"""Unit and integration tests for PayLens."""
import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from main import app
from services.data_service import data_service
from services.anomaly_detector import anomaly_detector
from services.ai_investigator import ai_investigator

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "PayLens"
    assert data["status"] == "operational"

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["dataset"]["loaded"] is True
    assert data["dataset"]["total_rows"] == 25000

def test_transactions_summary():
    response = client.get("/transactions/summary")
    assert response.status_code == 200
    data = response.json()
    
    kpis = data["kpis"]
    assert kpis["total_transactions"] == 25000
    assert kpis["successful_transactions"] > 20000
    assert kpis["failed_transactions"] > 1000
    assert 0.8 < kpis["success_rate"] < 1.0
    assert kpis["estimated_transaction_value_at_risk"] > 0

    assert len(data["payment_methods"]) >= 4
    assert len(data["banks"]) >= 6
    assert len(data["error_codes"]) >= 3
    assert len(data["daily_trends"]) > 20

def test_anomaly_detection():
    incidents = anomaly_detector.detect_incidents()
    assert len(incidents) > 0
    top = incidents[0]
    assert top.incident_id.startswith("INC-")
    assert top.severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    assert top.estimated_transaction_value_at_risk > 0
    assert top.affected_transactions > 0
    assert top.success_rate < top.baseline_success_rate

def test_anomalies_endpoint():
    response = client.get("/anomalies")
    assert response.status_code == 200
    incidents = response.json()
    assert isinstance(incidents, list)
    assert len(incidents) > 0

def test_investigate_endpoint():
    # First fetch incidents
    res = client.get("/anomalies")
    incidents = res.json()
    target_id = incidents[0]["incident_id"]

    # Run investigation
    inv_res = client.post("/investigate", json={"incident_id": target_id})
    assert inv_res.status_code == 200
    data = inv_res.json()
    assert data["incident_id"] == target_id
    assert len(data["likely_root_cause"]) > 0
    assert len(data["observed_evidence"]) > 0
    assert len(data["business_impact"]) > 0
    assert len(data["recommended_action"]) > 0
    assert data["confidence"] in ["High", "Medium", "Low"]
    assert "Estimated Transaction Value at Risk" in data["business_impact"]

def test_transactions_pagination_and_filter():
    # Page 1
    res1 = client.get("/transactions?page=1&page_size=10")
    assert res1.status_code == 200
    data1 = res1.json()
    assert len(data1["items"]) == 10
    assert data1["total_count"] == 25000
    assert data1["total_pages"] == 2500

    # Filter by bank and status
    res2 = client.get("/transactions?bank=SBI&status=failed&page=1&page_size=10")
    assert res2.status_code == 200
    data2 = res2.json()
    for item in data2["items"]:
        assert item["bank"] == "SBI"
        assert item["status"] == "failed"

def test_assistant_chat():
    res = client.post("/assistant/chat", json={"message": "What is the biggest payment issue right now?"})
    assert res.status_code == 200
    data = res.json()
    assert len(data["response"]) > 0
    assert "sources" in data

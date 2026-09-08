import io
import time
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.main import app
from app.db import engine, create_db
from app.models.fact import Document, Fact, CrossDocumentLink, IngestionJob
from app.routers.ingest import process_ingestion_background

client = TestClient(app)


def setup_module():
    create_db()


def make_dummy_pdf_bytes() -> bytes:
    """Generate minimal valid PDF bytes starting with %PDF-."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n"
        b"4 0 obj\n<< /Length 75 >>\nstream\n"
        b"BT /F1 12 Tf 100 700 Td (In FY24, Delhivery Limited reported Revenue from Operations 81,415.38 Rs in Million.) Tj ET\n"
        b"endstream\nendobj\n"
        b"xref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000206 00000 n \n"
        b"trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n333\n%%EOF\n"
    )


def test_health_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"


def test_reject_non_pdf():
    files = {"file": ("test.txt", b"plain text", "text/plain")}
    res = client.post("/api/ingest", files=files)
    assert res.status_code == 400
    assert "Only PDF" in res.json()["detail"]


def test_reject_invalid_pdf_magic():
    files = {"file": ("fake.pdf", b"NOT_A_REAL_PDF", "application/pdf")}
    res = client.post("/api/ingest", files=files)
    assert res.status_code == 400
    assert "PDF magic header" in res.json()["detail"]


def test_showcase_endpoint_returns_mandatory_cases():
    res = client.get("/api/showcase")
    assert res.status_code == 200
    cases = res.json()["cases"]
    assert len(cases) >= 4
    types = {c["link"]["relation_type"] for c in cases}
    assert "CORROBORATED" in types
    assert "GENUINE_CONTRADICTION" in types
    assert any(t in types for t in ("RECONCILED_SCOPE", "RECONCILED_METHODOLOGY", "RECONCILED_TEMPORAL"))


def test_facts_endpoint_filters():
    res = client.get("/api/facts?entity=Delhivery")
    assert res.status_code == 200
    facts = res.json()
    assert len(facts) > 0
    for f in facts:
        assert "delhivery" in f["entity"].lower()


def test_async_ingestion_lifecycle():
    pdf_bytes = make_dummy_pdf_bytes()
    files = {"file": ("delhivery_report_test.pdf", pdf_bytes, "application/pdf")}
    res = client.post("/api/ingest", files=files)
    assert res.status_code == 200
    job_data = res.json()
    assert "job_id" in job_data
    job_id = job_data["job_id"]

    # Poll status
    poll_res = client.get(f"/api/ingest/{job_id}")
    assert poll_res.status_code == 200
    status_data = poll_res.json()
    assert status_data["status"] in ("queued", "parsing", "extracting", "reconciling", "completed")

import os
os.environ.setdefault("SMARTFACTORY_DATABASE_URL", "sqlite:///./test-smartfactory.db")
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app import main as main_module
from app.database import Base, engine, SessionLocal
from app.main import app
from app.models import Purchase, ProductionRun, Order, Invoice, Payment, Expense


@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def login(client, email="admin@smartfactory.local", password="Admin123!"):
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_benchmark_production_stock_gst_and_receivables():
    with TestClient(app) as client:
        headers = login(client)
        # Unsupported GET falls through to the API guard; POST is the registered method.
        assert client.get("/api/benchmark/run", headers=headers).status_code in (404, 405)
        result = client.post("/api/benchmark/run", headers=headers)
        assert result.status_code == 200, result.text
        r = result.json()["results"]
        assert r["flour_kg"] == 120
        assert r["flour_weighted_average_rate"] == 43.125
        assert r["oil_litres"] == 19.5
        assert r["spice_kg"] == 3.8
        assert r["pouches_on_hand"] == 306
        assert r["pouches_available"] == 300
        assert r["cartons"] == 21
        assert r["finished_after_dispatch"] == 88
        assert r["yield_variance_percent"] == -6
        assert r["oil_consumption_variance_percent"] == 5
        assert r["invoice_taxable_paise"] == 750000
        assert r["cgst_paise"] == 18750 and r["sgst_paise"] == 18750
        assert r["invoice_total_paise"] == 787500
        assert r["retailer_outstanding_paise"] == 387500
        assert r["distributor_shortage"] == 32
        assert r["production_cost_paise"] == 587000
        assert r["cost_per_packet_paise"] == 3122
        dashboard = client.get("/api/dashboard", headers=headers).json()
        flour = next(m for m in dashboard["materials"] if m["name"] == "Flour")
        assert flour["average_rate_paise"] == 4312.5
        assert {o["customer"]: (o["quantity"], o["status"]) for o in dashboard["orders"]} == {
            "Retailer A": (150, "dispatched"), "Distributor B": (120, "stock_shortage")}
        assert dashboard["invoices"][0]["paid_paise"] == 400000
        assert dashboard["stats"]["stock"] == 88
        with SessionLocal() as db:
            purchase = db.query(Purchase).one()
            production = db.query(ProductionRun).one()
            invoice = db.query(Invoice).one()
            payment = db.query(Payment).one()
            expenses = {x.category: x.amount_paise for x in db.query(Expense).all()}
            assert purchase.total_paise == 270000
            assert production.actual_output == 188
            assert invoice.total_paise == 787500 and invoice.order.status == "dispatched"
            assert payment.amount_paise == 400000
            assert expenses == {"Labour": 120000, "Gas & power": 60000}


def test_failed_production_does_not_partially_change_stock():
    with TestClient(app) as client:
        headers = login(client)
        before = client.get("/api/dashboard", headers=headers).json()
        product_id = before["products"][0]["id"]
        response = client.post("/api/production", headers=headers, json={
            "product_id": product_id, "batch_size": 1, "actual_output": 188,
            "damaged_pouches": 0, "labour": 1200, "utilities": 600,
            "materials": [{"name":"Flour","quantity":999},{"name":"Cooking oil","quantity":10},
                          {"name":"Salt and spice mix","quantity":1.2},{"name":"200 g pouch","quantity":200},
                          {"name":"Carton","quantity":10}]})
        assert response.status_code == 409
        after = client.get("/api/dashboard", headers=headers).json()
        flour_before = next(m["stock"] for m in before["materials"] if m["name"] == "Flour")
        flour_after = next(m["stock"] for m in after["materials"] if m["name"] == "Flour")
        assert flour_after == flour_before == 100
        assert after["stats"]["stock"] == before["stats"]["stock"] == 50


def test_failed_benchmark_rolls_back_reset_and_scenario(monkeypatch):
    with TestClient(app) as client:
        headers = login(client)
        assert client.post("/api/benchmark/run", headers=headers).status_code == 200

        def fail_after_reset(db, name):
            raise HTTPException(409, "forced transaction failure")

        monkeypatch.setattr(main_module, "material_by", fail_after_reset)
        failed = client.post("/api/benchmark/run", headers=headers)
        assert failed.status_code == 409
        dashboard = client.get("/api/dashboard", headers=headers).json()
        assert dashboard["benchmark"]["complete"] is True
        assert len(dashboard["orders"]) == 2
        assert dashboard["stats"]["stock"] == 88


def test_auditor_is_read_only_for_stock_actions():
    with TestClient(app) as client:
        headers = login(client, "audit@smartfactory.local", "Audit123!")
        response = client.post("/api/benchmark/run", headers=headers)
        assert response.status_code == 403
        reports = client.get("/api/reports/finished-stock?format=csv", headers=headers)
        assert reports.status_code == 200
        assert "closing_stock" in reports.text


def test_karnataka_invoice_uses_igst_and_pdf_download_works():
    with TestClient(app) as client:
        headers = login(client)
        result=client.post("/api/benchmark/run",headers=headers)
        assert result.status_code == 200
        dashboard=client.get("/api/dashboard",headers=headers).json()
        customer=next(c for c in dashboard["customers"] if c["name"]=="Distributor B")
        product=dashboard["products"][0]
        order=client.post("/api/orders",headers=headers,json={"customer_id":customer["id"],"product_id":product["id"],"quantity":1}).json()
        approved=client.post(f"/api/orders/{order['id']}/decision?decision=approve",headers=headers)
        assert approved.status_code==200 and approved.json()["status"]=="approved"
        invoice=client.post(f"/api/orders/{order['id']}/invoice",headers=headers)
        assert invoice.status_code==200
        assert invoice.json()["igst_paise"]==250
        assert invoice.json()["cgst_paise"]==invoice.json()["sgst_paise"]==0
        pdf=client.get(f"/api/invoices/{invoice.json()['id']}/pdf",headers=headers)
        assert pdf.status_code==200 and pdf.content.startswith(b"%PDF")


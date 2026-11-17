import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_public_search():
    res = client.get("/api/v1/public/search?q=Civil")
    assert res.status_code == 200
    data = res.json()
    assert "stops" in data
    assert "routes" in data
    assert len(data["stops"]) > 0

def test_public_stop_details_and_arrivals():
    res = client.get("/api/v1/public/stops/S001")
    assert res.status_code == 200
    data = res.json()
    assert data["code"] == "S001"
    assert "name" in data

    res_arr = client.get("/api/v1/public/stops/S001/arrivals")
    assert res_arr.status_code == 200
    arr_data = res_arr.json()
    assert "arrivals" in arr_data
    assert len(arr_data["arrivals"]) > 0

def test_public_route_live():
    res = client.get("/api/v1/public/routes/7A/live")
    assert res.status_code == 200
    data = res.json()
    assert "route" in data
    assert "stops" in data
    assert "polyline" in data

def test_public_journey_plan():
    res = client.get("/api/v1/public/plan?from=S001&to=S009")
    assert res.status_code == 200
    data = res.json()
    assert "plans" in data
    assert len(data["plans"]) > 0

def test_public_alerts():
    res = client.get("/api/v1/public/alerts")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_ops_fleet_and_incidents():
    res_fleet = client.get("/api/v1/ops/fleet")
    assert res_fleet.status_code == 200
    assert len(res_fleet.json()) >= 14

    res_inc = client.get("/api/v1/incidents")
    assert res_inc.status_code == 200
    assert isinstance(res_inc.json(), list)

def test_scheduling_endpoints():
    res_gantt = client.get("/api/v1/schedule/gantt")
    assert res_gantt.status_code == 200
    data = res_gantt.json()
    assert "rows" in data
    assert len(data["rows"]) > 0

    res_gen = client.post("/api/v1/schedule/generate", json={"service_date": "2026-11-18"})
    assert res_gen.status_code == 200
    assert res_gen.json()["trips_count"] > 0

def test_reports_endpoints():
    res_ot = client.get("/api/v1/reports/on-time")
    assert res_ot.status_code == 200
    assert len(res_ot.json()) >= 6

    res_csv = client.get("/api/v1/reports/on-time?format=csv")
    assert res_csv.status_code == 200
    assert "Route,OnTimePercent" in res_csv.text

    res_util = client.get("/api/v1/reports/utilisation")
    assert res_util.status_code == 200
    assert "fleet_utilisation_pct" in res_util.json()

import pytest
import sqlite3
import json
import threading
import time
import os
import tempfile
import urllib.request
from datetime import date
from dashboard.server import create_server

@pytest.fixture
def test_db():
    fd, path = tempfile.mkstemp()
    os.close(fd)
    
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    
    # Initialize schema
    cursor.execute("CREATE TABLE daily_budget (date TEXT PRIMARY KEY, spent_amount FLOAT)")
    cursor.execute("CREATE TABLE issued_seals (seal_id TEXT PRIMARY KEY, amount FLOAT, vendor TEXT, status TEXT, masked_card TEXT, expiration_date TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
    cursor.execute("CREATE TABLE dashboard_settings (key TEXT PRIMARY KEY, value TEXT)")
    
    # Seed data
    today = date.today().isoformat()
    cursor.execute("INSERT INTO daily_budget (date, spent_amount) VALUES (?, ?)", (today, 150.0))
    cursor.execute("INSERT INTO dashboard_settings (key, value) VALUES (?, ?)", ("max_daily_budget", "1000"))
    
    cursor.execute("""
        INSERT INTO issued_seals (seal_id, amount, vendor, status, masked_card)
        VALUES (?, ?, ?, ?, ?)
    """, ("seal_123", 50.0, "Amazon", "Issued", "****-****-****-1234"))
    
    cursor.execute("""
        INSERT INTO issued_seals (seal_id, amount, vendor, status, masked_card)
        VALUES (?, ?, ?, ?, ?)
    """, ("seal_456", 25.0, "Steam", "Rejected", "****-****-****-5678"))
    
    conn.commit()
    conn.close()
    
    yield path
    
    if os.path.exists(path):
        os.remove(path)

@pytest.fixture
def server(test_db):
    port = 3211  # Use a different port for tests
    server = create_server(port, test_db)
    
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    
    # Give it a moment to start
    time.sleep(0.5)
    
    yield f"http://127.0.0.1:{port}"
    
    server.shutdown()
    server.server_close()
    thread.join()

def test_get_budget(server):
    with urllib.request.urlopen(f"{server}/api/budget/today") as response:
        assert response.status == 200
        data = json.loads(response.read().decode())
        assert data["spent"] == 150.0
        assert data["max"] == 1000.0
        assert data["remaining"] == 850.0

def test_get_seals(server):
    with urllib.request.urlopen(f"{server}/api/seals") as response:
        assert response.status == 200
        data = json.loads(response.read().decode())
        assert len(data) == 2
        assert data[0]["seal_id"] in ["seal_123", "seal_456"]

def test_get_seals_filtered(server):
    with urllib.request.urlopen(f"{server}/api/seals?status=rejected") as response:
        assert response.status == 200
        data = json.loads(response.read().decode())
        assert len(data) == 1
        assert data[0]["status"] == "Rejected"
        assert data[0]["seal_id"] == "seal_456"

def test_put_setting(server):
    url = f"{server}/api/settings/max_daily_budget"
    data = json.dumps({"value": "2000"}).encode()
    req = urllib.request.Request(url, data=data, method="PUT")
    req.add_header("Content-Type", "application/json")
    
    with urllib.request.urlopen(req) as response:
        assert response.status == 200
        res_data = json.loads(response.read().decode())
        assert res_data["key"] == "max_daily_budget"
        assert res_data["value"] == "2000"

    # Verify update persisted
    with urllib.request.urlopen(f"{server}/api/budget/today") as response:
        data = json.loads(response.read().decode())
        assert data["max"] == 2000.0

def test_static_file(server):
    # This assumes index.html exists in dashboard/
    try:
        with urllib.request.urlopen(f"{server}/") as response:
            assert response.status == 200
            assert "text/html" in response.getheader("Content-Type")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            pytest.skip("index.html not found, skipping static file test")
        else:
            raise

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

DATA_DIR = Path(__file__).parent / "data"

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_upload_dataset():
    csv_path = DATA_DIR / "sales.csv"
    with open(csv_path, "rb") as f:
        response = client.post(
            "/api/v1/datasets/upload",
            files={"file": ("sales.csv", f, "text/csv")}
        )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "dataset_id" in data
    
    dataset_id = data["dataset_id"]

    # Test GET dataset metadata
    response = client.get(f"/api/v1/datasets/{dataset_id}")
    assert response.status_code == 200
    metadata = response.json()
    assert metadata["dataset_id"] == dataset_id

    # Test GET dataset schema
    response = client.get(f"/api/v1/datasets/{dataset_id}/schema")
    assert response.status_code == 200
    schema = response.json()
    assert schema["dataset_id"] == dataset_id
    assert "column_details" in schema

    # Test GET dataset profile
    response = client.get(f"/api/v1/datasets/{dataset_id}/profile")
    assert response.status_code == 200
    profile = response.json()
    assert profile["dataset_id"] == dataset_id
    assert "column_profiles" in profile

def test_get_nonexistent_dataset():
    response = client.get("/api/v1/datasets/ds_nonexistent")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DATASET_NOT_FOUND"

    response = client.get("/api/v1/datasets/ds_nonexistent/schema")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DATASET_NOT_FOUND"

    response = client.get("/api/v1/datasets/ds_nonexistent/profile")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DATASET_NOT_FOUND"

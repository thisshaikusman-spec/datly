from io import BytesIO

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_upload_and_get_dataset():
    csv_content = b"col1,col2\n1,2\n3,4\n"
    
    upload_response = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("test.csv", BytesIO(csv_content), "text/csv")}
    )
    
    assert upload_response.status_code == 200
    dataset_id = upload_response.json()["dataset_id"]
    
    metadata_response = client.get(
        f"/api/v1/datasets/{dataset_id}"
    )
    
    assert metadata_response.status_code == 200
    metadata = metadata_response.json()
    assert metadata["dataset_id"] == dataset_id

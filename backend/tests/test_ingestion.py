from pathlib import Path

import pytest
from fastapi import UploadFile

from app.core.exceptions import DatlyException
from app.repositories.dataset_store import dataset_store
from app.services.ingestion.service import process_upload

DATA_DIR = Path(__file__).parent / "data"

def test_process_upload_csv():
    csv_path = DATA_DIR / "sales.csv"
    with open(csv_path, "rb") as f:
        upload_file = UploadFile(filename="sales.csv", file=f, size=csv_path.stat().st_size)
        metadata = process_upload(upload_file)
        
    assert metadata.success is True
    assert metadata.filename == "sales.csv"
    assert metadata.file_type == "csv"
    assert metadata.rows == 5
    assert metadata.columns == 5
    
    # Check repository
    assert dataset_store.exists(metadata.dataset_id)
    df = dataset_store.get_dataset(metadata.dataset_id)
    assert df is not None
    assert len(df) == 5

def test_process_upload_unsupported():
    with open(__file__, "rb") as f:
        upload_file = UploadFile(filename="test.py", file=f, size=Path(__file__).stat().st_size)
        with pytest.raises(DatlyException) as exc:
            process_upload(upload_file)
        assert exc.value.code == "UNSUPPORTED_FILE_TYPE"

def test_process_upload_empty():
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".csv") as f:
        upload_file = UploadFile(filename="empty.csv", file=f, size=0)
        with pytest.raises(DatlyException) as exc:
            process_upload(upload_file)
        assert exc.value.code == "INVALID_FILE"

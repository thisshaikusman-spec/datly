import os
import uuid
from datetime import UTC, datetime

from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import DatlyException
from app.models.dataset import DatasetMetadata
from app.repositories.dataset_store import dataset_store
from app.services.ingestion.csv_loader import load_csv
from app.services.ingestion.excel_loader import load_excel
from app.services.ingestion.json_loader import load_json


def generate_dataset_id() -> str:
    return f"ds_{uuid.uuid4().hex[:8]}"

def process_upload(file: UploadFile, workspace_id: str | None = None) -> DatasetMetadata:
    if not file or not file.filename:
        raise DatlyException(code="INVALID_FILE", message="No file was uploaded.", status_code=400)

    _, ext = os.path.splitext(file.filename)
    ext = ext.lstrip('.').lower()
    
    if ext not in settings.allowed_extensions:
        raise DatlyException(
            code="UNSUPPORTED_FILE_TYPE", 
            message="Only CSV, XLSX and JSON files are supported.", 
            status_code=400
        )

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size == 0:
         raise DatlyException(code="INVALID_FILE", message="Uploaded file is empty.", status_code=400)

    if file_size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise DatlyException(
            code="FILE_TOO_LARGE", 
            message=f"File exceeds maximum size of {settings.MAX_UPLOAD_SIZE_MB}MB.", 
            status_code=413
        )

    try:
        if ext == 'csv':
            df = load_csv(file.file)
        elif ext in ['xlsx', 'xls']:
            df = load_excel(file.file)
        elif ext == 'json':
            df = load_json(file.file)
        else:
            raise DatlyException(code="UNSUPPORTED_FILE_TYPE", message="Unsupported file type.", status_code=400)
    except Exception as e:  # noqa: BLE001
        raise DatlyException(code="MALFORMED_DATASET", message=f"Failed to parse dataset: {e!s}", status_code=400)

    if df is None or df.empty:
        raise DatlyException(code="EMPTY_DATASET", message="The parsed dataset contains no data rows.", status_code=400)
        
    if len(df.columns) == 0:
        raise DatlyException(code="EMPTY_DATASET", message="The dataset has no columns.", status_code=400)

    from app.services.ingestion.cleaner import clean_dataframe
    df = clean_dataframe(df)
        
    dataset_id = generate_dataset_id()
    
    metadata = DatasetMetadata(
        success=True,
        dataset_id=dataset_id,
        filename=file.filename,
        file_type=ext,
        rows=len(df),
        columns=len(df.columns),
        created_at=datetime.now(UTC),
        workspace_id=workspace_id or "default",
    )
    
    dataset_store.save_dataset(metadata, df, workspace_id=workspace_id)
    
    return metadata

import logging

import pandas as pd

from app.models.dataset import DatasetMetadata
from app.repositories.workspace_store import workspace_store

logger = logging.getLogger("datly.dataset_store")


class InMemoryDatasetStore:
    def __init__(self):
        self._store = workspace_store
        self._dataframes = workspace_store._dataframes
        self._metadata = workspace_store._metadata

    def save_dataset(self, metadata: DatasetMetadata, df: pd.DataFrame, workspace_id: str | None = None) -> None:
        logger.debug(f"save_dataset called with ds_id {metadata.dataset_id}")
        self._store.save_dataset(metadata, df, workspace_id=workspace_id or metadata.workspace_id)

    def get_dataset(self, dataset_id: str) -> pd.DataFrame | None:
        return self._store.get_dataset(dataset_id)

    def get_metadata(self, dataset_id: str) -> DatasetMetadata | None:
        logger.debug(f"get_metadata called with ds_id {dataset_id}")
        return self._store.get_metadata(dataset_id)

    def exists(self, dataset_id: str) -> bool:
        return self._store.exists(dataset_id)


dataset_store = InMemoryDatasetStore()

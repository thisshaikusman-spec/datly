import json
import logging
import os
import re
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from app.core.config import settings
from app.core.exceptions import DatlyException
from app.models.dataset import DatasetMetadata
from app.models.workspace import Workspace

logger = logging.getLogger("datly.workspace_store")


def sanitize_alias(filename: str) -> str:
    """Generate a clean alias identifier from a filename (e.g. sales_2024.csv -> sales_2024)."""
    base, _ = os.path.splitext(filename)
    alias = re.sub(r"[^a-zA-Z0-9_]", "_", base.strip().lower())
    alias = re.sub(r"_+", "_", alias).strip("_")
    if not alias or alias[0].isdigit():
        alias = f"ds_{alias}"
    return alias


def generate_unique_alias(filename: str, existing_aliases: set[str]) -> str:
    base_alias = sanitize_alias(filename)
    alias = base_alias
    counter = 1
    while alias in existing_aliases:
        counter += 1
        alias = f"{base_alias}_{counter}"
    return alias


class WorkspaceStore:
    def __init__(self, data_dir: str | Path | None = None):
        if data_dir is None:
            # backend/data
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.data_dir = base_dir / settings.DATA_DIR
        else:
            self.data_dir = Path(data_dir)

        self.data_dir.mkdir(parents=True, exist_ok=True)

        # In-memory caches in front
        self._workspaces: dict[str, Workspace] = {}
        self._dataframes: dict[str, pd.DataFrame] = {}
        self._metadata: dict[str, DatasetMetadata] = {}
        # Mapping dataset_id -> workspace_id
        self._dataset_to_workspace: dict[str, str] = {}

        # Scan disk on initialization to recover persisted workspaces
        self._load_from_disk()

    def _load_from_disk(self) -> None:
        if not self.data_dir.exists():
            return

        for ws_dir in self.data_dir.iterdir():
            if not ws_dir.is_dir():
                continue
            ws_id = ws_dir.name
            ws_meta_file = ws_dir / "workspace.json"
            if ws_meta_file.exists():
                try:
                    with open(ws_meta_file, encoding="utf-8") as f:
                        data = json.load(f)
                    ws = Workspace.model_validate(data)
                    self._workspaces[ws_id] = ws
                except Exception as e:  # noqa: BLE001
                    logger.warning(f"Failed to load workspace {ws_id}: {e}")
                    ws = Workspace(id=ws_id, created_at=datetime.now(UTC), dataset_ids=[])
                    self._workspaces[ws_id] = ws
            else:
                ws = Workspace(id=ws_id, created_at=datetime.now(UTC), dataset_ids=[])
                self._workspaces[ws_id] = ws

            # Scan datasets in this workspace directory
            for ds_file in ws_dir.glob("*.json"):
                if ds_file.name == "workspace.json":
                    continue
                ds_id = ds_file.stem
                try:
                    with open(ds_file, encoding="utf-8") as f:
                        meta_dict = json.load(f)
                    meta = DatasetMetadata.model_validate(meta_dict)
                    meta.workspace_id = ws_id
                    self._metadata[ds_id] = meta
                    self._dataset_to_workspace[ds_id] = ws_id
                    if ds_id not in ws.dataset_ids:
                        ws.dataset_ids.append(ds_id)
                except Exception as e:  # noqa: BLE001
                    logger.warning(f"Failed to load dataset metadata {ds_file}: {e}")

        logger.info(f"[STORE] Loaded {len(self._workspaces)} workspaces and {len(self._metadata)} datasets from disk.")

    def create_workspace(self, workspace_id: str | None = None, name: str = "Default Workspace") -> Workspace:
        import uuid
        ws_id = workspace_id or f"ws_{uuid.uuid4().hex[:8]}"
        ws = Workspace(id=ws_id, name=name, created_at=datetime.now(UTC), dataset_ids=[])
        self._workspaces[ws_id] = ws

        # Persist workspace directory
        ws_dir = self.data_dir / ws_id
        ws_dir.mkdir(parents=True, exist_ok=True)
        with open(ws_dir / "workspace.json", "w", encoding="utf-8") as f:
            f.write(ws.model_dump_json(indent=2))

        return ws

    def get_or_create_workspace(self, workspace_id: str | None) -> Workspace:
        if not workspace_id:
            return self.create_workspace()
        if workspace_id in self._workspaces:
            return self._workspaces[workspace_id]
        return self.create_workspace(workspace_id)

    def get_workspace(self, workspace_id: str) -> Workspace | None:
        return self._workspaces.get(workspace_id)

    def list_workspaces(self) -> list[Workspace]:
        return list(self._workspaces.values())

    def save_dataset(self, metadata: DatasetMetadata, df: pd.DataFrame, workspace_id: str | None = None) -> None:
        ws_id = workspace_id or metadata.workspace_id or "default"
        ws = self.get_or_create_workspace(ws_id)

        # Check maximum datasets per workspace
        if metadata.dataset_id not in ws.dataset_ids and len(ws.dataset_ids) >= settings.MAX_DATASETS_PER_WORKSPACE:
            if ws_id == "default" and len(ws.dataset_ids) > 0:
                self.delete_dataset("default", ws.dataset_ids[0])
            else:
                raise DatlyException(
                    code="WORKSPACE_LIMIT_EXCEEDED",
                    message=f"Workspace has reached the maximum of {settings.MAX_DATASETS_PER_WORKSPACE} datasets.",
                    status_code=400,
                )

        # Generate unique alias for this workspace
        existing_aliases = {
            self._metadata[did].alias
            for did in ws.dataset_ids
            if did in self._metadata and self._metadata[did].alias
        }
        if not metadata.alias:
            metadata.alias = generate_unique_alias(metadata.filename, existing_aliases)
        metadata.workspace_id = ws_id

        # Update in-memory caches
        ds_id = metadata.dataset_id
        self._metadata[ds_id] = metadata
        self._dataframes[ds_id] = df
        self._dataset_to_workspace[ds_id] = ws_id
        if ds_id not in ws.dataset_ids:
            ws.dataset_ids.append(ds_id)

        # Persist to disk (Parquet + JSON metadata)
        ws_dir = self.data_dir / ws_id
        ws_dir.mkdir(parents=True, exist_ok=True)

        parquet_path = ws_dir / f"{ds_id}.parquet"
        try:
            df.to_parquet(parquet_path, index=False)
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[STORE] Failed to save parquet ({e}), converting object columns to string")
            safe_df = df.copy()
            for col in safe_df.columns:
                if safe_df[col].dtype == "object":
                    safe_df[col] = safe_df[col].astype(str)
            safe_df.to_parquet(parquet_path, index=False)

        json_path = ws_dir / f"{ds_id}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(metadata.model_dump_json(indent=2))

        # Update workspace.json
        with open(ws_dir / "workspace.json", "w", encoding="utf-8") as f:
            f.write(ws.model_dump_json(indent=2))

        logger.info(f"[STORE] Saved dataset {ds_id} (alias: {metadata.alias}) in workspace {ws_id}")

    def get_dataset(self, dataset_id: str) -> pd.DataFrame | None:
        if dataset_id in self._dataframes:
            return self._dataframes[dataset_id]

        # Try loading from disk
        ws_id = self._dataset_to_workspace.get(dataset_id)
        if not ws_id:
            # Check all workspace dirs
            for ws_dir in self.data_dir.iterdir():
                if (ws_dir / f"{dataset_id}.parquet").exists():
                    ws_id = ws_dir.name
                    break

        if ws_id:
            parquet_path = self.data_dir / ws_id / f"{dataset_id}.parquet"
            if parquet_path.exists():
                try:
                    df = pd.read_parquet(parquet_path)
                    self._dataframes[dataset_id] = df
                    return df
                except Exception as e:  # noqa: BLE001
                    logger.error(f"[STORE] Error reading parquet {parquet_path}: {e}")
        return None

    def get_metadata(self, dataset_id: str) -> DatasetMetadata | None:
        return self._metadata.get(dataset_id)

    def get_dataset_by_alias(self, workspace_id: str, alias: str) -> tuple[DatasetMetadata, pd.DataFrame] | None:
        ws = self._workspaces.get(workspace_id)
        if not ws:
            return None
        target_alias = alias.lower().strip()
        for did in ws.dataset_ids:
            meta = self.get_metadata(did)
            if meta and meta.alias and meta.alias.lower() == target_alias:
                df = self.get_dataset(did)
                if df is not None:
                    return meta, df
        return None

    def list_workspace_datasets(self, workspace_id: str) -> list[DatasetMetadata]:
        ws = self._workspaces.get(workspace_id)
        if not ws:
            return []
        datasets: list[DatasetMetadata] = []
        for did in ws.dataset_ids:
            meta = self.get_metadata(did)
            if meta:
                datasets.append(meta)
        return datasets

    def delete_dataset(self, workspace_id: str, dataset_id: str) -> bool:
        ws = self._workspaces.get(workspace_id)
        if not ws or dataset_id not in ws.dataset_ids:
            return False

        ws.dataset_ids.remove(dataset_id)
        self._dataframes.pop(dataset_id, None)
        self._metadata.pop(dataset_id, None)
        self._dataset_to_workspace.pop(dataset_id, None)

        ws_dir = self.data_dir / workspace_id
        parquet_path = ws_dir / f"{dataset_id}.parquet"
        json_path = ws_dir / f"{dataset_id}.json"
        if parquet_path.exists():
            try:
                parquet_path.unlink()
            except Exception as e:  # noqa: BLE001
                logger.warning(f"Failed to delete {parquet_path}: {e}")
        if json_path.exists():
            try:
                json_path.unlink()
            except Exception as e:  # noqa: BLE001
                logger.warning(f"Failed to delete {json_path}: {e}")

        # Update workspace.json
        with open(ws_dir / "workspace.json", "w", encoding="utf-8") as f:
            f.write(ws.model_dump_json(indent=2))

        logger.info(f"[STORE] Deleted dataset {dataset_id} from workspace {workspace_id}")
        return True

    def exists(self, dataset_id: str) -> bool:
        return dataset_id in self._metadata


# Global singleton instance
workspace_store = WorkspaceStore()

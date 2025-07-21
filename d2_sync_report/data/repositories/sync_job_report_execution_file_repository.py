from datetime import datetime
from pydantic import BaseModel

from d2_sync_report.domain.repositories.sync_job_report_execution_repository import (
    SyncJobReportExecutionRepository,
)
import os
from typing import Optional
from d2_sync_report.domain.entities.sync_job_report_execution import SyncJobReportExecution


class SyncJobReportExecutionFileRepository(SyncJobReportExecutionRepository):
    def __init__(self):
        self.cache = FileCache()

    def save_last(self, execution: SyncJobReportExecution) -> None:
        props = FileCacheProps(
            last_processed=execution.last_processed, last_sync=execution.last_sync
        )
        self.cache.save(props)

    def get_last(self) -> Optional[SyncJobReportExecution]:
        props = self.cache.load()
        if props is None:
            return None
        return SyncJobReportExecution(
            last_processed=props.last_processed, last_sync=props.last_sync
        )


class FileCacheProps(BaseModel):
    last_processed: datetime
    last_sync: datetime


class FileCache:
    filename = "cache.json"

    def save(self, props: FileCacheProps) -> None:
        cache_path = self._get_cache_path()

        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(props.model_dump_json(indent=4) + "\n")
        print(f"Cache saved: {cache_path}")

    def load(self) -> Optional[FileCacheProps]:
        cache_path = self._get_cache_path()

        if os.path.exists(cache_path):
            print(f"Cache loaded: {cache_path}")

            try:
                cache_props = FileCacheProps.model_validate_json(
                    open(cache_path, "r", encoding="utf-8").read()
                )
                print(f"Cache: {cache_props}")
                return cache_props
            except ValueError as exc:
                print(f"Cache load error: {exc}")
                # File is corrupted, remove it
                os.remove(cache_path)
                return None

        else:
            print(f"Cache file does not exist: {cache_path}")
            return None

    def _get_cache_path(self) -> str:
        script_folder = os.path.dirname(os.path.dirname(__file__))
        return os.path.join(script_folder, self.filename)

from pydantic import BaseModel
from d2_sync_report.data.dhis2_api import D2Api
from d2_sync_report.domain.entities.metadata_versioning import MetadataVersioning
from d2_sync_report.domain.repositories.metadata_versioning_repository import (
    MetadataVersioningRepository,
)


class MetadataVersioningD2Repository(MetadataVersioningRepository):
    def __init__(self, api: D2Api):
        self.api = api

    def get(self) -> MetadataVersioning:
        local_version = self.get_local_metadata_version()
        remote_version = self.get_remote_metadata_version()
        return MetadataVersioning(local=local_version, remote=remote_version)

    def get_local_metadata_version(self) -> str:
        res = self.api.get("/api/metadata/version", MetadataVersionResponse)
        return res.name

    def get_remote_metadata_version(self) -> str:
        res = self.api.get("/api/systemSettings", SystemSettingsResponse)
        return res.keyRemoteMetadataVersion


class MetadataVersionResponse(BaseModel):
    id: str
    name: str


class SystemSettingsResponse(BaseModel):
    keyRemoteMetadataVersion: str

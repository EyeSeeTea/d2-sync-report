from pydantic import BaseModel
from d2_sync_report.data import dhis2_api
from d2_sync_report.domain.entities.instance import Instance
from d2_sync_report.domain.entities.metadata_versioning import MetadataVersioning
from d2_sync_report.domain.repositories.metadata_versioning_repository import (
    MetadataVersioningRepository,
)


class MetadataVersioningD2Repository(MetadataVersioningRepository):
    def get(self, instance: Instance) -> MetadataVersioning:
        local_version = self.get_local_metadata_version(instance)
        remote_version = self.get_remote_metadata_version(instance)
        return MetadataVersioning(local=local_version, remote=remote_version)

    def get_local_metadata_version(self, instance: Instance) -> str:
        res = dhis2_api.request(instance, "GET", "/api/metadata/version", MetadataVersionResponse)
        return res.name

    def get_remote_metadata_version(self, instance: Instance) -> str:
        res = dhis2_api.request(instance, "GET", "/api/systemSettings", SystemSettingsResponse)
        return res.keyRemoteMetadataVersion


class MetadataVersionResponse(BaseModel):
    id: str
    name: str


class SystemSettingsResponse(BaseModel):
    keyRemoteMetadataVersion: str

from abc import ABC, abstractmethod

from d2_sync_report.domain.entities.metadata_versioning import MetadataVersioning


class MetadataVersioningRepository(ABC):
    @abstractmethod
    def get(self) -> MetadataVersioning:
        pass

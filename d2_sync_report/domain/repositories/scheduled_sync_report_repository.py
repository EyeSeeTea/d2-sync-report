from abc import ABC, abstractmethod
from d2_sync_report.domain.entities.scheduled_sync_report import (
    ScheduledSyncReport,
)


class ScheduledSyncReportRepository(ABC):
    @abstractmethod
    def get_logs(self) -> ScheduledSyncReport:
        pass

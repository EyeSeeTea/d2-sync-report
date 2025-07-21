from dataclasses import dataclass
from typing import Literal, List
from datetime import datetime


ReportType = Literal["eventProgramsData", "trackerProgramsData", "metadata"]


@dataclass
class SyncJobReportItem:
    type: ReportType
    success: bool
    start: datetime
    end: datetime
    errors: List[str]


@dataclass
class SyncJobReport:
    items: List[SyncJobReportItem]
    last_processed: datetime

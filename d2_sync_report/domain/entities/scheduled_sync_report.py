from dataclasses import dataclass
from typing import Literal, List
from datetime import datetime


ReportType = Literal["eventProgramsData", "trackerProgramsData", "metadata"]


@dataclass
class ScheduledSyncReportItem:
    type: ReportType
    success: bool
    start: datetime
    end: datetime
    errors: List[str]


@dataclass
class ScheduledSyncReport:
    items: List[ScheduledSyncReportItem]

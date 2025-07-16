from dataclasses import dataclass
from typing import Literal, List
from datetime import datetime


@dataclass
class ScheduledSyncReportItem:
    type: Literal["eventProgramsData", "trackerProgramsData", "metadata"]
    success: bool
    start: datetime
    end: datetime
    errors: List[str]


@dataclass
class ScheduledSyncReport:
    items: List[ScheduledSyncReportItem]

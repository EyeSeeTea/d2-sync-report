from dataclasses import dataclass
from enum import Enum
from typing import List
from datetime import datetime


class SyncJobType(str, Enum):
    AGGREGATED = "aggregatedData"
    EVENT_PROGRAMS = "eventProgramsData"
    TRACKER_PROGRAMS = "trackerProgramsData"
    METADATA = "metadata"


@dataclass
class SyncJobReportItem:
    type: SyncJobType
    success: bool
    start: datetime
    end: datetime
    errors: List[str]


@dataclass
class SyncJobReport:
    items: List[SyncJobReportItem]
    last_processed: datetime

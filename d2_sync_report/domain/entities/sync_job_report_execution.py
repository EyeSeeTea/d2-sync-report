from dataclasses import dataclass
from datetime import datetime


@dataclass
class SyncJobReportExecution:
    last_processed: datetime
    last_sync: datetime

from dataclasses import dataclass, replace
from datetime import datetime
from typing import List, Optional, Union

from d2_sync_report.domain.entities.sync_job_report import SyncJobReportItem, SyncJobType


@dataclass
class LogEntry:
    timestamp: Optional[datetime]
    text: str


@dataclass
class SyncJobParserInProgress:
    type: SyncJobType
    start: datetime
    errors: List[str]


@dataclass
class SyncJobParserState:
    current: Union[SyncJobParserInProgress, None]
    parsed_jobs: List[SyncJobReportItem]
    last_processed_timestamp: Optional[datetime]

    @staticmethod
    def initial() -> "SyncJobParserState":
        return SyncJobParserState(current=None, parsed_jobs=[], last_processed_timestamp=None)

    def add_errors(self, errors: List[str]) -> "SyncJobParserState":
        if not self.current:
            return self
        else:
            return replace(self, current=replace(self.current, errors=self.current.errors + errors))

    def append_to_last_error(self, error: str) -> "SyncJobParserState":
        """
        Append a text to the last error in the current job's errors list, using separator " - "
        """
        if not self.current or not self.current.errors:
            return self
        else:
            last_error = self.current.errors[-1]
            print(f"Appending to last error: '{last_error}' with '{error}'")
            updated_errors = self.current.errors[:-1] + [last_error + " - " + error]
            return replace(self, current=replace(self.current, errors=updated_errors))

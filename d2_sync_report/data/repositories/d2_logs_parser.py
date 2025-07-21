import os
from datetime import datetime
from functools import reduce
from typing import Callable, Iterator, List, Optional, Tuple
from d2_sync_report.data.repositories.d2_job_reducers import D2JobReducers
from d2_sync_report.data.repositories.job_reducer_types import LogEntry, SyncJobParserState
from d2_sync_report.domain.entities.sync_job_report import SyncJobReport, SyncJobReportItem

"""
This class parses the DHIS2 logs to extract synchronization job reports.

As we have a single log file that aggregates all the actions and job synchronizations
in the instance, we need to separate the job parsing. Some log lines can be discriminated,
using the section (e.g. "EVENT_PROGRAMS_DATA_SYNC", "TRACKER_PROGRAMS_DATA_SYNC", "META_DATA_SYNC"),
but others (like low-level error messages) are not tagged with any section. 

The repository uses a state machine approach to parse the logs, where it keeps track
of the current synchronization job and its state. It processes each log entry,
and based on the content of the log entry, it updates the state accordingly.
"""


class D2LogsParser:
    def __init__(self, logs_folder_path: str):
        self.logs_folder_path = logs_folder_path

    def get(self, since: Optional[datetime] = None) -> SyncJobReport:
        logs_file_path = os.path.join(self.logs_folder_path, "dhis.log")
        print(f"Reading logs from: {logs_file_path}")

        def get_log_entries() -> Iterator[LogEntry]:
            return self._get_log_entries(logs_file_path, since)

        (items, last_processed) = self._get_log_report_items(get_log_entries)

        return SyncJobReport(items=items, last_processed=last_processed or datetime.now())

    def _get_log_entries(
        self, logs_file_path: str, since: Optional[datetime] = None
    ) -> Iterator[LogEntry]:
        parse = False if since else True

        with open(logs_file_path, "r", encoding="utf-8") as file:
            for line0 in file:
                line = line0.strip()
                entry = self._get_log_entry(line)

                if not entry:
                    continue

                if not parse and entry.timestamp and since and entry.timestamp > since:
                    parse = True

                if parse:
                    yield entry

    def _get_log_report_items(
        self, get_log_entries: Callable[[], Iterator[LogEntry]]
    ) -> Tuple[List[SyncJobReportItem], Optional[datetime]]:
        initial_state = SyncJobParserState.initial()
        reducers = D2JobReducers()

        def apply_reducer(
            reducer: Callable[[SyncJobParserState, LogEntry], SyncJobParserState],
        ) -> SyncJobParserState:
            return reduce(reducer, get_log_entries(), initial_state)

        # Syncs can run in parallel, so we need to apply reducers separately and aggregate results.
        state1 = apply_reducer(reducers.event_programs_reducer)
        state2 = apply_reducer(reducers.tracker_programs_reducer)
        state3 = apply_reducer(reducers.metadata_sync_reducer)

        parsed_jobs = state1.parsed_jobs + state2.parsed_jobs + state3.parsed_jobs
        return (parsed_jobs, state1.last_processed_timestamp)

    def _get_log_entry(self, line: str) -> Optional[LogEntry]:
        # "* INFO 2025-07-16T09:04:50,123 Some message"
        if not line.startswith("*"):
            return LogEntry(timestamp=None, text=line)
        else:
            parts = line.split()
            if len(parts) < 4:
                error(f"Cannot parse: {line}")
                return LogEntry(timestamp=None, text=line)

            timestamp_str = parts[2]
            try:
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S,%f")
            except ValueError:
                error(f"Invalid timestamp: {line}")
                return LogEntry(timestamp=None, text=line)

            return LogEntry(timestamp=timestamp, text=" ".join(parts[3:]))


def error(message: str) -> None:
    print(f"Error: {message}")

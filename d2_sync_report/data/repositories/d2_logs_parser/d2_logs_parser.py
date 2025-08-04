import os
import re
from dataclasses import dataclass, replace
from datetime import datetime
from functools import reduce
from typing import Iterator, List, Optional, Tuple

from d2_sync_report.data.dhis2_api import D2Api
from d2_sync_report.data.repositories.d2_logs_parser.d2_job_reducers import D2JobReducers
from d2_sync_report.data.repositories.d2_logs_parser.job_reducer_types import (
    LogEntry,
    SyncJobParserState,
)
from d2_sync_report.data.repositories.d2_logs_suggestions import (
    D2LogsSuggestions,
)
from d2_sync_report.domain.entities.sync_job_report import SyncJobReport, SyncJobReportItem
from d2_sync_report.utils.uniq import uniq

"""
This class parses the DHIS2 logs to extract synchronization job reports.

As we have a single log file that aggregates any action in the instance, we'd like the ability to 
isolate which sync job they belong to. Some log lines can indeed be fully discriminated,
using the section (e.g. "EVENT_PROGRAMS_DATA_SYNC"), but others (like low-level error messages)
are not tagged.

The repository uses a state machine approach to parse the logs, where it keeps track
of the current synchronization job and its state.
"""


class D2LogsParser:
    api: D2Api

    def __init__(self, api: D2Api, logs_folder_path: str):
        self.api = api
        self.logs_folder_path = logs_folder_path
        self.d2_logs_suggestions = D2LogsSuggestions(self.api)

    def get(self, since: Optional[datetime] = None) -> SyncJobReport:
        log_files = self._get_log_files()
        print(f"Reading logs from: {", ".join(log_files)}")

        def get_log_entries() -> Iterator[LogEntry]:
            for log_file in log_files:
                yield from self._get_log_entries(log_file, since)

        (items, last_processed) = self._get_log_report_items(get_log_entries())

        self.d2_logs_suggestions.copy_resources()

        return SyncJobReport(
            items=self._add_suggestions(items),
            last_processed=last_processed or datetime.now(),
        )

    def _add_suggestions(self, items: List[SyncJobReportItem]) -> List[SyncJobReportItem]:
        items_with_suggestions: List[SyncJobReportItem] = []

        for item in items:
            suggestions = [
                suggestion
                for error in item.errors
                for suggestion in self.d2_logs_suggestions.get_suggestions_from_error(error)
            ]

            item2 = replace(item, suggestions=uniq(suggestions))
            items_with_suggestions.append(item2)

        return items_with_suggestions

    def _get_log_files(self) -> list[str]:
        rotated_log_files = [
            filename
            for filename in os.listdir(self.logs_folder_path)
            if re.match(r"dhis\.log\.\d+$", filename)
        ]

        all_log_files = sorted(
            rotated_log_files,
            key=lambda filename: int(filename[len("dhis.log.") :]),
        ) + ["dhis.log"]

        return [os.path.join(self.logs_folder_path, log_file) for log_file in all_log_files]

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
        self, log_entries: Iterator[LogEntry]
    ) -> Tuple[List[SyncJobReportItem], Optional[datetime]]:
        initial_state = SyncJobParserState.initial()

        # Sync jobs can run in parallel, so reduce parsers isolatedly and aggregate results at the end.

        initial_compositite_state = ReducersState(
            initial_state, initial_state, initial_state, initial_state
        )

        state = reduce(ReducersState.reducer, log_entries, initial_compositite_state)

        parsed_jobs = (
            state.data_sync_state.parsed_jobs
            + state.event_programs_state.parsed_jobs
            + state.tracker_programs_state.parsed_jobs
            + state.metadata_sync_state.parsed_jobs
        )

        return (parsed_jobs, state.data_sync_state.last_processed_timestamp)

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


reducers = D2JobReducers()


@dataclass
class ReducersState:
    data_sync_state: SyncJobParserState
    event_programs_state: SyncJobParserState
    tracker_programs_state: SyncJobParserState
    metadata_sync_state: SyncJobParserState

    @staticmethod
    def reducer(state: "ReducersState", log_entry: LogEntry) -> "ReducersState":
        state1 = reducers.data_sync_reducer(state.data_sync_state, log_entry)
        state2 = reducers.event_programs_reducer(state.event_programs_state, log_entry)
        state3 = reducers.tracker_programs_reducer(state.tracker_programs_state, log_entry)
        state4 = reducers.metadata_sync_reducer(state.metadata_sync_state, log_entry)
        return ReducersState(state1, state2, state3, state4)


def error(message: str) -> None:
    print(f"Error: {message}")

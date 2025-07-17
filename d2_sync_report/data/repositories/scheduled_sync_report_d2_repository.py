from __future__ import annotations
import itertools
import os
import re
from typing import Iterator, List, Literal, Optional, Set, Tuple, TypeVar, Union
from datetime import datetime
from dataclasses import dataclass, replace
from functools import reduce
from pydantic import BaseModel

from d2_sync_report.domain.entities.scheduled_sync_report import (
    ReportType,
    ScheduledSyncReport,
    ScheduledSyncReportItem,
)
from d2_sync_report.domain.repositories.scheduled_sync_report_repository import (
    ScheduledSyncReportRepository,
)


@dataclass
class LogEntry:
    timestamp: datetime
    text: str


SyncJobType = Literal["eventProgramsData", "trackerProgramsData", "metadata"]


@dataclass
class InProgress:
    type: SyncJobType
    start: datetime
    errors: List[str]


@dataclass
class State:
    current: Union[InProgress, None]
    parsed_jobs: List[ScheduledSyncReportItem]
    last_processed_timestamp: Optional[datetime]

    @staticmethod
    def initial() -> State:
        return State(current=None, parsed_jobs=[], last_processed_timestamp=None)

    def add_errors(self, errors: List[str]) -> State:
        if not self.current:
            return self

        return replace(
            self, current=replace(self.current, errors=self.current.errors + errors)
        )


class ScheduledSyncReportD2Repository(ScheduledSyncReportRepository):
    def __init__(self, logs_folder_path: str, ignore_cache: bool):
        self.logs_folder_path = logs_folder_path
        self.ignore_cache = ignore_cache

    def get_logs(self) -> ScheduledSyncReport:
        logs_file_path = os.path.join(self.logs_folder_path, "dhis.log")
        cache = Cache()
        now = datetime.now()

        print(f"Reading logs from: {logs_file_path}")
        with open(logs_file_path, "r", encoding="utf-8") as file:
            lines = (line.rstrip() for line in file)

            all_log_entries = (
                log_entry
                for line in lines
                if (log_entry := self._get_log_entry(line)) is not None
            )

            cache_value = cache.load() if not self.ignore_cache else None

            if cache_value and cache_value.last_processed:
                print(f"Parse logs since: {cache_value.last_processed}")

            log_entries = itertools.dropwhile(
                lambda log_entry: cache_value
                and log_entry.timestamp <= cache_value.last_processed,
                all_log_entries,
            )

            (items, last_processed) = self.get_log_report_items(log_entries)
            if last_processed:
                cache.save(CacheProps(last_processed=last_processed, last_sync=now))

            return ScheduledSyncReport(items=items)

    def get_log_report_items(
        self, log_entries: Iterator[LogEntry]
    ) -> Tuple[List[ScheduledSyncReportItem], Optional[datetime]]:
        def composed_reducer(state: State, entry: LogEntry):
            state2 = self._event_programs_reducer(state, entry)
            state3 = self._tracker_programs_reducer(state2, entry)
            return state3

        final_state = reduce(composed_reducer, log_entries, State.initial())
        return (final_state.parsed_jobs, final_state.last_processed_timestamp)

    def _event_programs_reducer(self, state: State, log_entry: LogEntry) -> State:
        matcher = LogEntryReducer(state, log_entry)

        if matcher.matches("Starting Event programs data synchronization"):
            return matcher.set_start_sync_job(type="eventProgramsData")
        elif not state.current or state.current.type != "eventProgramsData":
            return state
        elif matcher.matches("Event programs data synchronization failed"):
            return matcher.close_sync_job(success=False)
        elif matcher.matches("Event programs data synchronization skipped"):
            return matcher.close_sync_job(success=True)
        elif matcher.matches("Event programs data sync was successfully done"):
            return matcher.close_sync_job(success=True)
        elif state.current and state.current.type == "eventProgramsData":
            return matcher.parse_import_summaries()
        else:
            return state

    def _tracker_programs_reducer(self, state: State, log_entry: LogEntry) -> State:
        matcher = LogEntryReducer(state, log_entry)

        if matcher.matches("Starting Tracker programs data synchronization"):
            return matcher.set_start_sync_job(type="trackerProgramsData")
        elif not state.current or state.current.type != "trackerProgramsData":
            return state
        elif matcher.matches("Tracker programs data synchronization failed"):
            return matcher.close_sync_job(success=False)
        elif matcher.matches("Tracker programs data synchronization skipped"):
            return matcher.close_sync_job(success=True)
        elif matcher.matches(
            "Tracker programs data synchronization was successfully done"
        ):
            return matcher.close_sync_job(success=True)
        elif state.current and state.current.type == "trackerProgramsData":
            return matcher.parse_import_summaries()
        else:
            return state

    def _get_log_entry(self, line: str) -> Optional[LogEntry]:
        # "* INFO 2025-07-16T09:04:50,123 Some message"
        if not line.startswith("*"):
            return None
        parts = line.split()
        if len(parts) < 4:
            error(f"Cannot parse: {line}")
            return None

        timestamp_str = parts[2]
        try:
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S,%f")
        except ValueError:
            error(f"Invalid timestamp: {line}")
            return None

        return LogEntry(timestamp=timestamp, text=" ".join(parts[3:]))


def error(message: str) -> None:
    print(f"Error: {message}")


def now() -> datetime:
    """Returns the current datetime."""
    return datetime.now()  # For testing purposes, you might want to mock this in tests.


# ImportSummary{
#     status=ERROR,
#     description='Program is not assigned to this Organisation Unit: WA5iEXjqCnS',
#     importCount=[imports=0, updates=0, ignores=1],
#     conflicts={},
#     dataSetComplete='null',
#     reference='ZOkh9BeNXYF',
#     href='null'
# },


@dataclass
class ImportSummary:
    status: Optional[str] = None
    description: Optional[str] = None
    import_count: Optional[str] = None
    reference: Optional[str] = None
    conflicts: Optional[str] = None

    def format_summary(self) -> str:
        summary = self

        message_parts: List[str] = (
            [summary.description]
            if summary.status != "SUCCESS"
            and summary.description
            and summary.description != "null"
            else []
        ) + ([summary.conflicts] if summary.conflicts else [])

        message = " ".join(message_parts)

        return " ".join(
            [
                f'status="{summary.status}"',
                f'object_id="{summary.reference}"',
                f'message="{message}"',
            ]
        )


def parse_import_summaries(line: str) -> List[ImportSummary]:
    summary_blocks: List[str] = re.findall(r"ImportSummary\{(.*?)'\}", line)
    summaries: List[ImportSummary] = []

    for block in summary_blocks:
        status_match = re.search(r"status=(\w+)", block)
        description_match = re.search(r"description='(.*?)'", block)
        import_count_match = re.search(r"importCount=\[(.*?)\]", block)
        reference_match = re.search(r"reference='(.*?)'", block)
        conflicts_match = re.search(r"conflicts=\{(.*?)\},", block, re.DOTALL)

        summary = ImportSummary(
            status=status_match.group(1) if status_match else None,
            description=description_match.group(1) if description_match else None,
            import_count=import_count_match.group(1) if import_count_match else None,
            reference=reference_match.group(1) if reference_match else None,
            conflicts=conflicts_match.group(1).strip() if conflicts_match else None,
        )

        summaries.append(summary)

    return summaries


T = TypeVar("T")


def uniq(xs: List[T]) -> List[T]:
    seen: Set[T] = set()
    return [x for x in xs if not (x in seen or seen.add(x))]


## Cache


class CacheProps(BaseModel):
    last_processed: datetime
    last_sync: datetime


class Cache:
    def save(self, props: CacheProps) -> None:
        cache_path = self._get_cache_path()

        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(props.model_dump_json(indent=4) + "\n")
        print(f"Cache saved: {cache_path}")

    def load(self) -> Optional[CacheProps]:
        cache_path = self._get_cache_path()

        if os.path.exists(cache_path):
            print(f"Cache loaded: {cache_path}")

            try:
                cache_props = CacheProps.model_validate_json(
                    open(cache_path, "r", encoding="utf-8").read()
                )
                print(f"Cache: {cache_props}")
                return cache_props
            except ValueError as exc:
                print(f"Cache load error: {exc}")
                # File is corrupted, remove it
                os.remove(cache_path)
                return None

        else:
            print(f"Cache file does not exist: {cache_path}")
            return None

    def _get_cache_path(self) -> str:
        script_folder = os.path.dirname(os.path.dirname(__file__))
        return os.path.join(script_folder, "cache.json")


class LogEntryReducer:
    def __init__(self, state: State, log_entry: LogEntry):
        self.state = state
        self.log_entry = log_entry

    def matches(self, pattern: str) -> bool:
        return pattern in self.log_entry.text

    def close_sync_job(self, success: bool) -> State:
        state = self.state
        log_entry = self.log_entry

        if not state.current:
            return state

        parsed = ScheduledSyncReportItem(
            type=state.current.type,
            success=success and not state.current.errors,
            errors=uniq(state.current.errors),
            start=state.current.start,
            end=log_entry.timestamp or state.current.start,
        )

        return State(
            current=None,
            parsed_jobs=state.parsed_jobs + [parsed],
            last_processed_timestamp=log_entry.timestamp,
        )

    def set_start_sync_job(self, type: ReportType) -> State:
        state = self.state
        log_entry = self.log_entry

        return State(
            current=InProgress(type=type, start=log_entry.timestamp, errors=[]),
            parsed_jobs=state.parsed_jobs,
            last_processed_timestamp=None,
        )

    def parse_import_summaries(self):
        state = self.state
        log_entry = self.log_entry
        summaries = parse_import_summaries(log_entry.text)

        errors = [
            summary.format_summary()
            for summary in summaries
            if summary.status == "ERROR" or summary.conflicts
        ]

        return state.add_errors(errors)

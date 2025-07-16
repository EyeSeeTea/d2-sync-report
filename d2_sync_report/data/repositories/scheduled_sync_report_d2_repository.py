from itertools import dropwhile
import os
import re
from typing import Iterator, List, Literal, Optional, Set, TypeVar, Union
from datetime import datetime
from dataclasses import dataclass, replace
from functools import reduce
from pydantic import BaseModel

from d2_sync_report.domain.entities.scheduled_sync_report import (
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


class ScheduledSyncReportD2Repository(ScheduledSyncReportRepository):
    def __init__(self, logs_folder_path: str):
        self.logs_folder_path = logs_folder_path

    def get_logs(self) -> ScheduledSyncReport:
        logs_file_path = os.path.join(self.logs_folder_path, "dhis.log")
        cache = Cache().load()

        with open(logs_file_path, "r", encoding="utf-8") as f:
            lines = (line.rstrip() for line in f)

            all_log_entries: Iterator[LogEntry] = (
                entry for line in lines if (entry := self._parse_line(line)) is not None
            )

            log_entries = dropwhile(
                lambda entry: cache and entry.timestamp < cache.last_processed,
                all_log_entries,
            )
            items = self._parse(log_entries)

            return ScheduledSyncReport(items=items)

    def _parse(self, log_entries: Iterator[LogEntry]) -> List[ScheduledSyncReportItem]:
        initial_state = State(current=None, parsed_jobs=[])

        def reducer(state: State, log_entry: LogEntry) -> State:
            if not log_entry:
                return state

            def matches(pattern: str) -> bool:
                return pattern in log_entry.text

            def close_event_programs_data_sync(success: bool) -> State:
                if not state.current:
                    return state

                parsed = ScheduledSyncReportItem(
                    type=state.current.type,
                    success=success and not state.current.errors,
                    errors=uniq(state.current.errors),
                    start=state.current.start,
                    end=log_entry.timestamp or state.current.start,
                )

                return State(current=None, parsed_jobs=state.parsed_jobs + [parsed])

            if matches("Process started: Starting Event programs data synchronization"):
                return State(
                    current=InProgress(
                        type="eventProgramsData", start=log_entry.timestamp, errors=[]
                    ),
                    parsed_jobs=state.parsed_jobs,
                )

            elif matches("Event programs data synchronization failed"):
                return close_event_programs_data_sync(success=False)

            elif matches("Event programs data synchronization skipped") or matches(
                "Event programs data sync was successfully done"
            ):
                return close_event_programs_data_sync(success=True)

            else:
                summaries = parse_import_summaries(log_entry.text)
                errors = [
                    summary.format_summary()
                    for summary in summaries
                    if summary.status == "ERROR" or summary.conflicts
                ]

                if not state.current:
                    return state

                return replace(
                    state,
                    current=replace(
                        state.current, errors=state.current.errors + errors
                    ),
                )

        return reduce(reducer, log_entries, initial_state).parsed_jobs

    def _parse_line(self, line: str) -> Optional[LogEntry]:
        if not line.startswith("*"):
            return None
        parts = line.split()
        if len(parts) < 4:
            error(f"Cannot parse: {line}")
            return None

        timestamp_str = parts[2].split(",")[0]
        timestamp: Optional[datetime] = None
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
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
            f.write(props.model_dump_json(indent=2))
        print(f"Cache saved: {cache_path}")

    def load(self) -> Optional[CacheProps]:
        cache_path = self._get_cache_path()

        if os.path.exists(cache_path):
            print(f"Cache loaded: {cache_path}")

            try:
                return CacheProps.model_validate_json(
                    open(cache_path, "r", encoding="utf-8").read()
                )
            except ValueError as exc:
                print(f"Cache load error: {exc}")
                # File is corrupted, remove it
                os.remove(cache_path)
                return None

        else:
            return None

    def _get_cache_path(self) -> str:
        script_folder = os.path.dirname(os.path.dirname(__file__))
        return os.path.join(script_folder, "cache.json")

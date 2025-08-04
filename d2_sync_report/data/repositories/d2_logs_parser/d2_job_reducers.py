from dataclasses import dataclass
from typing import List
from d2_sync_report.data.repositories.d2_logs_parser.import_summaries import parse_import_summaries
from d2_sync_report.data.repositories.d2_logs_parser.job_reducer_types import (
    SyncJobParserInProgress,
    LogEntry,
    SyncJobParserState,
)
from d2_sync_report.domain.entities.sync_job_report import SyncJobReportItem, SyncJobType
from d2_sync_report.utils.uniq import uniq


@dataclass
class Delimiters:
    """
    Patters that identify the start and end (success or error) of sync jobs.
    To be used in the generic sync reducer.
    """

    open: List[str]
    close_success: List[str]
    close_error: List[str]


class D2JobReducers:
    def data_sync_reducer(
        self, state: SyncJobParserState, log_entry: LogEntry
    ) -> SyncJobParserState:
        matcher = LogEntryReducer(state, log_entry, section="DATA_SYNC")

        delimiters = Delimiters(
            open=["Starting DataValueSynchronization job"],
            close_success=["Process completed after"],
            close_error=["DataValueSynchronization failed"],
        )

        return self._generic_sync_reducer(state, matcher, SyncJobType.AGGREGATED, delimiters)

    def event_programs_reducer(
        self, state: SyncJobParserState, log_entry: LogEntry
    ) -> SyncJobParserState:
        matcher = LogEntryReducer(state, log_entry, section="EVENT_PROGRAMS_DATA_SYNC")

        delimiters = Delimiters(
            open=["Starting Event programs data synchronization"],
            close_success=[
                "Event programs data sync was successfully done",
                "Event programs data synchronization skipped",
            ],
            close_error=["Event programs data synchronization failed"],
        )

        return self._generic_sync_reducer(state, matcher, SyncJobType.EVENT_PROGRAMS, delimiters)

    def tracker_programs_reducer(
        self, state: SyncJobParserState, log_entry: LogEntry
    ) -> SyncJobParserState:
        matcher = LogEntryReducer(state, log_entry, section="TRACKER_PROGRAMS_DATA_SYNC")

        delimiters = Delimiters(
            open=["Starting Tracker programs data synchronization"],
            close_success=[
                "Tracker programs data synchronization was successfully done",
                "Tracker programs data synchronization skipped",
            ],
            close_error=["Tracker programs data synchronization failed"],
        )
        return self._generic_sync_reducer(state, matcher, SyncJobType.TRACKER_PROGRAMS, delimiters)

    def metadata_sync_reducer(
        self, state: SyncJobParserState, log_entry: LogEntry
    ) -> SyncJobParserState:
        matcher = LogEntryReducer(state, log_entry, section="META_DATA_SYNC")

        delimiters = Delimiters(
            open=["Metadata Sync cron Job started"],
            close_success=["Metadata sync cron job ended"],
            close_error=[],
        )

        return self._generic_sync_reducer(
            state, matcher, SyncJobType.METADATA, delimiters, section=False
        )

    # Logs parsing is very similar for all syncs, just some tags and the start/close delimiters change.
    # So, to keep it DRY, let's create a generic reducer that can handle all sync jobs.
    def _generic_sync_reducer(
        self,
        state: SyncJobParserState,
        matcher: "LogEntryReducer",
        type: SyncJobType,
        delimiters: Delimiters,
        section: bool = True,
    ) -> SyncJobParserState:
        # Search for starter string (i.e: "Starting Tracker programs data synchronization job")
        if any(matcher.matches(open, section) for open in delimiters.open):
            return matcher.open_sync_job(type=type)
        elif not state.current or state.current.type != type:
            return state
        # Search for success closer string (i.e: "Tracker programs data synchronization skipped")
        elif any(matcher.matches(close, section) for close in delimiters.close_success):
            return matcher.close_sync_job(success=True)
        # Search for error closer string (i.e: "Tracker programs data synchronization failed")
        elif any(matcher.matches(close, section) for close in delimiters.close_error):
            return matcher.close_sync_job(success=False)
        # Refactor: no matches+parse -> parse1() or parse2() or ... -> add_error of that output
        elif matcher.matches_import_summaries():
            return matcher.parse_import_summaries()
        elif matcher.matches_caused_by():
            return matcher.add_error()
        elif matcher.matches_error_detail():
            return matcher.add_detail_error()
        else:
            return state


class LogEntryReducer:
    """
    Encapsulate the logic to process log entries and manage the state of sync jobs.

    Matches can include the section or not. Example for Metadata synchronization::

       * INFO  2025-07-21T11:47:28,307 [META_DATA_SYNC aBcD9Zo0xrG] Process started

    This way we can match against a specific job types.
    """

    def __init__(self, state: SyncJobParserState, log_entry: LogEntry, section: str):
        self.state = state
        self.log_entry = log_entry
        self.section = section

    def matches(self, pattern: str, section: bool = False) -> bool:
        line = self.log_entry.text.lower()
        section_matches = ("[" + self.section.lower() + " ") in line if section else True
        pattern_matches = pattern.lower() in line
        return section_matches and pattern_matches

    def close_sync_job(self, success: bool) -> SyncJobParserState:
        state = self.state
        log_entry = self.log_entry

        if not state.current:
            return state

        errors = uniq(state.current.errors)

        parsed = SyncJobReportItem(
            type=state.current.type,
            success=success and not state.current.errors,
            start=state.current.start,
            end=log_entry.timestamp or state.current.start,
            errors=errors,
            suggestions=[],
        )

        return SyncJobParserState(
            current=None,
            parsed_jobs=state.parsed_jobs + [parsed],
            last_processed_timestamp=log_entry.timestamp,
        )

    def open_sync_job(self, type: SyncJobType) -> SyncJobParserState:
        state = self.state
        log_entry = self.log_entry

        if not log_entry.timestamp:
            print("Log entry does not have a timestamp, cannot set start of sync job.")
            return state

        return SyncJobParserState(
            current=SyncJobParserInProgress(type=type, start=log_entry.timestamp, errors=[]),
            parsed_jobs=state.parsed_jobs,
            last_processed_timestamp=None,
        )

    def matches_import_summaries(self):
        return "ImportSummary{" in self.log_entry.text

    def matches_caused_by(self):
        return "Caused by:" in self.log_entry.text

    def matches_error_detail(self):
        return "Detail: " in self.log_entry.text

    def add_detail_error(self) -> SyncJobParserState:
        """
        If the log entry starts with "Detail: ", it usually follows a "Caused by" error message.
        Let's concatenate it to the previous error message if that's the case.
        """
        text = self.log_entry.text
        errors = self.state.current.errors if self.state.current else None

        if text.startswith("Detail: ") and errors and "Caused by" in errors[-1]:
            return self.state.append_to_last_error(text)
        else:
            return self.state

    def parse_import_summaries(self) -> SyncJobParserState:
        state = self.state
        log_entry = self.log_entry
        summaries = parse_import_summaries(log_entry.text)

        errors = [
            summary.format_summary()
            for summary in summaries
            if summary.status == "ERROR" or summary.conflicts
        ]

        return state.add_errors(errors)

    def add_error(self):
        return self.state.add_errors([self.log_entry.text])

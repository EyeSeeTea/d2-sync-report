from d2_sync_report.data.repositories.d2_logs_parser.import_summaries import parse_import_summaries
from d2_sync_report.data.repositories.d2_logs_parser.job_reducer_types import (
    SyncJobParserInProgress,
    LogEntry,
    SyncJobParserState,
)
from d2_sync_report.domain.entities.sync_job_report import SyncJobReportItem, SyncJobType
from d2_sync_report.utils.uniq import uniq


class D2JobReducers:
    def data_sync_reducer(
        self, state: SyncJobParserState, log_entry: LogEntry
    ) -> SyncJobParserState:
        matcher = LogEntryReducer(state, log_entry, section="DATA_SYNC")
        type = SyncJobType.AGGREGATED

        if matcher.matches("Starting DataValueSynchronization job", section=True):
            return matcher.open_sync_job(type=type)
        elif not state.current or state.current.type != type:
            return state
        elif matcher.matches("DataValueSynchronization failed", section=True):
            return matcher.close_sync_job(success=False)
        elif matcher.matches("Process completed after", section=True):
            return matcher.close_sync_job(success=True)
        elif matcher.matches_import_summaries():
            return matcher.parse_import_summaries()
        elif matcher.matches_caused_by():
            return matcher.add_error(log_entry)
        elif matcher.matches_error_detail():
            return matcher.add_error(log_entry)
        else:
            return state

    def event_programs_reducer(
        self, state: SyncJobParserState, log_entry: LogEntry
    ) -> SyncJobParserState:
        matcher = LogEntryReducer(state, log_entry, section="EVENT_PROGRAMS_DATA_SYNC")
        type = SyncJobType.EVENT_PROGRAMS

        if matcher.matches("Starting Event programs data synchronization", section=True):
            return matcher.open_sync_job(type=type)
        elif not state.current or state.current.type != type:
            return state
        elif matcher.matches("Event programs data synchronization failed", section=True):
            return matcher.close_sync_job(success=False)
        elif matcher.matches("Event programs data synchronization skipped", section=True):
            return matcher.close_sync_job(success=True)
        elif matcher.matches("Event programs data sync was successfully done", section=True):
            return matcher.close_sync_job(success=True)
        elif matcher.matches_import_summaries():
            return matcher.parse_import_summaries()
        elif matcher.matches_caused_by():
            return matcher.add_error(log_entry)
        elif matcher.matches_error_detail():
            return matcher.add_error(log_entry)
        else:
            return state

    def tracker_programs_reducer(
        self, state: SyncJobParserState, log_entry: LogEntry
    ) -> SyncJobParserState:
        matcher = LogEntryReducer(state, log_entry, section="TRACKER_PROGRAMS_DATA_SYNC")
        type = SyncJobType.TRACKER_PROGRAMS

        if matcher.matches("Starting Tracker programs data synchronization", section=True):
            return matcher.open_sync_job(type=type)
        elif not state.current or state.current.type != type:
            return state
        elif matcher.matches("Tracker programs data synchronization failed", section=True):
            return matcher.close_sync_job(success=False)
        elif matcher.matches("Tracker programs data synchronization skipped", section=True):
            return matcher.close_sync_job(success=True)
        elif matcher.matches(
            "Tracker programs data synchronization was successfully done", section=True
        ):
            return matcher.close_sync_job(success=True)
        elif matcher.matches_import_summaries():
            return matcher.parse_import_summaries()
        elif matcher.matches_caused_by():
            return matcher.add_error(log_entry)
        elif matcher.matches_error_detail():
            return matcher.add_error(log_entry)
        else:
            return state

    def metadata_sync_reducer(
        self, state: SyncJobParserState, log_entry: LogEntry
    ) -> SyncJobParserState:
        matcher = LogEntryReducer(state, log_entry, section="META_DATA_SYNC")
        type = SyncJobType.METADATA

        if matcher.matches("Metadata Sync cron Job started", section=False):
            return matcher.open_sync_job(type=type)
        elif not state.current or state.current.type != type:
            return state
        elif matcher.matches("Metadata sync cron job ended", section=False):
            return matcher.close_sync_job(success=True)
        elif matcher.matches_import_summaries():
            return matcher.parse_import_summaries()
        elif matcher.matches_caused_by():
            return matcher.add_error(log_entry)
        elif matcher.matches_error_detail():
            return matcher.add_error(log_entry)
        else:
            return state


class LogEntryReducer:
    """
    Encapsulate the logic for processing log entries and managing the state of sync jobs.

    Matches can include the section or not. Example for Metadata synchronization::

       * INFO  2025-07-21T11:47:28,307 [META_DATA_SYNC aBcD9Zo0xrG] Process started

    This way we can match against a specific section.
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

    def add_error(self, entry: LogEntry):
        return self.state.add_errors([entry.text])

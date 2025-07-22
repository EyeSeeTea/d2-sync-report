from datetime import datetime
from typing import List, Optional

from d2_sync_report.domain.entities.message import Message
from d2_sync_report.domain.entities.sync_job_report import (
    SyncJobReport,
    SyncJobReportItem,
)
from d2_sync_report.domain.entities.sync_job_report_execution import SyncJobReportExecution
from d2_sync_report.domain.repositories.message_repository import MessageRepository
from d2_sync_report.domain.repositories.sync_job_report_execution_repository import (
    SyncJobReportExecutionRepository,
)
from d2_sync_report.domain.repositories.sync_job_report_repository import (
    SyncJobReportRepository,
)
from d2_sync_report.domain.repositories.user_repository import UserRepository


class SendSyncReportUseCase:
    message_subject = "DHIS2 Sync Job Report"

    def __init__(
        self,
        sync_job_report_execution_repository: SyncJobReportExecutionRepository,
        sync_job_report_repository: SyncJobReportRepository,
        user_repository: UserRepository,
        message_repository: MessageRepository,
    ):
        self.sync_job_report_execution_repository = sync_job_report_execution_repository
        self.sync_job_report = sync_job_report_repository
        self.user_repository: UserRepository = user_repository
        self.message_repository: MessageRepository = message_repository

    def execute(
        self,
        user_group_name_to_send: Optional[str],
        skip_cache: bool,
    ) -> SyncJobReport:
        now = datetime.now()
        user_emails = self.get_users_in_group(user_group_name_to_send)
        since, reports = self.get_reports(skip_cache)
        contents = self.get_message_contents(now, since, reports)

        if not user_emails:
            print("No message is sent. Contents:\n")
            print(contents)
        else:
            message = Message(subject=self.message_subject, text=contents, recipients=user_emails)
            response = self.message_repository.send(message)
            print(f"Send email response: {response}")

        self.save_cache(skip_cache, reports)
        return reports

    def get_message_contents(
        self, now: datetime, since: Optional[datetime], reports: SyncJobReport
    ) -> str:
        formatted_reports = "\n\n".join(self._format_report(report) for report in reports.items)

        if formatted_reports:
            return formatted_reports
        else:
            since_str = since.strftime("%Y-%m-%d %H:%M:%S") if since else "BEGINNING"
            return f"No sync jobs found ({since_str} -> {now.strftime('%Y-%m-%d %H:%M:%S')})."

    def get_reports(self, skip_cache: bool):
        since = self.get_since_datetime(skip_cache)
        print(f"Fetching reports since: {since or '-'}")
        reports = self.sync_job_report.get(since=since)
        return since, reports

    def get_users_in_group(self, user_group_to_send: Optional[str]) -> Optional[List[str]]:
        if not user_group_to_send:
            return None
        users = self.user_repository.get_list_by_group(name=user_group_to_send)
        user_emails = [user.email for user in users]
        print(f"Users in group '{user_group_to_send}': {user_emails or 'NONE'}")
        return user_emails

    def get_since_datetime(self, skip_cache: bool) -> Optional[datetime]:
        last = None if skip_cache else self.sync_job_report_execution_repository.get_last()
        return last.last_processed if last else None

    def save_cache(self, skip_cache: bool, reports: SyncJobReport) -> None:
        if not skip_cache:
            self.sync_job_report_execution_repository.save_last(
                SyncJobReportExecution(
                    last_processed=reports.last_processed,
                    last_sync=datetime.now(),
                )
            )

    def _format_report(self, report: SyncJobReportItem) -> str:
        indent = " " * 2

        parts: List[Optional[str]] = [
            f"Type: {report.type}",
            f"Status: {"SUCCESS" if report.success else "ERROR"}",
            f"Start: {format_datetime(report.start)}",
            f"End: {format_datetime(report.end)}",
        ]

        def add_index(msg: str, idx: int) -> str:
            return indent + f"[{idx + 1}/{len(report.errors)}] {msg}"

        errors = (
            f"Errors:\n{'\n'.join(add_index(error, idx) for (idx, error) in enumerate(report.errors))}"
            if report.errors
            else ""
        )

        return "\n".join(compact(parts)) + "\n" + errors


def compact(xs: list[str | None]) -> list[str]:
    """Remove None values from the list."""
    return [x for x in xs if x is not None]


def format_datetime(dt: datetime) -> str:
    """Format datetime to string in the format YYYY-MM-DD HH:MM:SS."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

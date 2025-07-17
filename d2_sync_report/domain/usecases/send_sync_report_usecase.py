from datetime import datetime
from typing import List, Optional

from d2_sync_report.domain.entities.message import Message
from d2_sync_report.domain.entities.scheduled_sync_report import (
    ScheduledSyncReport,
    ScheduledSyncReportItem,
)
from d2_sync_report.domain.repositories.message_repository import MessageRepository
from d2_sync_report.domain.repositories.scheduled_sync_report_repository import (
    ScheduledSyncReportRepository,
)
from d2_sync_report.domain.repositories.user_repository import UserRepository


class SendSyncReportUseCase:
    def __init__(
        self,
        scheduled_sync_report_repository: ScheduledSyncReportRepository,
        user_repository: UserRepository,
        message_repository: MessageRepository,
    ):
        self.scheduled_sync_report = scheduled_sync_report_repository
        self.user_repository: UserRepository = user_repository
        self.message_repository: MessageRepository = message_repository

    def execute(
        self,
        user_group_name_to_send: str,
        skip_message: bool,
    ) -> ScheduledSyncReport:
        users = self.user_repository.get_list_by_group(name=user_group_name_to_send)
        user_emails = [user.email for user in users]
        print(f"Users in group '{user_group_name_to_send}': {user_emails or 'NONE'}")

        reports = self.scheduled_sync_report.get_logs()
        contents = "\n\n".join(self._format_report(report) for report in reports.items)

        if not reports.items:
            print("No reports found. Skip sending message")
        elif skip_message:
            print("Flag --skip-message is set. Skip sending message. Contents:\n")
            print(contents)
        else:
            message = Message(
                subject="Scheduled Sync Report",
                text=contents,
                recipients=user_emails,
            )
            response = self.message_repository.send(message)
            print(f"Server response: {response}")

        return reports

    def _format_report(self, report: ScheduledSyncReportItem) -> str:
        indent = " " * 2

        parts: List[Optional[str]] = [
            f"Type: {report.type}",
            f"Status: {"SUCCESS" if report.success else "ERROR"}",
            f"Start: {format_datetime(report.start)}",
            f"End: {format_datetime(report.end)}",
            (
                f"Errors:\n{indent}{f"\n{indent}".join(report.errors)}"
                if report.errors
                else None
            ),
        ]

        return "\n".join(compact(parts))


def compact(xs: list[str | None]) -> list[str]:
    """Remove None values from the list."""
    return [x for x in xs if x is not None]


def format_datetime(dt: datetime) -> str:
    """Format datetime to string in the format YYYY-MM-DD HH:MM:SS."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

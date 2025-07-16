from dataclasses import dataclass
from tyro import cli
from d2_sync_report.domain.usecases.send_sync_report_usecase import (
    SendSyncReportUseCase,
)
from d2_sync_report.data.repositories.message_d2_repository import MessageD2Repository
from d2_sync_report.data.repositories.scheduled_sync_report_d2_repository import (
    ScheduledSyncReportD2Repository,
)


@dataclass
class Args:
    url: str
    auth: str
    logs_folder_path: str


def main() -> None:
    args = cli(Args)

    use_case = SendSyncReportUseCase(
        ScheduledSyncReportD2Repository(args.logs_folder_path),
        MessageD2Repository("http://localhost:8080"),
    )
    reports = use_case.execute()
    print(reports)


if __name__ == "__main__":
    main()

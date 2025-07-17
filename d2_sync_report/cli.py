import re
from dataclasses import dataclass, replace
import tyro

from d2_sync_report.data.repositories.user_d2_repository import UserD2Repository
from d2_sync_report.domain.entities.instance import Auth, Instance
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
    send_user_group: str
    logs_folder_path: str
    skip_message: bool = False
    ignore_cache: bool = False


def main() -> None:
    args = tyro.cli(Args)

    (username, password) = args.auth.split(":", 1)
    instance = Instance(url=args.url, auth=Auth(username, password))
    args_to_log = replace(
        args,
        auth=re.sub(r"[^:]", "*", args.auth),
    )
    print(args_to_log)

    SendSyncReportUseCase(
        ScheduledSyncReportD2Repository(args.logs_folder_path, args.ignore_cache),
        UserD2Repository(instance),
        MessageD2Repository(instance),
    ).execute(
        user_group_name_to_send=args.send_user_group,
        skip_message=args.skip_message,
    )


if __name__ == "__main__":
    main()

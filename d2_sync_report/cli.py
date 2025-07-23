import re
from dataclasses import dataclass, replace
from typing import Annotated, Optional
import tyro
from tyro.conf import arg

from d2_sync_report.data.repositories.metadata_versioning_d2_repository import (
    MetadataVersioningD2Repository,
)
from d2_sync_report.data.repositories.sync_job_report_execution_file_repository import (
    SyncJobReportExecutionFileRepository,
)
from d2_sync_report.data.repositories.user_d2_repository import UserD2Repository
from d2_sync_report.domain.entities.instance import (
    BasicAuth,
    Instance,
    PersonalTokenAccessAuth,
)
from d2_sync_report.domain.usecases.send_sync_report_usecase import (
    SendSyncReportUseCase,
)
from d2_sync_report.data.repositories.message_d2_repository import MessageD2Repository
from d2_sync_report.data.repositories.sync_job_report_d2_repository import (
    SyncJobReportD2Repository,
)


@dataclass
class Args:
    logs_folder_path: Annotated[
        str,
        arg(help="Folder containing file dhis.log", metavar="[DOCKER_CONTAINER:]FOLDER_PATH"),
    ]
    url: Annotated[str, arg(help="DHIS2 instance base URL", metavar="URL")]
    auth: Annotated[str, arg(help="USER:PASS or PAT token", metavar="AUTH")]
    ignore_cache: Annotated[bool, arg(help="Ignore cached state", default=False)] = False
    notify_user_group: Annotated[
        Optional[str], arg(help="User group to send report to", metavar="NAME or CODE")
    ] = None


def main() -> None:
    args = tyro.cli(Args)
    instance = get_instance(args)

    SendSyncReportUseCase(
        SyncJobReportExecutionFileRepository(),
        SyncJobReportD2Repository(instance, args.logs_folder_path),
        MetadataVersioningD2Repository(),
        UserD2Repository(instance),
        MessageD2Repository(instance),
    ).execute(
        user_group_name_to_send=args.notify_user_group,
        skip_cache=args.ignore_cache,
        instance=instance,
    )


def log_args(args: Args) -> None:
    obfuscated_auth = re.sub(r"[^:]", "*", args.auth) if args.auth else None
    args_to_log = replace(args, auth=obfuscated_auth)
    print(args_to_log)


def get_instance(args: Args) -> Instance:
    log_args(args)

    if args.auth.startswith("d2pat_"):
        return Instance(
            url=args.url,
            auth=PersonalTokenAccessAuth(token=args.auth),
        )
    elif ":" in args.auth:
        username, password = args.auth.split(":", 1)
        return Instance(
            url=args.url,
            auth=BasicAuth(type="basic", username=username, password=password),
        )
    else:
        raise ValueError("Invalid auth format")


if __name__ == "__main__":
    main()

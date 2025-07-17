import os
from datetime import datetime

from d2_sync_report.data.repositories.scheduled_sync_report_d2_repository import (
    ScheduledSyncReportD2Repository,
)


def test_event_programs_data_sync_success():
    repository = get_repo("event-programs-data-sync-success")
    reports = repository.get_logs().items

    assert len(reports) == 1
    report = reports[0]
    assert report.type == "eventProgramsData"
    assert report.success is True
    assert_datetime_equals(report.start, datetime(2025, 7, 16, 9, 4, 50))
    assert_datetime_equals(report.end, datetime(2025, 7, 16, 9, 4, 50))
    assert len(report.errors) == 0


def test_event_programs_data_sync_error():
    repository = get_repo("event-programs-data-sync-error")
    reports = repository.get_logs().items

    assert len(reports) == 1
    report = reports[0]
    assert report.type == "eventProgramsData"
    assert report.success is False
    assert len(report.errors) == 2

    assert_string_from_parts(
        report.errors[0],
        [
            'status="ERROR"',
            'object_id="ZOkh9BeNXYF"',
            'message="Program is not assigned to this Organisation Unit: WA5iEXjqCnS"',
        ],
    )

    assert_string_from_parts(
        report.errors[1],
        [
            'status="ERROR"',
            'object_id="zCziVRiuiHG"',
            "message=\"Deletion of event zCziVRiuiHG failed Attribute.value:Non-unique attribute value 'Ar011R' for attribute QPFgav8YHVb=ImportConflict{error:Attribute.value, message:Non-unique attribute value 'Ar011R' for attribute QPFgav8YHVb}\"",
        ],
    )


## Tracker programs


def test_tracker_programs_data_sync_success():
    repository = get_repo("tracker-programs-data-sync-success")
    reports = repository.get_logs().items

    assert len(reports) == 1
    report = reports[0]
    assert report.type == "trackerProgramsData"
    assert report.success is True
    assert len(report.errors) == 0


def test_tracker_programs_data_sync_error():
    repository = get_repo("tracker-programs-data-sync-error")
    reports = repository.get_logs().items

    assert len(reports) == 1
    report = reports[0]
    assert report.type == "trackerProgramsData"
    assert report.success is False
    assert len(report.errors) == 1

    assert_string_from_parts(
        report.errors[0],
        [
            'status="ERROR"',
            'object_id="ZOkh9BeNXYF"',
            'message="Program is not assigned to this Organisation Unit: WA5iEXjqCnS"',
        ],
    )


## Helpers


def assert_string_from_parts(actual: str, expected_parts: list[str]):
    expected = " ".join(expected_parts)
    assert actual == expected


def assert_datetime_equals(actual: datetime, expected: datetime):
    assert actual.replace(microsecond=0) == expected


def get_test_log_path(filename: str) -> str:
    return os.path.join(os.path.dirname(__file__), "logs", filename)


def get_repo(logs_folder_path: str):
    log_path = get_test_log_path(logs_folder_path)
    return ScheduledSyncReportD2Repository(logs_folder_path=log_path, ignore_cache=True)

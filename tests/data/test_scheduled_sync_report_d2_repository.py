import os
from datetime import datetime

from d2_sync_report.data.repositories.scheduled_sync_report_d2_repository import (
    ScheduledSyncReportD2Repository,
)


def get_test_log_path(filename: str) -> str:
    return os.path.join(os.path.dirname(__file__), "logs", filename)


def test_event_programs_data_sync_successful():
    log_path = get_test_log_path("event-programs-data-sync-successful")
    repo = ScheduledSyncReportD2Repository(logs_folder_path=log_path)
    reports = repo.get_logs().items

    assert len(reports) == 1
    report = reports[0]
    assert report.type == "eventProgramsData"
    assert report.success is True
    assert_datetime_equals(report.start, datetime(2025, 7, 16, 9, 4, 50))
    assert_datetime_equals(report.end, datetime(2025, 7, 16, 9, 4, 50))
    assert len(report.errors) == 0


def test_event_programs_data_sync_error():
    log_path = get_test_log_path("event-programs-data-sync-error")
    repo = ScheduledSyncReportD2Repository(logs_folder_path=log_path)
    reports = repo.get_logs().items

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


def assert_string_from_parts(actual: str, expected_parts: list[str]):
    expected = " ".join(expected_parts)
    assert actual == expected


def assert_datetime_equals(actual: datetime, expected: datetime):
    assert actual.replace(microsecond=0) == expected

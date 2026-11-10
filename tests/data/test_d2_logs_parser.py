import os
from datetime import datetime
from typing import Optional

from d2_sync_report.cli import get_default_suggestions_path
from d2_sync_report.data.repositories.d2_logs_parser.d2_logs_parser import D2LogsParser
from d2_sync_report.domain.entities.sync_job_report import SyncJobReportItem
from tests.data.d2_api_mock import D2ApiMock, Expectations
from tests.data.request_mocks import request_mocks

## Aggregated data synchronization


def test_aggregated_data_sync_success():
    repository = get_repo(folder="data-synchronization-success")
    reports = repository.get().items

    assert len(reports) == 1
    report = reports[0]
    assert report.type == "aggregatedData"
    assert report.success is True
    assert len(report.errors) == 0


## Event programs data


def test_event_programs_data_sync_success():
    repository = get_repo(folder="event-programs-data-sync-success")
    reports = repository.get().items

    assert len(reports) == 1
    report = reports[0]
    assert report.type == "eventProgramsData"
    assert report.success is True
    assert_datetime_equals(report.start, datetime(2025, 7, 16, 9, 4, 50))
    assert_datetime_equals(report.end, datetime(2025, 7, 16, 9, 4, 50))
    assert len(report.errors) == 0


def test_event_programs_data_sync_error():
    repository = get_repo(folder="event-programs-data-sync-error")
    reports = repository.get().items

    assert len(reports) == 1
    report = reports[0]
    assert report.type == "eventProgramsData"
    assert report.success is False
    assert len(report.errors) == 2


## Tracker programs data


def test_tracker_programs_data_sync_success():
    repository = get_repo(folder="tracker-programs-data-sync-success")
    reports = repository.get().items

    assert len(reports) == 1
    report = reports[0]
    assert report.type == "trackerProgramsData"
    assert report.success is True
    assert len(report.errors) == 0


## Metadata synchronization


def test_metadata_sync_success():
    repository = get_repo(folder="metadata-synchronization-success")
    reports = repository.get().items

    assert len(reports) == 1
    report = reports[0]
    assert report.type == "metadata"
    assert report.success is True
    assert len(report.errors) == 0


def test_metadata_sync_error():
    repository = get_repo(folder="metadata-synchronization-error")
    reports = repository.get().items

    assert len(reports) == 1
    report = reports[0]
    assert report.type == "metadata"
    assert report.success is False
    assert len(report.errors) == 2


def test_metadata_sync_failed():
    # DHIS2 does not log "Metadata sync cron job ended" when the job fails
    repository = get_repo(folder="metadata-synchronization-failed")
    reports = repository.get().items

    assert len(reports) == 1
    report = reports[0]
    assert report.type == "metadata"
    assert report.success is False
    assert_datetime_equals(report.start, datetime(2026, 10, 21, 11, 12, 15))
    assert_datetime_equals(report.end, datetime(2026, 10, 21, 11, 13, 44))
    assert report.errors == [
        "Exception occurred while trying to import the metadata. not-null property references"
        + " a null or transient value : org.hisp.dhis.security.apikey.ApiToken.key"
    ]
    assert len(report.suggestions) == 1
    assert report.suggestions[0].startswith("The metadata version includes an API token")


def test_metadata_sync_duplicate_username():
    repository = get_repo(folder="metadata-synchronization-duplicate-username")
    reports = repository.get().items

    assert len(reports) == 1
    report = reports[0]
    assert report.type == "metadata"
    assert report.success is False
    # The job progress failure ("Stage failed after: could not execute statement") repeats
    # the message of the exception already logged, so it's not added as another error
    assert report.errors == [
        "Caused by: org.hibernate.exception.ConstraintViolationException: could not execute"
        + " statement",
        "Caused by: org.postgresql.util.PSQLException: ERROR: duplicate key value violates unique"
        + ' constraint "uk_userinfo_username"'
        + " - Detail: Key (username)=(admin-test) already exists.",
    ]
    # Usernames can contain characters other than letters, digits, "_" and "."
    assert report.suggestions == [
        "User with username 'admin-test' already exists. Go to"
        + " https://mock-instance/dhis-web-user/index.html#/users?query=admin-test and delete it"
    ]


def test_metadata_sync_import_error():
    # ATOMIC version: the import fails with status ERROR and the sync is aborted
    repository = get_repo(folder="metadata-synchronization-import-error")
    reports = repository.get().items

    assert len(reports) == 1
    report = reports[0]
    assert report.type == "metadata"
    assert report.success is False
    assert report.errors == [
        'version="Version_19" error_code="E5002" message="Invalid reference [OI69n5Ig2Tw]'
        + ' (FileResource) on object John Traore [xE7jOejl9FI] (User) for association `avatar`"'
    ]
    assert report.warnings == []
    assert len(report.suggestions) == 1
    assert report.suggestions[0].startswith("User 'John Traore' [xE7jOejl9FI] has an avatar")


def test_metadata_sync_import_warning():
    # BEST_EFFORT version: the import succeeds with status WARNING, without the invalid reference
    repository = get_repo(folder="metadata-synchronization-import-warning")
    reports = repository.get().items

    assert len(reports) == 1
    report = reports[0]
    assert report.type == "metadata"
    assert report.success is True
    assert report.errors == []
    assert report.warnings == [
        'version="Version_18" error_code="E5002" message="Invalid reference [fwZo9etl31C]'
        + ' (FileResource) on object John Traore [xE7jOejl9FI] (User) for association `avatar`"'
    ]
    # Suggestions also apply to warnings
    assert len(report.suggestions) == 1
    assert report.suggestions[0].startswith("User 'John Traore' [xE7jOejl9FI] has an avatar")


## Test errors and suggestions


def test_error_program_not_assigned_to_organisation_unit():
    report = get_report_with_error_and_suggestions()

    assert_report_entry(
        report,
        error=[
            "Gq942x50jWX",
            "Program is not assigned to this Organisation Unit: WA5iEXjqCnS",
        ],
        suggestion=[
            "Maintenance App",
            "Mock Program",
            "Mock Organisation Unit",
            "/dhis-web-maintenance/index.html#/edit/programSection/program/Gq942x50jWX",
        ],
    )


def test_error_user_already_exists():
    report = get_report_with_error_and_suggestions()

    assert_report_entry(
        report,
        error=[
            "duplicate key value violates unique constraint",
            "Claude.KWITONDA",
        ],
        suggestion=[
            "User with username 'Claude.KWITONDA' already exists",
            "https://mock-instance/dhis-web-user/index.html#/users?query=Claude.KWITONDA",
            "delete it",
        ],
    )


def test_period_not_open_for_data_set():
    report = get_report_with_error_and_suggestions()

    assert_report_entry(
        report,
        error=[
            "Period: `2025W27` is not open for this data set at this time: `h3zkiErOoFl`",
        ],
        suggestion=[
            "Maintenance App",
            "Mock Data Set",
            "DATA INPUT PERIODS",
            "2025W27",
            "/dhis-web-maintenance/index.html#/edit/dataSetSection/dataSet/h3zkiErOoFl",
        ],
    )


def test_option_set_not_an_option_of_option_set():
    report = get_report_with_error_and_suggestions()

    assert_report_entry(
        report,
        error=[
            "HFxbAFNOYqb",
            "kenema_other_chiefdoms_outside_kenema_district_itf",
            "not a valid option code of option set",
            "CTZmCZx5nOk",
        ],
        suggestion=[
            "Maintenance App",
            "Mock Option Set",
            "kenema_other_chiefdoms_outside_kenema_district_itf",
            "/dhis-web-maintenance/index.html#/edit/otherSection/optionSet/CTZmCZx5nOk/options",
        ],
    )


def test_category_option_combo_not_accesible():
    report = get_report_with_error_and_suggestions()

    assert_report_entry(
        report,
        error=[
            "Category option combo not found or not accessible for writing data",
            "zUs1ja0c8zT",
        ],
        suggestion=[
            "Category option combo `CategoryOption1, CategoryOption2`",
            "zUs1ja0c8zT",
            "does not exist",
            "Sharing Settings",
            "/dhis-web-maintenance/index.html#/edit/categorySection/categoryOption",
            "Clear application cache",
        ],
    )


def test_cannot_update_remote_notes():
    report = get_report_with_error_and_suggestions()

    assert_report_entry(
        report,
        error=[
            'duplicate key value violates unique constraint "uk_t94h9p111tcydbm6je22tla52"',
            "Detail: Key (uid)=(NtwUZWYlhxt) already exists",
        ],
        suggestion=[
            "DHIS2-12887",
            "delete-tracker-note",
            "mock_container psql",
        ],
    )


def test_cannot_add_event_to_completed_enrollment():
    report = get_report_with_error_and_suggestions()

    assert_report_entry(
        report,
        error=[
            "Not possible to add event to a completed enrollment",
            "Bzyve9gtbyw",
        ],
        suggestion=[
            "Uncomplete this enrollment for event Bzyve9gtbyw",
            "/dhis-web-capture/index.html#/enrollment?enrollmentId=pfDcyZw9bs1&orgUnitId=RFe6Bei9Yek&programId=jPRLZ8MJ86L&teiId=uyRjwOSJa5k",
        ],
    )


def test_program_stage_not_repeatable():
    report = get_report_with_error_and_suggestions()

    assert_report_entry(
        report,
        error=[
            "Program stage is not repeatable",
            "an event already exists",
            "Bzyve9gtbyw",
        ],
        suggestion=[
            "/dhis-web-capture/index.html#/enrollmentEventEdit?eventId=Bzyve9gtbyw&orgUnitId=RFe6Bei9Yek",
        ],
    )


def test_no_row_with_given_identifier_exists():
    report = get_report_with_error_and_suggestions()

    assert_report_entry(
        report,
        error=[
            "No row with the given identifier exists",
            "org.hisp.dhis.category.CategoryOptionCombo#1698861",
        ],
        suggestion=[
            "may have different causes.",
            "restarting",
            "problem with the metadata",
        ],
    )


def test_event_could_not_be_deleted_due_to_non_unique_attribute_value():
    report = get_report_with_error_and_suggestions()

    assert_report_entry(
        report,
        error=[
            "Non-unique attribute value",
            "Ar011R",
        ],
        suggestion=[
            "/dhis-web-capture/index.html#/enrollment?enrollmentId=pfDcyZw9bs1&orgUnitId=RFe6Bei9Yek&programId=jPRLZ8MJ86L&teiId=uyRjwOSJa5k",
        ],
    )


## Helpers


def get_report_with_error_and_suggestions():
    """
    Get a report that contains all errors and suggestions.
    """
    repository = get_repo(folder="tracker-programs-data-sync-error")
    reports = repository.get().items

    assert len(reports) == 1
    return reports[0]


def assert_datetime_equals(actual: datetime, expected: datetime):
    assert actual.replace(microsecond=0) == expected


def get_log_folder(folder: str) -> str:
    return os.path.join(os.path.dirname(__file__), "logs", folder)


def test_tracker_programs_data_sync_error():
    repository = get_repo(folder="tracker-programs-data-sync-error")
    reports = repository.get().items

    assert len(reports) == 1
    report = reports[0]
    assert report.type == "trackerProgramsData"
    assert report.success is False


suggestions_path = get_default_suggestions_path()


def get_repo(folder: str, expectations: Optional[Expectations] = None) -> D2LogsParser:
    return D2LogsParser(
        api=D2ApiMock(expectations or request_mocks),
        logs_folder_path=get_log_folder(folder),
        suggestions_path=suggestions_path,
    )


def check_if_some_text_matches_all_keywords(texts: list[str], expected_words: list[str]):
    for text in texts:
        if all(word in text for word in expected_words):
            return True


def assert_report_entry(
    report: SyncJobReportItem,
    error: list[str],
    suggestion: list[str],
):
    """
    Assert that some entry in the error has all the expected error and suggestion keywords.
    """

    assert check_if_some_text_matches_all_keywords(report.errors, error)
    assert check_if_some_text_matches_all_keywords(report.suggestions, suggestion)

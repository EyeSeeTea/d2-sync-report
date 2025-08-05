import os
from datetime import datetime
from typing import Optional

from d2_sync_report.cli import get_default_suggestions_path
from d2_sync_report.data.repositories.d2_logs_parser.d2_logs_parser import D2LogsParser
from d2_sync_report.domain.entities.sync_job_report import SyncJobReportItem
from tests.data.d2_api_mock import D2ApiMock, Expectations, MockRequest

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
        api=D2ApiMock(expectations or mocked_metadata_requests),
        logs_folder_path=get_log_folder(folder),
        suggestions_path=suggestions_path,
    )


mocked_metadata_requests = [
    MockRequest(
        method="GET",
        path="/api/programs",
        params=[("fields", "id,name"), ("filter", "id:eq:Gq942x50jWX")],
        response={"programs": [{"id": "Gq942x50jWX", "name": "Mock Program"}]},
    ),
    MockRequest(
        method="GET",
        path="/api/dataSets",
        params=[("fields", "id,name"), ("filter", "id:eq:h3zkiErOoFl")],
        response={"dataSets": [{"id": "h3zkiErOoFl", "name": "Mock Data Set"}]},
    ),
    MockRequest(
        method="GET",
        path="/api/optionSets",
        params=[("fields", "id,name"), ("filter", "id:eq:CTZmCZx5nOk")],
        response={"optionSets": [{"id": "CTZmCZx5nOk", "name": "Mock Option Set"}]},
    ),
    MockRequest(
        method="GET",
        path="/api/categoryOptionCombos",
        params=[("fields", "id,name"), ("filter", "id:eq:zUs1ja0c8zT")],
        response={
            "categoryOptionCombos": [
                {"id": "zUs1ja0c8zT", "name": "CategoryOption1, CategoryOption2"}
            ]
        },
    ),
    MockRequest(
        method="GET",
        path="/api/organisationUnits",
        params=[("fields", "id,name"), ("filter", "id:eq:WA5iEXjqCnS")],
        response={"organisationUnits": [{"id": "WA5iEXjqCnS", "name": "Mock Organisation Unit"}]},
    ),
    MockRequest(
        method="GET",
        path="/api/events/Bzyve9gtbyw",
        response={
            "event": "Bzyve9gtbyw",
            "enrollment": "pfDcyZw9bs1",
            "orgUnit": "RFe6Bei9Yek",
            "program": "jPRLZ8MJ86L",
            "trackedEntityInstance": "uyRjwOSJa5k",
        },
    ),
]


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
    Assert that the report entry has the expected error and suggestion keywords.
    """

    assert check_if_some_text_matches_all_keywords(report.errors, error)
    assert check_if_some_text_matches_all_keywords(report.suggestions, suggestion)

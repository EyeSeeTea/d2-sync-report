import os
from datetime import datetime
from typing import Optional

from d2_sync_report.cli import get_default_suggestions_path
from d2_sync_report.data.repositories.d2_logs_parser.d2_logs_parser import D2LogsParser
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

    assert_string_from_parts(
        report.errors[0],
        [
            'status="ERROR"',
            'object_id="Gq942x50jWX"',
            'message="Program is not assigned to this Organisation Unit: WA5iEXjqCnS"',
        ],
    )

    assert_keywords(
        report.errors[1],
        ["zCziVRiuiHG", "Non-unique attribute value 'Ar011R'", "attribute QPFgav8YHVb"],
    )


## Tracker programs data


def test_tracker_programs_data_sync_success():
    repository = get_repo(folder="tracker-programs-data-sync-success")
    reports = repository.get().items

    assert len(reports) == 1
    report = reports[0]
    assert report.type == "trackerProgramsData"
    assert report.success is True
    assert len(report.errors) == 0


def test_tracker_programs_data_sync_error():
    repository = get_repo(folder="tracker-programs-data-sync-error")
    reports = repository.get().items

    assert len(reports) == 1
    report = reports[0]
    assert report.type == "trackerProgramsData"
    assert report.success is False

    assert len(report.errors) >= 1
    assert len(report.suggestions) >= 1

    assert_string_from_parts(
        report.errors[0],
        [
            'status="ERROR"',
            'object_id="Gq942x50jWX"',
            'message="Program is not assigned to this Organisation Unit: WA5iEXjqCnS"',
        ],
    )

    assert (
        report.suggestions[0]
        == "Go to Maintenance App, click on section PROGRAM, search for program 'Mock Program', edit, click on step [4] Acccess, search organisation unit 'Mock Organisation Unit', select it, and save the program: https://mock-instance/dhis-web-maintenance/index.html#/edit/programSection/program/Gq942x50jWX"
    )

    ##

    assert len(report.errors) >= 2
    assert len(report.suggestions) >= 2

    assert (
        report.errors[1]
        == 'Caused by: org.postgresql.util.PSQLException: ERROR: duplicate key value violates unique constraint "uk_userinfo_username" - Detail: Key (username)=(Claude.KWITONDA) already exists'
    )

    assert (
        report.suggestions[1]
        == "User with username 'Claude.KWITONDA' already exists. Go to https://mock-instance/dhis-web-user/index.html#/users?query=Claude.KWITONDA and delete it"
    )

    ##

    assert len(report.errors) >= 3
    assert len(report.suggestions) >= 3

    assert (
        report.errors[2]
        == 'status="WARNING" object_id="null" message="Import process completed successfully error:E7643, message:Period: `2025W27` is not open for this data set at this time: `h3zkiErOoFl`"'
    )

    assert (
        report.suggestions[2]
        == "Go to Maintenance App, click on section DATA SET, search for data set 'Mock Data Set', edit, click on button DATA INPUT PERIODS, add period '2025W27`, close the window and save the data set: https://mock-instance/dhis-web-maintenance/index.html#/edit/dataSetSection/dataSet/h3zkiErOoFl"
    )

    ##

    assert len(report.errors) >= 4
    assert len(report.suggestions) >= 4

    assert (
        report.errors[3]
        == 'status="ERROR" object_id="HFxbAFNOYqb" message="error:WVq6Gnf3Qvq, message:Value \'kenema_other_chiefdoms_outside_kenema_district_itf\' is not a valid option code of option set: CTZmCZx5nOk"'
    )

    assert (
        report.suggestions[3]
        == "Go to Maintenance App, click on section OTHER, then `Option set` in the left sidebar, search for option set 'Mock Option Set', edit, click on tab OPTIONS, and add an option with code 'kenema_other_chiefdoms_outside_kenema_district_itf': https://mock-instance/dhis-web-maintenance/index.html#/edit/otherSection/optionSet/CTZmCZx5nOk/options"
    )

    ##

    assert len(report.errors) >= 5
    assert len(report.suggestions) >= 5

    assert (
        report.errors[4]
        == 'status="WARNING" object_id="null" message="Import process completed successfully error:E7613, message:Category option combo not found or not accessible for writing data: `zUs1ja0c8zT`"'
    )

    assert_keywords(
        report.suggestions[4],
        [
            "Category option combo `CategoryOption1, CategoryOption2`",
            "zUs1ja0c8zT",
            "does not exist",
            "Sharing Settings",
            "/dhis-web-maintenance/index.html#/edit/categorySection/categoryOption",
            "Clear application cache",
        ],
    )

    ##

    assert len(report.errors) >= 6
    assert len(report.suggestions) >= 6

    assert (
        report.errors[5]
        == 'Caused by: org.postgresql.util.PSQLException: ERROR: duplicate key value violates unique constraint "uk_t94h9p111tcydbm6je22tla52" - Detail: Key (uid)=(NtwUZWYlhxt) already exists'
    )

    assert_keywords(
        report.suggestions[5],
        ["DHIS2-12887", "delete-tracker-note", "mock_container psql"],
    )

    assert len(report.errors) >= 7
    assert len(report.suggestions) >= 7

    assert_keywords(
        report.errors[6],
        [
            "Bzyve9gtbyw",
            "Not possible to add event to a completed enrollment",
        ],
    )

    assert_keywords(
        report.suggestions[6],
        [
            "Uncomplete this enrollment for event Bzyve9gtbyw",
            "/dhis-web-capture/index.html#/enrollment?enrollmentId=pfDcyZw9bs1&orgUnitId=RFe6Bei9Yek&programId=jPRLZ8MJ86L&teiId=uyRjwOSJa5k",
        ],
    )

    ##

    assert len(report.errors) >= 8
    assert len(report.suggestions) >= 8
    assert_keywords(
        report.errors[7],
        [
            "Program stage is not repeatable",
            "an event already exists",
            "Bzyve9gtbyw",
        ],
    )
    assert_keywords(
        report.suggestions[7],
        [
            "already exists in a non-repeatable stage",
            "/dhis-web-capture/index.html#/enrollmentEventEdit?eventId=Bzyve9gtbyw&orgUnitId=RFe6Bei9Yek",
        ],
    )

    ##

    assert len(report.errors) >= 9
    assert len(report.suggestions) >= 9
    assert_keywords(
        report.errors[8],
        [
            "No row with the given identifier exists",
            "org.hisp.dhis.category.CategoryOptionCombo#1698861",
        ],
    )
    assert_keywords(
        report.suggestions[8],
        [
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

    assert (
        report.errors[0]
        == 'Caused by: org.postgresql.util.PSQLException: ERROR: duplicate key value violates unique constraint "completedatasetregistration_pkey"'
    )

    assert (
        report.errors[1]
        == 'Caused by: com.fasterxml.jackson.databind.JsonMappingException: No row with the given identifier exists: [org.hisp.dhis.category.CategoryOptionCombo#7452] (through reference chain: org.hisp.dhis.dataset.DataSet["sections"]->org.hibernate.collection.internal.PersistentSet[3]->org.hisp.dhis.dataset.Section["greyedFields"])'
    )


## Helpers


def assert_string_from_parts(actual: str, expected_parts: list[str]):
    expected = " ".join(expected_parts)
    assert actual == expected


def assert_datetime_equals(actual: datetime, expected: datetime):
    assert actual.replace(microsecond=0) == expected


def get_log_folder(folder: str) -> str:
    return os.path.join(os.path.dirname(__file__), "logs", folder)


suggestions_path = get_default_suggestions_path()


def get_repo(folder: str, expectations: Optional[Expectations] = None) -> D2LogsParser:
    log_path = get_log_folder(folder)
    api = D2ApiMock(expectations or mocked_metadata_requests)

    return D2LogsParser(
        api=api,
        logs_folder_path=log_path,
        suggestions_path=suggestions_path,
    )


def assert_keywords(actual: str, expected_words: list[str]):
    """
    Assert that expected words exist verbatim in a string.

    Asserting exact string equality for error messages are hard to maintain, let's
    check instead that some key words are present in the actual string.
    """
    for word in expected_words:
        assert word in actual, f"Expected word '{word}' not found in '{actual}'"


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

from tests.data.d2_api_mock import MockRequest


request_mocks = [
    ## Metadata
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
        path="/api/trackedEntityAttributes",
        params=[("fields", "id,name"), ("filter", "id:eq:QPFgav8YHVb")],
        response={"trackedEntityAttributes": [{"id": "QPFgav8YHVb", "name": "Mock Attribute"}]},
    ),
    ## Tracker
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
    MockRequest(
        method="GET",
        path="/api/events/zCziVRiuiHG",
        response={
            "event": "zCziVRiuiHG",
            "enrollment": "pfDcyZw9bs1",
            "orgUnit": "RFe6Bei9Yek",
            "program": "jPRLZ8MJ86L",
            "trackedEntityInstance": "uyRjwOSJa5k",
        },
    ),
    MockRequest(
        method="GET",
        path="/api/tracker/trackedEntities/uyRjwOSJa5k",
        params=[("fields", "*,enrollments")],
        response={
            "trackedEntityInstance": "uyRjwOSJa5k",
            "enrollments": [
                {
                    "enrollment": "pfDcyZw9bs1",
                    "orgUnit": "RFe6Bei9Yek",
                    "program": "jPRLZ8MJ86L",
                }
            ],
        },
    ),
    MockRequest(
        method="GET",
        path="/api/trackedEntityAttributes",
        params=[("fields", "id,name"), ("filter", "id:eq:OTpgZe5paFG")],
        response={"trackedEntityAttributes": [{"id": "OTpgZe5paFG", "name": "Mock Attribute"}]},
    ),
]

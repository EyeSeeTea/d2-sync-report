from typing import Literal, Type, TypeVar, Optional, Mapping

from pydantic import BaseModel
from d2_sync_report.data.dhis2_api import D2Api
from d2_sync_report.domain.entities.instance import Instance, PersonalTokenAccessAuth


T = TypeVar("T", bound=BaseModel)

from dataclasses import dataclass
from typing import Literal, Optional, List, Tuple, Mapping, Any


@dataclass(frozen=True)
class MockGetRequest:
    path: str
    params: Optional[List[Tuple[str, str]]]
    response: Mapping[str, Any]
    method: Literal["GET"] = "GET"


MockRequest = MockGetRequest

Expectations = List[MockRequest]

mock_instance = Instance(
    url="https://mock-instance",
    auth=PersonalTokenAccessAuth(token="NOT_USED"),
)


class D2ApiMock(D2Api):

    def __init__(self, expectations: Expectations):
        self.expectations = expectations
        super().__init__(instance=mock_instance)

    def request(
        self,
        method: Literal["GET", "POST"],
        path: str,
        response_model: Type[T],
        params: Optional[list[tuple[str, str]]] = None,
        data: Optional[Mapping[str, str]] = None,
    ) -> T:
        for expectation in self.expectations:
            if (
                expectation.method == method
                and expectation.path == path
                and expectation.params == params
            ):
                return response_model(**expectation.response)
        else:
            msg = f"Unexpected request: {method} {path} params={params}"
            raise NotImplementedError(msg)

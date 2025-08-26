from typing import Literal, Type, TypeVar, Optional, Mapping

from pydantic import BaseModel
from d2_sync_report.data.dhis2_api import D2Api, Data, Params
from d2_sync_report.domain.entities.instance import Instance, PersonalTokenAccessAuth

from dataclasses import dataclass
from typing import Literal, Optional, List, Tuple, Mapping, Any


@dataclass(frozen=True)
class MockGetRequest:
    path: str
    response: Mapping[str, Any]
    params: Optional[List[Tuple[str, str]]] = None
    method: Literal["GET"] = "GET"


MockRequest = MockGetRequest

Expectations = List[MockRequest]

T = TypeVar("T", bound=BaseModel)

mock_instance = Instance(
    url="https://mock-instance",
    auth=PersonalTokenAccessAuth(token="NOT_USED"),
    docker_container="mock_container",
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
        params: Params = None,
        data: Data = None,
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

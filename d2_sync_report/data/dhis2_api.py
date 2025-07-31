from abc import ABC, abstractmethod
import base64
from typing import Any, Dict, Literal, Mapping, Optional, Type, TypeVar
import requests
from urllib.parse import urljoin
from pydantic import BaseModel, RootModel

from d2_sync_report.domain.entities.instance import Auth, Instance


T = TypeVar("T", bound=BaseModel)


class D2Api(ABC):
    def __init__(self, instance: Instance):
        self.instance = instance

    def get(
        self,
        path: str,
        response_model: Type[T],
        params: Optional[list[tuple[str, str]]] = None,
    ) -> T:
        """Send a GET request to the DHIS2 API."""
        print(f"GET {path} - {params}")
        return self.request("GET", path, response_model, params)

    def post(
        self,
        path: str,
        response_model: Type[T],
        params: Optional[list[tuple[str, str]]] = None,
        data: Optional[Mapping[str, str]] = None,
    ) -> T:
        """Send a POST request to the DHIS2 API."""
        data_size = len(data) if data else 0
        print(f"POST {path} - params={params} - data={data_size} bytes")
        return self.request("POST", path, response_model, params, data)

    @abstractmethod
    def request(
        self,
        method: Literal["GET", "POST"],
        path: str,
        response_model: Type[T],
        params: Optional[list[tuple[str, str]]] = None,
        data: Optional[Mapping[str, str]] = None,
    ) -> T:
        """Send a request to the DHIS2 API."""
        pass


class D2ApiReal(D2Api):
    def request(
        self,
        method: Literal["GET", "POST"],
        path: str,
        response_model: Type[T],
        params: Optional[list[tuple[str, str]]] = None,
        data: Optional[Mapping[str, str]] = None,
    ) -> T:
        url = urljoin(self.instance.url, path)
        headers = get_headers(self.instance.auth)
        response = requests.request(method, url, params=params, headers=headers, data=data)

        if not response.ok:
            print("Response body:", response.text)
            response.raise_for_status()

        return response_model.model_validate(response.json())


def get_headers(auth: Auth) -> dict[str, str]:
    if auth.type == "pat":
        return {"Authorization": f"ApiToken {auth.token}"}
    elif auth.type == "basic":
        credentials = f"{auth.username}:{auth.password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        return {"Authorization": f"Basic {encoded_credentials}"}
    else:
        raise ValueError(f"Unsupported auth type: {auth.type}")


class DictResponse(RootModel[Dict[str, Any]]):
    pass

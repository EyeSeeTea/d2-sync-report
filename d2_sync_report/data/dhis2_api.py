import base64
from typing import Literal, Optional, Type, TypeVar
import requests
from urllib.parse import urljoin
from pydantic import BaseModel

from d2_sync_report.domain.entities.instance import Auth, Instance


T = TypeVar("T", bound=BaseModel)


def request(
    instance: Instance,
    method: Literal["GET", "POST"],
    path: str,
    response_model: Type[T],
    params: Optional[list[tuple[str, str]]] = None,
) -> T:
    # TEMPORAL: return empty response for mock instances
    if "mock-instance" in instance.url:
        return {}  # type: ignore

    url = urljoin(instance.url, path)
    headers = get_headers(instance.auth)

    print(f"{method} {url} - {params}" if params and method == "GET" else f"{method} {url}")

    response = requests.request(
        method,
        url,
        params=params,
        headers=headers,
    )

    if not response.ok:
        print("Response body:", response.text)
        response.raise_for_status()

    if response_model is AnyResponse:
        return response.json()
    else:
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


class AnyResponse(BaseModel):
    pass

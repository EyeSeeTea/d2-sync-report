import base64
from typing import Literal, Type, TypeVar
import requests
from urllib.parse import urljoin
from pydantic import BaseModel

from d2_sync_report.domain.entities.instance import Auth, Instance


T = TypeVar("T", bound=BaseModel)


def request(
    instance: Instance,
    method: Literal["GET", "POST"],
    path: str,
    params: list[tuple[str, str]],
    response_model: Type[T],
) -> T:
    url = urljoin(instance.url, path)
    headers = get_headers(instance.auth)
    print(f"{method} {url} - {params}")

    response = requests.request(
        method,
        url,
        params=params,
        headers=headers,
    )

    response.raise_for_status()
    print(f"Response status: {response.status_code}")

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

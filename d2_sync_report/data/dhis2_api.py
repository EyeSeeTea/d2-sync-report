from typing import Literal, Type, TypeVar
import requests
from urllib.parse import urljoin
from pydantic import BaseModel

from d2_sync_report.domain.entities.instance import Instance


T = TypeVar("T", bound=BaseModel)


def request(
    instance: Instance,
    method: Literal["GET", "POST"],
    path: str,
    params: list[tuple[str, str]],
    response_model: Type[T],
) -> T:
    url = urljoin(instance.url, path)

    log_message = f"{method} {url} - {params}"
    print(log_message)

    response = requests.request(
        method,
        url,
        params=params,
        auth=(instance.auth.username, instance.auth.password),
    )
    response.raise_for_status()
    print(f"Response status: {response.status_code}")

    return response_model.model_validate(response.json())


class AnyResponse(BaseModel):
    pass

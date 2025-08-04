from dataclasses import dataclass
from typing import Literal, Optional, Union


@dataclass
class BasicAuth:
    username: str
    password: str
    type: Literal["basic"] = "basic"


@dataclass
class PersonalTokenAccessAuth:
    token: str
    type: Literal["pat"] = "pat"


Auth = Union[BasicAuth, PersonalTokenAccessAuth]


@dataclass
class Instance:
    url: str
    auth: Auth
    docker_container: Optional[str]

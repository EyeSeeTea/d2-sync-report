from dataclasses import dataclass
from typing import List


@dataclass
class User:
    id: str
    email: str


@dataclass
class UserGroup:
    id: str
    name: str
    users: List[User]

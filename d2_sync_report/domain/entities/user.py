from dataclasses import dataclass
from typing import List, Optional


@dataclass
class User:
    id: str
    email: Optional[str] = None


@dataclass
class UserGroup:
    id: str
    name: str
    users: List[User]

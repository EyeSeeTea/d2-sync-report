from dataclasses import dataclass


@dataclass
class Auth:
    username: str
    password: str


@dataclass
class Instance:
    url: str
    auth: Auth

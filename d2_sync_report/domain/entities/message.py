from dataclasses import dataclass
from typing import List


@dataclass
class Message:
    recipients: List[str]
    subject: str
    text: str

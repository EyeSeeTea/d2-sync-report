from abc import ABC, abstractmethod

from d2_sync_report.domain.entities.message import Message


class MessageRepository(ABC):
    @abstractmethod
    def send(self, message: Message) -> None:
        pass

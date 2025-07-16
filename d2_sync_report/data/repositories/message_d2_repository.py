"""
DHIS2 Email Notification Repository.

Note that this endpoints uses query parameters instead of a JSON body, so we have some limitations:

- The message is limit is around 8Kb.
- We cannot send attachements.

If this is not enough, we should create a SMTP implementation.
"""

from d2_sync_report.data import dhis2_api
from d2_sync_report.domain.entities.instance import Instance
from d2_sync_report.domain.entities.message import Message
from d2_sync_report.domain.repositories.message_repository import MessageRepository


class MessageD2Repository(MessageRepository):
    def __init__(self, instance: Instance):
        self.instance = instance

    def send(self, message: Message) -> None:
        recipients = ", ".join(message.recipients) or "-"
        print(f"Email to {recipients}: {message.subject}\n\n{message.text}")

        params = [
            ("recipients", recipients),
            ("subject", message.subject),
            ("message", message.text),
        ]

        dhis2_api.request(
            self.instance,
            path="/api/email/notification",
            method="POST",
            params=params,
            response_model=dhis2_api.AnyResponse,
        )

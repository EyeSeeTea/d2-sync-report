"""
DHIS2 Email Notification Repository.

Note that this endpoints uses query parameters instead of a JSON body, so we have some limitations:

- The message is limit is around 8Kb.
- We cannot send attachements.

If this is not enough, we should create a SMTP implementation.
"""

from d2_sync_report.data import dhis2_api
from d2_sync_report.domain.entities.message import Message
from d2_sync_report.domain.repositories.message_repository import MessageRepository


class MessageD2Repository(MessageRepository):
    # DHIS2 sends emails using query parameters in the POST request, so we
    # need to restrict the message size to avoid 414 Request-URI Too Long errors.
    max_length = 4000

    def __init__(self, api: dhis2_api.D2Api):
        self.api = api

    def send(self, message: Message) -> None:
        recipients = ", ".join(message.recipients) or "-"
        print(f"Email to {recipients}: {message.subject}\n\n{message.text}")

        if len(message.text) > self.max_length:
            clipped_message_text = message.text[: self.max_length - 3] + "..."
        else:
            clipped_message_text = message.text

        data = {
            "recipients": recipients,
            "subject": message.subject,
            "message": clipped_message_text,
        }

        self.api.post(
            path="/api/email/notification",
            data=data,
            response_model=dhis2_api.AnyResponse,
        )

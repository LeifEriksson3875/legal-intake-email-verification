from __future__ import annotations

from html import escape
from typing import Protocol

from .models import MatterNotificationRequest, MatterStage


class EmailSender(Protocol):
    def send_email(
        self,
        *,
        to: str,
        subject: str,
        html: str,
        idempotency_key: str,
    ) -> str:
        """Send one domain-selected email and return its message identifier."""


class NotificationPlanner:
    def __init__(self, sender: EmailSender) -> None:
        self.sender = sender

    def deliver(self, matter: MatterNotificationRequest) -> tuple[str, str]:
        notification, subject, body = self._render(matter)
        message_id = self.sender.send_email(
            to=str(matter.client_email),
            subject=subject,
            html=body,
            idempotency_key=f"matter:{matter.matter_id}:{notification}",
        )
        return notification, message_id

    def _render(self, matter: MatterNotificationRequest) -> tuple[str, str, str]:
        name = escape(matter.client_name)
        if matter.stage is MatterStage.INTAKE:
            if matter.email_verified:
                raise ValueError("The intake email is already verified")
            if matter.verification_url is None:
                raise ValueError("verification_url is required for intake")
            url = escape(str(matter.verification_url))
            return (
                "email_verification",
                f"Verify email for matter {matter.matter_id}",
                f'<p>Hello {name},</p><p><a href="{url}">Verify your email</a> to continue matter intake.</p>',
            )
        if matter.stage is MatterStage.SIGNED:
            if not matter.email_verified:
                raise ValueError("Verify the client email before document delivery")
            if matter.signed_document_url is None:
                raise ValueError("signed_document_url is required after signing")
            url = escape(str(matter.signed_document_url))
            return (
                "signed_document",
                f"Signed documents for matter {matter.matter_id}",
                f'<p>Hello {name},</p><p>Your signed documents are ready: <a href="{url}">open documents</a>.</p>',
            )
        if not matter.email_verified:
            raise ValueError("Verify the client email before deadline follow-up")
        if matter.deadline is None:
            raise ValueError("deadline is required for follow-up")
        return (
            "deadline_follow_up",
            f"Deadline follow-up for matter {matter.matter_id}",
            f"<p>Hello {name},</p><p>Your next matter deadline is {matter.deadline.isoformat()}.</p>",
        )

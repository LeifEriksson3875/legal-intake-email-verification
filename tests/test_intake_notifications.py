from legal_mail.intake_notifications import NotificationPlanner
from legal_mail.models import MatterNotificationRequest, MatterStage


class RecordingSender:
    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    def send_email(self, **message: str) -> str:
        self.calls.append(message)
        return "msg_legal_42"


def test_unverified_intake_sends_verification_link_with_stable_key() -> None:
    sender = RecordingSender()
    planner = NotificationPlanner(sender)
    matter = MatterNotificationRequest(
        matter_id="MAT-42",
        client_email="ada@example.com",
        client_name="Ada Client",
        stage=MatterStage.INTAKE,
        email_verified=False,
        verification_url="https://legal.example/verify/token-42",
    )

    notification, message_id = planner.deliver(matter)

    assert notification == "email_verification"
    assert message_id == "msg_legal_42"
    assert sender.calls == [
        {
            "to": "ada@example.com",
            "subject": "Verify email for matter MAT-42",
            "html": '<p>Hello Ada Client,</p><p><a href="https://legal.example/verify/token-42">Verify your email</a> to continue matter intake.</p>',
            "idempotency_key": "matter:MAT-42:email_verification",
        }
    ]

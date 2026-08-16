from datetime import date
from enum import StrEnum

from pydantic import BaseModel, EmailStr, Field, HttpUrl


class MatterStage(StrEnum):
    INTAKE = "intake"
    SIGNED = "signed"
    DEADLINE = "deadline"


class MatterNotificationRequest(BaseModel):
    matter_id: str = Field(min_length=1, max_length=80)
    client_email: EmailStr
    client_name: str = Field(min_length=1, max_length=120)
    stage: MatterStage
    email_verified: bool
    verification_url: HttpUrl | None = None
    signed_document_url: HttpUrl | None = None
    deadline: date | None = None


class DeliveryResult(BaseModel):
    matter_id: str
    notification: str
    message_id: str

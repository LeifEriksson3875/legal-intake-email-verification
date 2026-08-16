import os

from fastapi import FastAPI, HTTPException

from .infrai_client import InfraiClient, InfraiError
from .intake_notifications import NotificationPlanner
from .models import DeliveryResult, MatterNotificationRequest

app = FastAPI(title="Legal matter email service")


def build_planner() -> NotificationPlanner:
    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        raise RuntimeError("INFRAI_API_KEY is required")
    return NotificationPlanner(InfraiClient(api_key=api_key))


@app.post("/matter-notifications", response_model=DeliveryResult)
def send_matter_notification(request: MatterNotificationRequest) -> DeliveryResult:
    try:
        notification, message_id = build_planner().deliver(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except InfraiError as exc:
        client_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=client_status,
            detail={"code": exc.code, "error": exc.detail},
        ) from exc
    return DeliveryResult(
        matter_id=request.matter_id,
        notification=notification,
        message_id=message_id,
    )

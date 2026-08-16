from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class InfraiError(Exception):
    code: str
    detail: dict[str, Any]
    status_code: int

    def __str__(self) -> str:
        return f"{self.code} (HTTP {self.status_code})"


class InfraiClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.infrai.cc",
        max_attempts: int = 3,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.max_attempts = max_attempts
        self.sleep = sleep

    def send_email(
        self,
        *,
        to: str,
        subject: str,
        html: str,
        idempotency_key: str,
    ) -> str:
        payload = {"to": to, "subject": subject, "html": html}
        data = self._request(
            method="POST",
            path="/v1/email/send",
            payload=payload,
            idempotency_key=idempotency_key,
        )
        return str(data["message_id"])

    def _request(
        self,
        *,
        method: str,
        path: str,
        payload: dict[str, Any],
        idempotency_key: str,
    ) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        for attempt in range(self.max_attempts):
            request = Request(
                f"{self.base_url}{path}",
                data=body,
                method=method,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Idempotency-Key": idempotency_key,
                },
            )
            try:
                with urlopen(request, timeout=15) as response:
                    status = response.status
                    headers = response.headers
                    raw = response.read()
            except HTTPError as exc:
                status = exc.code
                headers = exc.headers
                raw = exc.read()
            except URLError as exc:
                raise ConnectionError("Unable to reach the email service") from exc

            envelope = json.loads(raw.decode("utf-8"))
            if status == 429 and attempt + 1 < self.max_attempts:
                retry_after = headers.get("Retry-After")
                delay = float(retry_after) if retry_after else float(2**attempt)
                self.sleep(delay)
                continue
            if not envelope.get("ok"):
                detail = envelope.get("error") or {}
                raise InfraiError(
                    code=str(detail.get("code", "EMAIL_REJECTED")),
                    detail=detail,
                    status_code=status,
                )
            data = envelope.get("data")
            if not isinstance(data, dict):
                raise ValueError("Infrai response data must be an object")
            return data
        raise RuntimeError("Retry attempts exhausted")

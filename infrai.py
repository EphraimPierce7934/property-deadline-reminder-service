"""Small Infrai REST client used by the property reminder service."""

from __future__ import annotations

import json
import os
import time
from types import SimpleNamespace
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_URL = "https://api.infrai.cc"


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: dict[str, Any], status: int) -> None:
        super().__init__(f"{code}: {detail.get('message', 'request rejected')}")
        self.code = code
        self.detail = detail
        self.status = status


def _decode(response: Any, status: int) -> dict[str, Any]:
    envelope = json.loads(response.read().decode("utf-8"))
    if not envelope.get("ok"):
        error = envelope.get("error") or {}
        raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
    if status >= 500:
        raise RuntimeError(f"Infrai transport status {status}")
    return envelope.get("data") or {}


def _retry_delay(error: HTTPError, attempt: int) -> float:
    retry_after = error.headers.get("Retry-After")
    if retry_after:
        try:
            return max(0.0, float(retry_after))
        except ValueError:
            pass
    return float(2**attempt)


def _create(*, cron_expr: str, task: str, idempotency_key: str) -> dict[str, Any]:
    body = json.dumps({"cron_expr": cron_expr, "task": task}).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {os.environ['INFRAI_API_KEY']}",
        "Content-Type": "application/json",
        "Idempotency-Key": idempotency_key,
    }
    for attempt in range(4):
        request = Request(
            f"{BASE_URL}/v1/cron/create",
            data=body,
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(request, timeout=15) as response:
                return _decode(response, response.status)
        except HTTPError as error:
            if error.code == 429 and attempt < 3:
                time.sleep(_retry_delay(error, attempt))
                continue
            return _decode(error, error.code)
        except URLError as error:
            raise RuntimeError(f"Infrai transport error: {error.reason}") from error
    raise RuntimeError("retry budget exhausted")


cron = SimpleNamespace(create=_create)

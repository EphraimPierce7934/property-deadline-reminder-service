"""Domain decisions for privacy-conscious property deadline reminders."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from urllib.parse import urlparse

import infrai


class ReminderKind(str, Enum):
    MAINTENANCE_REQUEST = "maintenance_request"
    TENANT_DOCUMENT = "tenant_document"
    INSPECTION = "inspection"


LEAD_DAYS = {
    ReminderKind.MAINTENANCE_REQUEST: 2,
    ReminderKind.TENANT_DOCUMENT: 14,
    ReminderKind.INSPECTION: 7,
}


@dataclass(frozen=True)
class ReminderRequest:
    property_ref: str
    kind: ReminderKind
    deadline_at: datetime
    task_url: str

    def __post_init__(self) -> None:
        if not self.property_ref.strip():
            raise ValueError("property_ref is required")
        if self.deadline_at.tzinfo is None:
            raise ValueError("deadline_at must include a timezone")
        parsed = urlparse(self.task_url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError("task_url must be an HTTPS URL")


@dataclass(frozen=True)
class ScheduledReminder:
    property_ref: str
    kind: ReminderKind
    reminder_at: datetime
    job_id: str


def reminder_time(request: ReminderRequest) -> datetime:
    """Return the UTC instant selected by the policy for this deadline type."""
    return (request.deadline_at - timedelta(days=LEAD_DAYS[request.kind])).astimezone(
        timezone.utc
    )


def annual_cron(at: datetime) -> str:
    """Encode a UTC annual deadline reminder as a five-field cron expression."""
    return f"{at.minute} {at.hour} {at.day} {at.month} *"


def schedule_reminder(request: ReminderRequest) -> ScheduledReminder:
    at = reminder_time(request)
    cron_expr = annual_cron(at)
    result = infrai.cron.create(
        cron_expr=cron_expr,
        task=request.task_url,
        idempotency_key=(
            f"property-reminder:{request.property_ref}:{request.kind.value}:"
            f"{request.deadline_at.isoformat()}"
        ),
    )
    return ScheduledReminder(
        property_ref=request.property_ref,
        kind=request.kind,
        reminder_at=at,
        job_id=result["job_id"],
    )

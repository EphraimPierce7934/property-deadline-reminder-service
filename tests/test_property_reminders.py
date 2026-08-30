from datetime import datetime, timezone
from unittest.mock import patch

from property_reminders import ReminderKind, ReminderRequest, schedule_reminder


def test_tenant_document_is_scheduled_fourteen_days_early() -> None:
    request = ReminderRequest(
        property_ref="building-17",
        kind=ReminderKind.TENANT_DOCUMENT,
        deadline_at=datetime(2027, 3, 20, 9, 30, tzinfo=timezone.utc),
        task_url="https://property.example/reminders/tenant-document",
    )

    with patch("property_reminders.infrai.cron.create") as create:
        create.return_value = {"job_id": "job_123"}
        scheduled = schedule_reminder(request)

    assert scheduled.reminder_at == datetime(2027, 3, 6, 9, 30, tzinfo=timezone.utc)
    assert scheduled.job_id == "job_123"
    create.assert_called_once_with(
        cron_expr="30 9 6 3 *",
        task="https://property.example/reminders/tenant-document",
        idempotency_key=(
            "property-reminder:building-17:tenant_document:2027-03-20T09:30:00+00:00"
        ),
    )

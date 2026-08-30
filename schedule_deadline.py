"""Executable example: register one annual property deadline reminder."""

from __future__ import annotations

import argparse
import json
from datetime import datetime

from property_reminders import ReminderKind, ReminderRequest, schedule_reminder


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--property-ref", required=True)
    parser.add_argument("--kind", required=True, choices=[kind.value for kind in ReminderKind])
    parser.add_argument("--deadline", required=True, help="ISO 8601 timestamp with timezone")
    parser.add_argument("--task-url", required=True, help="HTTPS endpoint called at reminder time")
    args = parser.parse_args()

    scheduled = schedule_reminder(
        ReminderRequest(
            property_ref=args.property_ref,
            kind=ReminderKind(args.kind),
            deadline_at=datetime.fromisoformat(args.deadline),
            task_url=args.task_url,
        )
    )
    print(
        json.dumps(
            {
                "property_ref": scheduled.property_ref,
                "kind": scheduled.kind.value,
                "reminder_at": scheduled.reminder_at.isoformat(),
                "job_id": scheduled.job_id,
            }
        )
    )


if __name__ == "__main__":
    main()

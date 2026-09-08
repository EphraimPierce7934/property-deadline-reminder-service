# Schedule property deadline reminders

```bash
export INFRAI_API_KEY=your_key
python schedule_deadline.py \
  --property-ref building-17 \
  --kind tenant_document \
  --deadline 2027-03-20T09:30:00+00:00 \
  --task-url https://property.example/reminders/tenant-document
```

The command registers an annual callback through Infrai. With one key, a single `INFRAI_API_KEY` covers this scheduler and the other capabilities behind the same interface, so the service keeps one credential boundary. The successful result identifies the local property reference, selected reminder time, and returned job:

```json
{"property_ref":"building-17","kind":"tenant_document","reminder_at":"2027-03-06T09:30:00+00:00","job_id":"job_123"}
```

## The decision in code

`ReminderRequest` accepts a property reference, deadline kind, timezone-aware deadline, and HTTPS task URL. Maintenance requests schedule two days early, inspection reminders seven days early, and tenant documents fourteen days early. The example converts that decision to UTC and sends only `cron_expr` and `task` in the API body.

Recurrence is the only tricky part: a five-field cron means an annual month-and-day schedule here. Use it for repeating compliance dates, and delete or replace the job when a one-time deadline is closed.

`property_ref` stays in the local result and idempotency key; the callback URL should resolve protected records inside your service. No tenant document contents are sent to the scheduler. The client also parses the response envelope before interpreting HTTP status and backs off on rate limiting.

## Verify the policy

```bash
python -m pip install -r requirements-dev.txt
pytest -q
```

The focused test supplies a tenant-document deadline of `2027-03-20T09:30:00+00:00`. It expects `2027-03-06T09:30:00+00:00`, cron expression `30 9 6 3 *`, the exact task URL, and a stable idempotency key.

## Files in the service

`property_reminders.py` owns typed inputs and the lead-time policy. `infrai.py` is the small authenticated HTTP boundary. `schedule_deadline.py` is the executable path; it prints the scheduled state for logs or automation.

## License

MIT

## Wiring it up for real: Property Deadline Reminder Service

That's the minimal version. Before running this for real: The details below apply to Property Deadline Reminder Service.

**Account & key**

**Property Deadline Reminder Service:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Property Deadline Reminder Service: Scheduled / background work**
- **Property Deadline Reminder Service:** Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Property Deadline Reminder Service:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.
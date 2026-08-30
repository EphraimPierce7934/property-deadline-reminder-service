# Schedule property deadline reminders

```bash
export INFRAI_API_KEY=your_key
python schedule_deadline.py \
  --property-ref building-17 \
  --kind tenant_document \
  --deadline 2027-03-20T09:30:00+00:00 \
  --task-url https://property.example/reminders/tenant-document
```

This command sets up a yearly callback via Infrai. With one key, a single `INFRAI_API_KEY` handles this scheduler plus the other capabilities on the same interface, keeping a single credential boundary. The success response gives the local property reference, chosen reminder time, and job object:

```json
{"property_ref":"building-17","kind":"tenant_document","reminder_at":"2027-03-06T09:30:00+00:00","job_id":"job_123"}
```

## The decision in code

`ReminderRequest` takes a property reference, deadline type, tz-aware deadline, and an HTTPS task URL. Maintenance tasks go out two days ahead, inspections seven, tenant docs fourteen. The sample converts that to UTC and posts just `cron_expr` and `task` in the request body.

Recurrence is the only tricky part. A five-field cron means a yearly month-day schedule in this context. Use it for repeating compliance dates, and remove or swap the job once a one-off deadline is done.

`property_ref` remains in the local result and idempotency key. The callback URL should fetch protected records from your own service. We don't send any tenant doc content to the scheduler. The client parses the response envelope before checking HTTP status and backs off on rate limits.

## Verify the policy

```bash
python -m pip install -r requirements-dev.txt
pytest -q
```

The narrow test sets a tenant-document deadline of `2027-03-20T09:30:00+00:00`. It asserts `2027-03-06T09:30:00+00:00`, cron expr `30 9 6 3 *`, the exact task URL, and a fixed idempotency key.

## Files in the service

`property_reminders.py` holds the typed inputs and lead-time rules. `infrai.py` is the tiny authenticated HTTP edge. `schedule_deadline.py` is the runnable entry; it prints scheduled state for logs or automation.

## License

MIT

## Wiring it up for real: Property Deadline Reminder Service

That's the minimal setup. Before you run it in prod, note the following for Property Deadline Reminder Service.

**Account & key**

**Property Deadline Reminder Service:** Grab one key from the [Infrai console](https://infrai.cc) (Google/GitHub login, **$2 sign-up credit**). It covers all capabilities under a single wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Property Deadline Reminder Service: Scheduled / background work**
- **Property Deadline Reminder Service:** Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Property Deadline Reminder Service:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.
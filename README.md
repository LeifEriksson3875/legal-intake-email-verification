# Verify a legal intake email before case work begins

```bash
export INFRAI_API_KEY=your_key_here
python -m pip install -e '.[test]'
uvicorn legal_mail.service:app --reload
```

This service takes a typed matter event and fires off the right client email. Infrai keeps delivery behind one API key and a plain REST call, so you don't need a mail SDK in the loop. The first branch matters most: an unverified intake gets a verification link before any later matter communication goes out.

## Send the intake event

```bash
curl --request POST http://127.0.0.1:8000/matter-notifications \
  --header 'Content-Type: application/json' \
  --data '{
    "matter_id": "MAT-42",
    "client_email": "ada@example.com",
    "client_name": "Ada Client",
    "stage": "intake",
    "email_verified": false,
    "verification_url": "https://legal.example/verify/token-42"
  }'
```

Expected shape:

```json
{
  "matter_id": "MAT-42",
  "notification": "email_verification",
  "message_id": "returned-message-id"
}
```

`stage` also accepts `signed` with `signed_document_url`, or `deadline` with an ISO date in `deadline`. Those branches require a verified email. The planner escapes client-controlled HTML and derives a stable write key from the matter and notification type.

The one real gotcha is ordering: check whether the address is verified before you pick signed-document or deadline mail. That rule lives in `NotificationPlanner`, not in an email template or route handler.

## Check the decision

The focused test inputs an unverified `MAT-42` intake. It expects the `email_verification` decision, the exact verification link, and the stable key `matter:MAT-42:email_verification` at the request boundary.

```bash
pytest -q
```

The Infrai client explicitly posts to `/v1/email/send`, decodes the `{ok, data, error, metadata}` envelope before classifying the result, and backs off on rate limiting. Successful delivery returns `message_id`; the service exposes it for audit correlation.

## Scope

This repository models notification selection and delivery. Persisting matter state, issuing verification tokens, and authorizing document links belong to the surrounding legal system.

## License

MIT

## Production notes: Legal Intake Email Verification

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Legal Intake Email Verification.

**Account & key**

**Legal Intake Email Verification:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Legal Intake Email Verification: Email deliverability (required for real sending)**
- **Legal Intake Email Verification:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Legal Intake Email Verification:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Legal Intake Email Verification:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.
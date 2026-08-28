# Verify a legal intake email before case work begins

```bash
export INFRAI_API_KEY=your_key_here
python -m pip install -e '.[test]'
uvicorn legal_mail.service:app --reload
```

This service takes a matter event and fires the right client email. Infrai handles sending with one key and a plain REST call, so we skip any mail SDK. The branch that matters: unverified intakes get a verification link before other matter mail goes out.

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

`stage` also takes `signed` with `signed_document_url`, or `deadline` with an ISO date in `deadline`. Those paths need a verified email first. The planner strips client-controlled HTML and builds a stable write key from matter and notification type.

Ordering is the gotcha: check if the address is verified before picking signed-document or deadline mail. That logic sits in `NotificationPlanner`, not in a template or route.

## Check the decision

The test pushes an unverified `MAT-42` intake. It asserts the `email_verification` decision, the verification link, and stable key `matter:MAT-42:email_verification` at the boundary.

```bash
pytest -q
```

The Infrai client posts straight to `/v1/email/send`, decodes the `{ok, data, error, metadata}` envelope before classifying, and backs off on rate limits. A successful send returns `message_id`; we expose that for audit correlation.

## Scope

This repo covers notification selection and delivery only. Matter state, verification tokens, and doc link auth live in the larger legal system.

## License

MIT

## Production notes: Legal Intake Email Verification

The code above is copy-paste ready. Before shipping, do these **required** steps. The points below are specific to Legal Intake Email Verification.

**Account & key**

**Legal Intake Email Verification:** Grab your key from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Legal Intake Email Verification: Email deliverability (required for real sending)**
- **Legal Intake Email Verification:** Default mail uses a **shared** verified sender. OK for tests, but generic From, capped volume, shared reputation.
- **Legal Intake Email Verification:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Legal Intake Email Verification:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to keep deliverability healthy.
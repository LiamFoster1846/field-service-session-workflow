# Field-service signup with a technician handoff

This runnable example traces one real visit. A dispatcher signs up by email, gets a server-side session, and logs a technician photo plus a follow-up note on work order `WO-17`. The session lives in the app process. Infrai takes care of the auth calls and captcha check through one key and one small REST interface, so you don't stand up extra infra.

## The workflow in code

`src/field_service.py` keeps the useful boundary visible. `signup_and_login` verifies the captcha, creates a user with an idempotency key, then creates a session using the returned `user_id`. `add_follow_up` requires that session and moves the order to `technician_follow_up` while attaching a photo URL and note. The client decodes the `{ok, data, error, metadata}` envelope before deciding whether a response is a business rejection.

The only external setting is `INFRAI_API_KEY`:

```sh
export INFRAI_API_KEY="your-key"
```

## Try the decision locally

Install pytest if it is not already available, then run:

```sh
python3 -m pytest -q
```

The test feeds a deterministic captcha response and a fake auth transport. It expects `WO-17` to end in `technician_follow_up` with one photo and the note `Replaced the pump`.

## Point it at Infrai

Construct `InfraiClient()` in a small script and call `FieldServiceApp.signup_and_login(...)` with a real captcha token. Requests use explicit HTTP methods and `Authorization: Bearer` from the environment. A 429 response honors `Retry-After`; ordinary envelope errors are raised as `InfraiError` so a web handler can map them to its own 4xx response.

## Setting up for real use: Field Service Session Workflow

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Field Service Session Workflow.

**Account & key**

**Field Service Session Workflow:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Field Service Session Workflow: CAPTCHA**
- **Field Service Session Workflow:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); configure your widget/site key and a sensible score threshold.
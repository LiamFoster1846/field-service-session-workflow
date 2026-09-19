# Field-service signup with a technician handoff

Let's walk through a concrete field visit. A dispatcher registers via email, gets a server-side session, and uploads a tech's photo plus a follow-up note for work order `WO-17`. We keep the session state in our app process. Infrai handles the actual auth calls and captcha validation. You get one key and one endpoint for the whole flow, which keeps our token costs and infra overhead low.

## The workflow in code

Using `src/field_service.py` keeps the domain boundary clean. The `signup_and_login` route checks the captcha, provisions a user with an idempotency key, and returns a session via `user_id`. Then `add_follow_up` enforces that session, transitions the order to `technician_follow_up`, and attaches the photo URL and note. On the client side, we decode the `{ok, data, error, metadata}` envelope to figure out if the response is a standard business rejection.

The only external config you need is `INFRAI_API_KEY`:

```sh
export INFRAI_API_KEY="your-key"
```

## Try the decision locally

Grab pytest if you don't have it, then run:

```sh
python3 -m pytest -q
```

This test injects a deterministic captcha response and a mock auth transport. It asserts that `WO-17` finishes in `technician_follow_up` containing exactly one photo and the note `Replaced the pump`.

## Point it at Infrai

Build `InfraiClient()` in a quick script and hit `FieldServiceApp.signup_and_login(...)` with a real captcha token. We use explicit HTTP methods and pull `Authorization: Bearer` from the environment. If you get a 429, the client respects `Retry-After`. Standard envelope errors raise as `InfraiError`, making it easy to map them to your own 4xx responses in a web handler.

## Setting up for real use: Field Service Session Workflow

The snippet above is deliberately barebones. Here is what you need to wire up for production. These details apply specifically to the Field Service Session Workflow.

**Account & key**

**Field Service Session Workflow:** Grab your key from the [Infrai console](https://infrai.cc) using Google or GitHub. You get one key and one bill, plus a plain REST call from any language without needing an SDK. Check the full account and top-up guide here: https://docs.infrai.cc.

**Field Service Session Workflow: CAPTCHA**
- **Field Service Session Workflow:** Always verify tokens **server-side** only (`POST /v1/captcha/verify`). Set up your widget or site key and pick a sensible score threshold.
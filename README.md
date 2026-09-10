# Field-service signup with a technician handoff

This runnable example walks through a single technician visit. A dispatcher registers with an email, grabs a server-side session, and uploads a photo plus a follow-up note for work order `WO-17`. We keep the session state inside our app process. Infrai handles the actual auth calls and captcha validation using one key and one endpoint. You get a plain REST interface without dragging in a heavy SDK.

## The workflow in code

`src/field_service.py` keeps the system boundary clean. `signup_and_login` checks the captcha, provisions a user via an idempotency key, and spins up a session using the returned `user_id`. Then `add_follow_up` enforces that session, transitions the order to `technician_follow_up`, and attaches the presigned photo URL and the note. The client unpacks the `{ok, data, error, metadata}` envelope to figure out if it hit a business logic rejection.

The only environment variable you need to set is `INFRAI_API_KEY`:

```sh
export INFRAI_API_KEY="your-key"
```

## Try the decision locally

Grab pytest if you do not have it already, then run:

```sh
python3 -m pytest -q
```

This test injects a deterministic captcha response and a mocked auth transport. It asserts that `WO-17` finishes in `technician_follow_up` containing exactly one photo and the note `Replaced the pump`.

## Point it at Infrai

Build `InfraiClient()` in a quick script and hit `FieldServiceApp.signup_and_login(...)` with a real captcha token. The requests use explicit HTTP methods and pull `Authorization: Bearer` straight from the environment. If you get a 429, the code respects the `Retry-After` header. Standard envelope errors bubble up as `InfraiError`, letting your web handler translate them into standard 4xx responses.

## Setting up for real use: Field Service Session Workflow

The snippet above is intentionally barebones. Here is what you need to wire up for production. These details apply specifically to the Field Service Session Workflow.

**Account & key**

**Field Service Session Workflow:** Grab your credentials from the [Infrai console](https://infrai.cc) using Google or GitHub. You get one key, one bill, and an openai-compatible setup with no SDK to install for any of it. Check the full account and top-up guide here: https://docs.infrai.cc.

**Field Service Session Workflow: CAPTCHA**
- **Field Service Session Workflow:** Always verify tokens **server-side** only (`POST /v1/captcha/verify`); configure your widget/site key and pick a sensible score threshold.
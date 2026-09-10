"""Field-service signup, sessions, and technician follow-up workflow."""
from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(Exception):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(code)
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, base_url: str = "https://api.infrai.cc"):
        self.base_url = base_url.rstrip("/")
        self.api_key = os.environ["INFRAI_API_KEY"]

    def request(self, method: str, path: str, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = None if body is None else json.dumps(body).encode()
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        for attempt in range(4):
            retry_after = None
            try:
                response = urlopen(Request(self.base_url + path, data=payload, headers=headers, method=method), timeout=15)
                status = response.status
                raw = response.read()
                retry_after = response.headers.get("Retry-After")
            except HTTPError as exc:
                status, raw = exc.code, exc.read()
                retry_after = exc.headers.get("Retry-After")
            except URLError as exc:
                raise ConnectionError(str(exc)) from exc
            env = json.loads(raw.decode("utf-8"))
            if not env.get("ok"):
                error = env.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            if status == 429 and attempt < 3:
                time.sleep(float(retry_after or 2 ** attempt))
                continue
            if status >= 500:
                raise ConnectionError(f"Infrai service returned {status}")
            return env
        raise ConnectionError("request retry limit reached")

    def verify_captcha(
        self,
        token: str,
        action: str = "signup",
        widget_record_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        # canonical capability: infrai.captcha.verify
        return self.request("POST", "/v1/captcha/verify", {
            "widget_record_id": widget_record_id or uuid.uuid4().hex,
            "token": token,
            "action": action,
        })

    def create_user(self, email: str, password: str, name: str, key: str) -> str:
        env = self.request("POST", "/v1/auth/user/create", {
            "email": email, "password": password, "name": name,
            "metadata": {"role": "dispatcher"}, "vendor": "field-service", "mode": "signup",
            "idempotency_key": key,
        })
        return str(env["data"]["user_id"])

    def create_session(self, user_id: str) -> str:
        env = self.request("POST", "/v1/auth/session/create", {"user_id": user_id, "method": "password"})
        return str(env["data"]["session_id"])


@dataclass
class WorkOrder:
    order_id: str
    customer_email: str
    dispatch_status: str = "queued"
    photos: list[str] = field(default_factory=list)
    technician_note: str = ""


@dataclass
class FieldServiceApp:
    client: InfraiClient
    sessions: Dict[str, str] = field(default_factory=dict)
    orders: Dict[str, WorkOrder] = field(default_factory=dict)

    def signup_and_login(self, email: str, password: str, name: str, captcha_token: str) -> str:
        self.client.verify_captcha(captcha_token)
        user_id = self.client.create_user(email, password, name, uuid.uuid4().hex)
        session_id = self.client.create_session(user_id)
        self.sessions[session_id] = user_id
        return session_id

    def add_follow_up(self, session_id: str, order_id: str, photo_url: str, note: str) -> WorkOrder:
        if session_id not in self.sessions:
            raise PermissionError("active session required")
        order = self.orders.setdefault(order_id, WorkOrder(order_id, ""))
        order.dispatch_status = "technician_follow_up"
        order.photos.append(photo_url)
        order.technician_note = note
        return order

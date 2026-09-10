from src.field_service import FieldServiceApp, WorkOrder


class FakeClient:
    def verify_captcha(self, token):
        assert token == "captcha-ok"
        return {"ok": True}

    def create_user(self, email, password, name, key):
        return "user-42"

    def create_session(self, user_id):
        assert user_id == "user-42"
        return "session-42"


def test_follow_up_moves_order_to_technician_state():
    app = FieldServiceApp(FakeClient())
    session = app.signup_and_login("dispatch@example.com", "secret", "Dispatch", "captcha-ok")
    order = app.add_follow_up(session, "WO-17", "https://photos.example/wo-17.jpg", "Replaced the pump")
    assert order == WorkOrder("WO-17", "", "technician_follow_up", ["https://photos.example/wo-17.jpg"], "Replaced the pump")

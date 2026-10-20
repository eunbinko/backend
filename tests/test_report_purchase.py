from app.core.config import settings
from app.services.portone import PortOneConfigurationError, require_portone_settings


def test_missing_portone_settings_fail_clearly(monkeypatch):
    monkeypatch.setattr(settings, "PORTONE_STORE_ID", "")
    monkeypatch.setattr(settings, "PORTONE_TOSSPAYMENTS_CHANNEL_KEY", "")
    monkeypatch.setattr(settings, "PORTONE_API_SECRET", "")
    try:
        require_portone_settings()
    except PortOneConfigurationError as error:
        assert "PORTONE_STORE_ID" in str(error)
    else:
        raise AssertionError("missing configuration should fail")


def test_report_order_creation_requires_login_and_handles_missing_settings(client):
    assert client.post("/esg/reports/1/orders", json={"amount_krw": 1}).status_code == 401
    assert client.post("/user/signup", json={
        "email": "buyer@example.com", "password": "very-secret", "name": "buyer",
    }).status_code == 201
    assert client.post("/user/login", json={"email": "buyer@example.com", "password": "very-secret"}).status_code == 200
    response = client.post("/esg/reports/1/orders", json={"amount_krw": 1})
    assert response.status_code == 503


def test_order_amount_is_server_calculated_and_completion_requires_verified_paid_result(client, monkeypatch):
    from app.core.config import settings
    from app.models.report_order import ReportOrder
    from app.services import portone

    monkeypatch.setattr(settings, "PORTONE_STORE_ID", "store-test")
    monkeypatch.setattr(settings, "PORTONE_TOSSPAYMENTS_CHANNEL_KEY", "channel-test")
    monkeypatch.setattr(settings, "PORTONE_API_SECRET", "server-only-test-secret")
    client.post("/user/signup", json={"email": "buyer2@example.com", "password": "very-secret", "name": "buyer"})
    client.post("/user/login", json={"email": "buyer2@example.com", "password": "very-secret"})

    # Seeded 삼성전자 PDF has verified 87-page metadata; client-sent amount is ignored.
    response = client.post("/esg/reports/1/orders", json={"amount_krw": 999999, "user_id": 999})
    assert response.status_code == 200
    order = response.json()["result"]
    assert order["amount_krw"] == 1000
    assert order["currency"] == "KRW"

    monkeypatch.setattr(portone, "get_portone_payment", lambda payment_id: {
        "id": payment_id, "status": "PAID", "amount": {"total": 1000, "currency": "KRW"},
    })
    complete = client.post(f"/esg/orders/{order['payment_id']}/complete", json={})
    assert complete.status_code == 200
    detail = client.get("/esg/reports/1").json()["result"]
    assert detail["purchased"] is True
    assert detail["access_url"].startswith("https://www.samsung.com/")

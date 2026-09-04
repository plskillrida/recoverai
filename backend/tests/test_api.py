import os
import sys
import pytest
from fastapi.testclient import TestClient

# Make app importable
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)

from app.main import app

client = TestClient(app)


# =========================================================
# AUTHENTICATION TESTS
# =========================================================

def test_01_login_missing_username():
    response = client.post(
        "/auth/login",
        json={
            "password": "wrong"
        }
    )

    assert response.status_code == 400


def test_02_login_missing_password():
    response = client.post(
        "/auth/login",
        json={
            "username": "admin"
        }
    )

    assert response.status_code == 400


def test_03_login_wrong_username():
    response = client.post(
        "/auth/login",
        json={
            "username": "does_not_exist",
            "password": "wrong"
        }
    )

    assert response.status_code == 401


def test_04_login_wrong_password():
    response = client.post(
        "/auth/login",
        json={
            "username": "admin",
            "password": "wrong_password"
        }
    )

    assert response.status_code == 401


def test_05_protected_endpoint_without_token():
    response = client.get(
        "/dashboard/summary"
    )

    assert response.status_code == 401


def test_06_me_without_token():
    response = client.get(
        "/auth/me"
    )

    assert response.status_code == 401


# =========================================================
# BASIC API TESTS
# =========================================================

def test_07_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["name"] == "RecoverAI"


def test_08_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_09_invalid_transaction():
    response = client.get(
        "/dashboard/transactions/nonexistent_payment"
    )

    assert response.status_code in [401, 404]


def test_10_invalid_recovery_verification():
    response = client.get(
        "/recovery/verify/nonexistent_payment"
    )

    assert response.status_code in [401, 404]


# =========================================================
# WEBHOOK TESTS
# =========================================================

def test_11_webhook_missing_signature():
    response = client.post(
        "/webhooks/razorpay",
        json={
            "event": "payment_link.paid",
            "payload": {}
        }
    )

    assert response.status_code in [400, 401]


def test_12_webhook_invalid_signature():
    response = client.post(
        "/webhooks/razorpay",
        headers={
            "X-Razorpay-Signature": "invalid_signature"
        },
        json={
            "event": "payment_link.paid",
            "payload": {}
        }
    )

    assert response.status_code in [400, 401]


def test_13_webhook_malformed_json():
    response = client.post(
        "/webhooks/razorpay",
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": "invalid"
        },
        content=b"not valid json"
    )

    assert response.status_code in [400, 401]


# =========================================================
# DASHBOARD AUTH TESTS
# =========================================================

def test_14_dashboard_summary_requires_auth():
    response = client.get(
        "/dashboard/summary"
    )

    assert response.status_code == 401


def test_15_dashboard_transactions_requires_auth():
    response = client.get(
        "/dashboard/transactions"
    )

    assert response.status_code == 401


def test_16_recoveries_requires_auth():
    response = client.get(
        "/recoveries"
    )

    assert response.status_code == 401


def test_17_recovery_verification_requires_auth():
    response = client.get(
        "/recovery/verify/pay_test_005"
    )

    assert response.status_code == 401


# =========================================================
# AUTHENTICATED API TESTS
# =========================================================

@pytest.fixture
def auth_headers():

    username = os.getenv(
        "RECOVERAI_ADMIN_USERNAME",
        "admin"
    )

    password = os.getenv(
        "RECOVERAI_ADMIN_PASSWORD"
    )

    if not password:
        pytest.skip(
            "RECOVERAI_ADMIN_PASSWORD not configured"
        )

    response = client.post(
        "/auth/login",
        json={
            "username": username,
            "password": password
        }
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }


def test_18_authenticated_me(auth_headers):

    response = client.get(
        "/auth/me",
        headers=auth_headers
    )

    assert response.status_code == 200
    assert response.json()["authenticated"] is True


def test_19_dashboard_summary(auth_headers):

    response = client.get(
        "/dashboard/summary",
        headers=auth_headers
    )

    assert response.status_code == 200

    data = response.json()

    assert "revenue_at_risk" in data
    assert "revenue_recovered" in data
    assert "recovery_rate" in data


def test_20_dashboard_transactions(auth_headers):

    response = client.get(
        "/dashboard/transactions",
        headers=auth_headers
    )

    assert response.status_code == 200

    assert isinstance(
        response.json(),
        list
    )


def test_21_recoveries(auth_headers):

    response = client.get(
        "/recoveries",
        headers=auth_headers
    )

    assert response.status_code == 200

    assert isinstance(
        response.json(),
        list
    )


# =========================================================
# TRANSACTION TESTS
# =========================================================

def test_22_existing_transaction(auth_headers):

    response = client.get(
        "/dashboard/transactions/pay_test_005",
        headers=auth_headers
    )

    assert response.status_code in [200, 404]


def test_23_missing_transaction(auth_headers):

    response = client.get(
        "/dashboard/transactions/does_not_exist",
        headers=auth_headers
    )

    assert response.status_code == 404


# =========================================================
# RECOVERY TESTS
# =========================================================

def test_24_existing_recovery_verification(auth_headers):

    response = client.get(
        "/recovery/verify/pay_test_005",
        headers=auth_headers
    )

    assert response.status_code == 200

    data = response.json()

    assert data["payment_id"] == "pay_test_005"


def test_25_recovery_verification_missing_payment(
    auth_headers
):

    response = client.get(
        "/recovery/verify/does_not_exist",
        headers=auth_headers
    )

    assert response.status_code == 404


# =========================================================
# SECURITY / INVALID TOKEN TESTS
# =========================================================

def test_26_invalid_token():

    response = client.get(
        "/dashboard/summary",
        headers={
            "Authorization":
                "Bearer invalid.token.here"
        }
    )

    assert response.status_code == 401


def test_27_malformed_authorization():

    response = client.get(
        "/dashboard/summary",
        headers={
            "Authorization": "InvalidToken"
        }
    )

    assert response.status_code == 401


# =========================================================
# PUBLIC ENDPOINT TESTS
# =========================================================

def test_28_docs_public():

    response = client.get("/docs")

    assert response.status_code == 200


def test_29_openapi_public():

    response = client.get("/openapi.json")

    assert response.status_code == 200


def test_30_webhook_is_public():

    response = client.post(
        "/webhooks/razorpay",
        headers={
            "X-Razorpay-Signature": "invalid"
        },
        json={}
    )

    # Important: webhook should not require JWT.
    # It should instead reject based on Razorpay signature.
    assert response.status_code != 401
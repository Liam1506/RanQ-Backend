"""
Integration tests for auth router endpoints (/api/auth/*).

All Supabase DB calls are mocked via unittest.mock.patch so no real
network connection is required.
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resp(data):
    """Return a mock object whose .data attribute is *data*."""
    m = MagicMock()
    m.data = data
    return m


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client_app():
    """
    Yield a FastAPI TestClient with the real app.
    The Supabase client (db.connect.db) is replaced with a MagicMock so no
    real DB calls are made.
    """
    mock_db = MagicMock()

    with patch("db.connect.db", mock_db), \
         patch("auth.router.db", mock_db), \
         patch("auth.authDb.auth_db", side_effect=lambda c, uid: uid):

        from main import app
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c, mock_db


# ---------------------------------------------------------------------------
# POST /api/auth/register
# ---------------------------------------------------------------------------

class TestRegister:

    def test_register_success(self, client_app):
        client, mock_db = client_app
        new_user = {
            "id": "uid-1", "username": "alice", "email": "alice@example.com",
            "verified": False, "admin": False,
        }

        # get_user_by_username (duplicate check) → not found
        # get_user_by_email (duplicate check)    → not found
        # insert_user internal calls             → irrelevant (patched below)
        # get_user_by_username (fetch after insert) → found
        with patch("auth.router.get_user_by_username", side_effect=[None, new_user]), \
             patch("auth.router.get_user_by_email", return_value=None), \
             patch("auth.router.insert_user", return_value="uid-1"):

            resp = client.post("/api/auth/register", json={
                "username": "alice",
                "email": "alice@example.com",
                "password": "s3cr3t",
            })

        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "alice"
        assert data["id"] == "uid-1"

    def test_register_username_taken(self, client_app):
        client, _ = client_app
        existing = {"id": "x", "username": "alice", "email": "a@b.com",
                    "password": "h", "verified": True, "admin": False}

        with patch("auth.router.get_user_by_username", return_value=existing):
            resp = client.post("/api/auth/register", json={
                "username": "alice", "email": "new@example.com", "password": "pw",
            })

        assert resp.status_code == 400
        assert "Username" in resp.json()["detail"]

    def test_register_email_taken(self, client_app):
        client, _ = client_app
        existing = {"id": "x", "username": "other", "email": "taken@b.com",
                    "password": "h", "verified": True, "admin": False}

        with patch("auth.router.get_user_by_username", return_value=None), \
             patch("auth.router.get_user_by_email", return_value=existing):
            resp = client.post("/api/auth/register", json={
                "username": "bob", "email": "taken@b.com", "password": "pw",
            })

        assert resp.status_code == 400
        assert "Email" in resp.json()["detail"]

    def test_register_invalid_email(self, client_app):
        client, _ = client_app
        resp = client.post("/api/auth/register", json={
            "username": "bob", "email": "not-an-email", "password": "pw",
        })
        assert resp.status_code == 422  # pydantic validation error


# ---------------------------------------------------------------------------
# POST /api/auth/login
# ---------------------------------------------------------------------------

class TestLogin:

    def test_login_success(self, client_app):
        client, _ = client_app
        from auth.router import hash_password

        hashed = hash_password("correct")
        user = {"id": "uid-1", "username": "alice", "email": "a@b.com",
                 "password": hashed, "verified": True, "admin": False}

        with patch("auth.router.get_user_by_username", return_value=user), \
             patch("auth.router.auth_db", return_value="uid-1"):
            resp = client.post("/api/auth/login", json={
                "username": "alice", "password": "correct",
            })

        assert resp.status_code == 200

    def test_login_wrong_password(self, client_app):
        client, _ = client_app
        from auth.router import hash_password

        hashed = hash_password("correct")
        user = {"id": "uid-1", "username": "alice", "email": "a@b.com",
                 "password": hashed, "verified": True, "admin": False}

        with patch("auth.router.get_user_by_username", return_value=user):
            resp = client.post("/api/auth/login", json={
                "username": "alice", "password": "wrong",
            })

        assert resp.status_code == 401

    def test_login_unknown_user(self, client_app):
        client, _ = client_app

        with patch("auth.router.get_user_by_username", return_value=None):
            resp = client.post("/api/auth/login", json={
                "username": "nobody", "password": "pw",
            })

        assert resp.status_code == 401

    def test_login_missing_fields(self, client_app):
        client, _ = client_app
        resp = client.post("/api/auth/login", json={"username": "alice"})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/auth/status
# ---------------------------------------------------------------------------

class TestStatus:

    def test_status_verified_user(self, client_app):
        client, _ = client_app
        user = {"id": "uid-1", "username": "alice", "email": "a@b.com",
                 "verified": True, "admin": False}

        with patch("auth.router.get_user_by_id", return_value=user):
            resp = client.get("/api/auth/status", params={"userId": "uid-1"})

        assert resp.status_code == 200
        assert resp.json() == {"verified": True}

    def test_status_unverified_user(self, client_app):
        client, _ = client_app
        user = {"id": "uid-1", "username": "alice", "email": "a@b.com",
                 "verified": False, "admin": False}

        with patch("auth.router.get_user_by_id", return_value=user):
            resp = client.get("/api/auth/status", params={"userId": "uid-1"})

        assert resp.status_code == 200
        assert resp.json() == {"verified": False}

    def test_status_user_not_found(self, client_app):
        client, _ = client_app

        with patch("auth.router.get_user_by_id", return_value=None):
            resp = client.get("/api/auth/status", params={"userId": "ghost"})

        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/auth/verify
# ---------------------------------------------------------------------------

class TestVerify:

    def test_verify_success(self, client_app):
        client, _ = client_app

        with patch("auth.router.verify_user", return_value=True):
            resp = client.get("/api/auth/verify", params={
                "userId": "uid-1", "verifyId": "some-hash",
            })

        assert resp.status_code == 200
        assert "verified" in resp.text.lower()

    def test_verify_invalid_link(self, client_app):
        client, _ = client_app

        with patch("auth.router.verify_user", return_value=False):
            resp = client.get("/api/auth/verify", params={
                "userId": "uid-1", "verifyId": "bad-hash",
            })

        assert resp.status_code == 400

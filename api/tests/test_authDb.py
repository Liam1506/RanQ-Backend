import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException


def make_response(data):
    r = MagicMock()
    r.data = data
    return r


@pytest.fixture
def client():
    return MagicMock()


# --- auth_db ---

def test_auth_db_verified_user(client):
    from auth.authDb import auth_db
    client.table.return_value.select.return_value.eq.return_value.execute.return_value = make_response(
        [{"verified": True, "admin": False}]
    )
    result = auth_db(client, "u1")
    assert result == "u1"


def test_auth_db_unverified_user(client):
    from auth.authDb import auth_db
    client.table.return_value.select.return_value.eq.return_value.execute.return_value = make_response(
        [{"verified": False, "admin": False}]
    )
    with pytest.raises(HTTPException) as exc:
        auth_db(client, "u1")
    assert exc.value.status_code == 402


def test_auth_db_no_user(client):
    from auth.authDb import auth_db
    client.table.return_value.select.return_value.eq.return_value.execute.return_value = make_response([])
    with pytest.raises(HTTPException) as exc:
        auth_db(client, "u1")
    assert exc.value.status_code == 401


def test_auth_db_db_exception(client):
    from auth.authDb import auth_db
    client.table.return_value.select.return_value.eq.return_value.execute.side_effect = Exception("DB down")
    with pytest.raises(HTTPException) as exc:
        auth_db(client, "u1")
    assert exc.value.status_code == 401


# --- auth_db_admin ---

def test_auth_db_admin_verified_admin(client):
    from auth.authDb import auth_db_admin
    client.table.return_value.select.return_value.eq.return_value.execute.return_value = make_response(
        [{"verified": True, "admin": True}]
    )
    result = auth_db_admin(client, "admin1")
    assert result == "admin1"


def test_auth_db_admin_verified_non_admin(client):
    from auth.authDb import auth_db_admin
    client.table.return_value.select.return_value.eq.return_value.execute.return_value = make_response(
        [{"verified": True, "admin": False}]
    )
    with pytest.raises(HTTPException) as exc:
        auth_db_admin(client, "u1")
    assert exc.value.status_code == 402


def test_auth_db_admin_unverified(client):
    from auth.authDb import auth_db_admin
    client.table.return_value.select.return_value.eq.return_value.execute.return_value = make_response(
        [{"verified": False, "admin": True}]
    )
    with pytest.raises(HTTPException) as exc:
        auth_db_admin(client, "u1")
    assert exc.value.status_code == 402


def test_auth_db_admin_no_user(client):
    from auth.authDb import auth_db_admin
    client.table.return_value.select.return_value.eq.return_value.execute.return_value = make_response([])
    with pytest.raises(HTTPException) as exc:
        auth_db_admin(client, "u1")
    assert exc.value.status_code == 401

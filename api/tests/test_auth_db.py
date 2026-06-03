import pytest
from unittest.mock import MagicMock, patch


def make_response(data):
    r = MagicMock()
    r.data = data
    return r


@pytest.fixture
def client():
    return MagicMock()


# --- get_user_by_id ---

def test_get_user_by_id_found(client):
    from auth.db import get_user_by_id
    user = {"id": "u1", "username": "alice", "email": "a@b.com", "verified": True, "admin": False}
    client.table.return_value.select.return_value.eq.return_value.execute.return_value = make_response([user])
    result = get_user_by_id(client, "u1")
    assert result == user


def test_get_user_by_id_not_found(client):
    from auth.db import get_user_by_id
    client.table.return_value.select.return_value.eq.return_value.execute.return_value = make_response([])
    result = get_user_by_id(client, "missing")
    assert result is None


# --- get_user_by_username ---

def test_get_user_by_username_found(client):
    from auth.db import get_user_by_username
    user = {"id": "u1", "username": "alice"}
    client.table.return_value.select.return_value.eq.return_value.execute.return_value = make_response([user])
    result = get_user_by_username(client, "alice")
    assert result == user


def test_get_user_by_username_not_found(client):
    from auth.db import get_user_by_username
    client.table.return_value.select.return_value.eq.return_value.execute.return_value = make_response([])
    result = get_user_by_username(client, "nobody")
    assert result is None


# --- get_user_by_email ---

def test_get_user_by_email_found(client):
    from auth.db import get_user_by_email
    user = {"id": "u1", "email": "a@b.com"}
    client.table.return_value.select.return_value.eq.return_value.execute.return_value = make_response([user])
    result = get_user_by_email(client, "a@b.com")
    assert result == user


def test_get_user_by_email_not_found(client):
    from auth.db import get_user_by_email
    client.table.return_value.select.return_value.eq.return_value.execute.return_value = make_response([])
    result = get_user_by_email(client, "nope@x.com")
    assert result is None


# --- insert_user ---

def test_insert_user_with_verification(client):
    from auth.db import insert_user
    client.table.return_value.insert.return_value.execute.return_value = make_response([])

    with patch("auth.db.send_verify_mail") as mock_mail, \
         patch.dict("os.environ", {"SKIP_EMAIL_VERIFICATION": "false"}):
        user_id = insert_user(client, "alice", "a@b.com", "hashed")
        assert isinstance(user_id, str)
        mock_mail.assert_called_once()


def test_insert_user_skip_verification(client):
    from auth.db import insert_user
    client.table.return_value.insert.return_value.execute.return_value = make_response([])

    with patch("auth.db.send_verify_mail") as mock_mail, \
         patch.dict("os.environ", {"SKIP_EMAIL_VERIFICATION": "true"}):
        user_id = insert_user(client, "bob", "b@c.com", "hashed")
        assert isinstance(user_id, str)
        mock_mail.assert_not_called()


# --- verify_user ---

def test_verify_user_success(client):
    from auth.db import verify_user
    mock_chain = MagicMock()
    mock_chain.execute.return_value = make_response([{"id": "u1"}])
    client.table.return_value.select.return_value.eq.return_value.eq.return_value = mock_chain
    client.table.return_value.update.return_value.eq.return_value.execute.return_value = make_response([])
    client.table.return_value.delete.return_value.eq.return_value.execute.return_value = make_response([])

    result = verify_user(client, "u1", "verify-hash")
    assert result is True


def test_verify_user_invalid_token(client):
    from auth.db import verify_user
    mock_chain = MagicMock()
    mock_chain.execute.return_value = make_response([])
    client.table.return_value.select.return_value.eq.return_value.eq.return_value = mock_chain

    result = verify_user(client, "u1", "wrong-hash")
    assert result is False

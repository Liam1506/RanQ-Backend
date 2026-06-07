import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from main import app
from db.connect import db
from auth.authDb import auth_db, auth_db_admin


@pytest.fixture
def mock_db():
    return MagicMock()


def _make_response(data):
    r = MagicMock()
    r.data = data
    return r


@pytest.fixture
def make_response():
    return _make_response


@pytest.fixture
def client(mock_db):
    def override_auth_user():
        return "test-user-id"

    def override_auth_admin():
        return "test-admin-id"

    from auth.authUser import auth_user, auth_admin
    app.dependency_overrides[auth_user] = override_auth_user
    app.dependency_overrides[auth_admin] = override_auth_admin

    import db.connect as db_module
    db_module.db = mock_db

    with TestClient(app) as c:
        yield c, mock_db

    app.dependency_overrides.clear()

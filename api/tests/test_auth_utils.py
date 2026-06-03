import pytest
from unittest.mock import MagicMock, patch

from auth.router import hash_password, verify_password


def test_hash_password_returns_string():
    hashed = hash_password("secret")
    assert isinstance(hashed, str)
    assert hashed != "secret"


def test_hash_password_different_each_time():
    h1 = hash_password("secret")
    h2 = hash_password("secret")
    assert h1 != h2


def test_verify_password_correct():
    hashed = hash_password("mypassword")
    assert verify_password("mypassword", hashed) is True


def test_verify_password_wrong():
    hashed = hash_password("mypassword")
    assert verify_password("wrongpassword", hashed) is False

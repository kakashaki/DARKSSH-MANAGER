"""Tests for env/env.py environment loader."""
import importlib
import os
import sys

import pytest

for key in ("API_ID", "API_HASH", "STRING_SESSION", "BOT_TOKEN", "BOT_USERNAME"):
    os.environ.setdefault(key, "placeholder")

import env.env as env_module  # noqa: E402


@pytest.fixture(autouse=True)
def reset_env_module():
    """Reload env.env before each test so import-time env lookups are fresh."""
    yield
    importlib.reload(env_module)


def test_env_variables_loaded(monkeypatch):
    """env.env should expose the required environment variables as globals."""
    monkeypatch.setenv("API_ID", "12345")
    monkeypatch.setenv("API_HASH", "abc123")
    monkeypatch.setenv("STRING_SESSION", "session-string")
    monkeypatch.setenv("BOT_TOKEN", "bot-token")
    monkeypatch.setenv("BOT_USERNAME", "testbot")
    monkeypatch.setenv("BANNER_NAME", "TestBanner")
    monkeypatch.setenv("ADMINS", "admin1,admin2")
    monkeypatch.setenv("SSH_IP", "192.168.1.1")
    monkeypatch.setenv("SSH_USERNAME", "root")
    monkeypatch.setenv("SSH_PASS", "secret")

    importlib.reload(env_module)

    assert env_module.api_id == "12345"
    assert env_module.api_hash == "abc123"
    assert env_module.string == "session-string"
    assert env_module.bot_token == "bot-token"
    assert env_module.bot_name == "testbot"
    assert env_module.BANNER_NAME == "TestBanner"
    assert env_module.LIST_OF_ADMINS == "admin1,admin2"
    assert env_module.host == "192.168.1.1"
    assert env_module.username == "root"
    assert env_module.password == "secret"


def test_env_optional_defaults(monkeypatch):
    """Optional environment variables should default to None when not set."""
    monkeypatch.setenv("API_ID", "12345")
    monkeypatch.setenv("API_HASH", "abc123")
    monkeypatch.setenv("STRING_SESSION", "session-string")
    monkeypatch.setenv("BOT_TOKEN", "bot-token")
    monkeypatch.setenv("BOT_USERNAME", "testbot")
    monkeypatch.delenv("BANNER_NAME", raising=False)
    monkeypatch.delenv("ADMINS", raising=False)
    monkeypatch.delenv("SSH_IP", raising=False)
    monkeypatch.delenv("SSH_USERNAME", raising=False)
    monkeypatch.delenv("SSH_PASS", raising=False)

    importlib.reload(env_module)

    assert env_module.api_id == "12345"
    assert env_module.BANNER_NAME is None
    assert env_module.LIST_OF_ADMINS is None
    assert env_module.host is None
    assert env_module.username is None
    assert env_module.password is None


def test_env_missing_required_raises(monkeypatch):
    """env.env should raise KeyError if required variables are missing."""
    for key in ("API_ID", "API_HASH", "STRING_SESSION", "BOT_TOKEN", "BOT_USERNAME"):
        monkeypatch.delenv(key, raising=False)

    with pytest.raises(KeyError):
        importlib.reload(env_module)

"""Tests for session/ssgen.py helper functions."""
import builtins
import sys
import time

import pytest

import session.ssgen as ssgen


def test_clear_screen_posix(monkeypatch):
    """clear_screen should run `clear` on POSIX systems."""
    calls = []
    monkeypatch.setattr(ssgen.os, "name", "posix")
    monkeypatch.setattr(ssgen.os, "system", lambda cmd: calls.append(cmd))
    ssgen.clear_screen()
    assert calls == ["clear"]


def test_clear_screen_windows(monkeypatch):
    """clear_screen should run `cls` on Windows."""
    calls = []
    monkeypatch.setattr(ssgen.os, "name", "nt")
    monkeypatch.setattr(ssgen.os, "system", lambda cmd: calls.append(cmd))
    ssgen.clear_screen()
    assert calls == ["cls"]


def test_spinner(monkeypatch):
    """spinner should print a progress message and sleep 24 times."""
    printed = []
    sleeps = []

    monkeypatch.setattr(builtins, "print", lambda *args, **kwargs: printed.append((args, kwargs)))
    monkeypatch.setattr(ssgen, "sleep", lambda seconds: sleeps.append(seconds))

    ssgen.spinner()

    assert any("Telethon" in str(args) for args, _ in printed)
    assert len(sleeps) == 24  # 3 iterations * 8 frames
    for duration in sleeps:
        assert duration == 0.1


def test_get_api_id_and_hash_valid(monkeypatch):
    """get_api_id_and_hash should return integer API_ID and string API_HASH."""
    monkeypatch.setattr(builtins, "input", lambda prompt: {
        "Please enter your API ID: ": "12345",
        "Please enter your API HASH: ": "abc123",
    }[prompt])
    api_id, api_hash = ssgen.get_api_id_and_hash()
    assert api_id == 12345
    assert api_hash == "abc123"


def test_get_api_id_and_hash_invalid_exits(monkeypatch):
    """get_api_id_and_hash should exit on non-integer API_ID."""
    monkeypatch.setattr(builtins, "input", lambda prompt: "not-a-number")
    with pytest.raises(SystemExit):
        ssgen.get_api_id_and_hash()

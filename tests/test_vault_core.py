"""Tests for _vault_core fallback (pure Python, no Cython needed in test env)."""
from pop_pay.engine._vault_core_fallback import derive_key, is_hardened


def test_fallback_derive_key_returns_none():
    assert derive_key(b"machine", b"user") is None


def test_fallback_not_hardened():
    assert is_hardened() is False

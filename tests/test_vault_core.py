"""Tests for _vault_core fallback (pure Python, no Cython needed in test env)."""
from pop_pay.engine._vault_core_fallback import get_compiled_salt, is_hardened


def test_fallback_returns_none_salt():
    assert get_compiled_salt() is None


def test_fallback_not_hardened():
    assert is_hardened() is False

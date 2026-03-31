# pop_pay/engine/_vault_core_fallback.py
"""Pure-Python fallback when Cython .so is not compiled."""

_COMPILED_SALT = None

def get_compiled_salt():
    return None

def is_hardened():
    return False

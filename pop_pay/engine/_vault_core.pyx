# pop_pay/engine/_vault_core.pyx
# cython: language_level=3
"""
Cython-compiled key derivation core for pop-pay vault.

In PyPI builds: _COMPILED_SALT is replaced with a secret value injected by CI
at build time. The salt NEVER crosses the Python boundary — derive_key() uses
it internally and returns only the derived AES-256 key.

In OSS/source builds: _COMPILED_SALT is None and derive_key() returns None,
signalling vault.py to fall back to the public OSS salt.

Security model:
- An agent with file-read tools sees only encrypted vault.enc (AES-256-GCM).
- An agent with shell execution can call derive_key() but still gets the right
  key only if they supply the correct machine_id + username — which requires
  local access anyway. The compiled salt is never exposed as a Python object.
- Passphrase mode (--passphrase) provides stronger protection: the key is
  derived from the user's passphrase, not machine identity.
"""

# CI build pipeline replaces this placeholder with the secret salt.
# Source builds: _COMPILED_SALT = None → derive_key() returns None → vault.py
# falls back to the public OSS salt.
_COMPILED_SALT = None  # Replaced by CI: b"<SECRET_INJECTED_AT_BUILD_TIME>"


def derive_key(machine_id: bytes, username: bytes):
    """Derive AES-256 key using the compiled-in salt.

    The salt never crosses the Python boundary — it is used only inside this
    Cython function. Returns None if running from OSS source (no compiled salt),
    signalling vault.py to use the public fallback salt instead.
    """
    if _COMPILED_SALT is None:
        return None
    import hashlib
    password = machine_id + b":" + username
    return hashlib.scrypt(password, salt=_COMPILED_SALT, n=2**14, r=8, p=1, dklen=32)


def is_hardened():
    """Return True if this is a PyPI/Cython hardened build (non-None salt)."""
    return _COMPILED_SALT is not None

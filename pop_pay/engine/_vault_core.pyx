# pop_pay/engine/_vault_core.pyx
# cython: language_level=3
"""
Cython-compiled key derivation core for pop-pay vault.

In PyPI builds: the _SALT constant is replaced with a secret value
injected by CI at build time (not present in the GitHub repo).
In OSS/source builds: falls back to the public salt defined in vault.py.

Security note: even in the compiled .so, a determined attacker can call
derive_key() directly from Python. The protection is against casual
source-reading, not against an agent that knows to call this function.
The passphrase mode (--passphrase flag) provides stronger protection.
"""

# CI build pipeline replaces this placeholder with the secret salt.
# Source builds use the public salt from vault.py instead (see fallback in vault.py).
_COMPILED_SALT = None  # Replaced by CI: b"<SECRET_INJECTED_AT_BUILD_TIME>"


def get_compiled_salt():
    """Return the compiled-in salt, or None if running from source."""
    return _COMPILED_SALT


def is_hardened():
    """Return True if this is a PyPI/Cython hardened build (non-None salt)."""
    return _COMPILED_SALT is not None

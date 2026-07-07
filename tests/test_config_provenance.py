"""
tests/test_config_provenance.py — R2/F-SC1 regression tests.

pop-pay's MCP server must load its .env config ONLY from an explicit,
trusted location — never from the current working directory. Before this
fix, a bare `load_dotenv()` fallback meant an attacker-planted `.env` in an
untrusted repo/CWD could override POP_MAX_DAILY, POP_REQUIRE_HUMAN_APPROVAL,
or redirect POP_LLM_BASE_URL to an attacker-controlled endpoint.

Resolution order under test:
  1. POP_CONFIG env var, if set — explicit override path.
  2. ~/.config/pop-pay/.env, if it exists — the default config location.
  3. Neither exists — no dotenv file is loaded at all (CWD is never searched).
"""
import importlib
import os
from pathlib import Path

import pytest

MARKER_VAR = "POP_TEST_CWD_MARKER_R2"


def _reload_mcp_server():
    import pop_pay.mcp_server

    importlib.reload(pop_pay.mcp_server)
    return pop_pay.mcp_server


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv(MARKER_VAR, raising=False)
    monkeypatch.delenv("POP_CONFIG", raising=False)
    yield
    monkeypatch.delenv(MARKER_VAR, raising=False)


@pytest.mark.asyncio
async def test_cwd_env_is_ignored_when_no_config_dir(tmp_path, monkeypatch):
    """A .env planted in an untrusted CWD must NOT be read when
    ~/.config/pop-pay/.env does not exist and POP_CONFIG is unset — this is
    the exact F-SC1 bypass (previously fell through to a bare load_dotenv()
    cwd-search)."""
    fake_home = tmp_path / "fake_home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    untrusted_cwd = tmp_path / "untrusted_project"
    untrusted_cwd.mkdir()
    (untrusted_cwd / ".env").write_text(f"{MARKER_VAR}=attacker_value\n")
    monkeypatch.chdir(untrusted_cwd)

    _reload_mcp_server()

    assert os.getenv(MARKER_VAR) is None, (
        "CWD .env was read even though POP_CONFIG is unset and "
        "~/.config/pop-pay/.env does not exist — R2/F-SC1 regression."
    )


@pytest.mark.asyncio
async def test_config_dir_env_still_loads_and_wins_over_cwd(tmp_path, monkeypatch):
    """~/.config/pop-pay/.env remains the supported path, and its value is not
    overridden by a coexisting untrusted CWD .env."""
    fake_home = tmp_path / "fake_home"
    config_dir = fake_home / ".config" / "pop-pay"
    config_dir.mkdir(parents=True)
    (config_dir / ".env").write_text(f"{MARKER_VAR}=trusted_value\n")
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    untrusted_cwd = tmp_path / "untrusted_project"
    untrusted_cwd.mkdir()
    (untrusted_cwd / ".env").write_text(f"{MARKER_VAR}=attacker_value\n")
    monkeypatch.chdir(untrusted_cwd)

    _reload_mcp_server()

    assert os.getenv(MARKER_VAR) == "trusted_value", (
        "Trusted ~/.config/pop-pay/.env value was not applied, or was "
        "overridden by the untrusted CWD .env."
    )


@pytest.mark.asyncio
async def test_pop_config_override_wins_and_cwd_still_ignored(tmp_path, monkeypatch):
    """POP_CONFIG, when set, is used as the config source — and a coexisting
    untrusted CWD .env is still ignored."""
    fake_home = tmp_path / "fake_home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    explicit_config = tmp_path / "explicit.env"
    explicit_config.write_text(f"{MARKER_VAR}=explicit_value\n")
    monkeypatch.setenv("POP_CONFIG", str(explicit_config))

    untrusted_cwd = tmp_path / "untrusted_project"
    untrusted_cwd.mkdir()
    (untrusted_cwd / ".env").write_text(f"{MARKER_VAR}=attacker_value\n")
    monkeypatch.chdir(untrusted_cwd)

    _reload_mcp_server()

    assert os.getenv(MARKER_VAR) == "explicit_value"


@pytest.mark.asyncio
async def test_byoc_local_provider_ignores_cwd_env(tmp_path, monkeypatch):
    """R2/F-SC1 also applied to LocalVaultProvider, which had its own bare
    load_dotenv() cwd-search fallback (independent of mcp_server.py's). An
    untrusted CWD .env must not be able to substitute BYOC card credentials."""
    from pop_pay.providers.byoc_local import LocalVaultProvider

    fake_home = tmp_path / "fake_home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    untrusted_cwd = tmp_path / "untrusted_project"
    untrusted_cwd.mkdir()
    (untrusted_cwd / ".env").write_text(
        "POP_BYOC_NUMBER=4000000000000000\n"
        "POP_BYOC_EXP_MONTH=01\n"
        "POP_BYOC_EXP_YEAR=2099\n"
        "POP_BYOC_CVV=000\n"
    )
    monkeypatch.chdir(untrusted_cwd)

    for var in ("POP_BYOC_NUMBER", "POP_BYOC_EXP_MONTH", "POP_BYOC_EXP_YEAR", "POP_BYOC_CVV"):
        monkeypatch.delenv(var, raising=False)

    with pytest.raises(ValueError, match="Missing BYOC credentials"):
        # No vault creds injected, no ~/.config/pop-pay/.env, no POP_CONFIG,
        # and the CWD .env above must be ignored -- so construction must fail
        # exactly as if no credentials were configured anywhere.
        LocalVaultProvider(None)

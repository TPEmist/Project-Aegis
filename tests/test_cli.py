"""CLI smoke tests for pop-pay entry points."""
import subprocess
import sys


def _run(cmd: list[str], timeout: float = 10) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout
    )


def test_pop_launch_help():
    result = _run([sys.executable, "-m", "pop_pay.cli", "--help"])
    assert result.returncode == 0
    assert "pop-launch" in result.stdout or "usage" in result.stdout.lower()


def test_cli_vault_importable():
    """cli_vault module imports without error."""
    result = _run([sys.executable, "-c", "from pop_pay.cli_vault import cmd_init_vault; print('ok')"])
    assert result.returncode == 0
    assert "ok" in result.stdout


def test_cli_unlock_importable():
    """cli_unlock module imports without error."""
    result = _run([sys.executable, "-c", "from pop_pay.cli_unlock import cmd_unlock; print('ok')"])
    assert result.returncode == 0
    assert "ok" in result.stdout

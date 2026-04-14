"""pop-pay CLI dispatcher.

Routes subcommands to the appropriate module. Unknown / empty args fall
through to the dashboard (backwards compatibility with the prior
`pop-pay = dashboard.server:main` entry point).
"""

from __future__ import annotations

import sys


def main() -> int:
    argv = sys.argv[1:]
    sub = argv[0] if argv else None

    if sub == "doctor":
        sys.argv = [sys.argv[0]] + argv[1:]
        from pop_pay.cli_doctor import main as doctor_main
        return doctor_main()

    if sub in ("-h", "--help") and len(argv) == 1:
        print(
            "pop-pay — Semantic Payment Guardrail for AI Agents\n\n"
            "Usage: pop-pay <command> [options]\n\n"
            "Commands:\n"
            "  doctor        Diagnose environment and configuration\n"
            "  (no command)  Launch the monitoring dashboard\n"
        )
        return 0

    # Fall through to the dashboard (legacy behavior).
    from dashboard.server import main as dashboard_main
    result = dashboard_main()
    return int(result) if isinstance(result, int) else 0


if __name__ == "__main__":
    sys.exit(main())

# `pop-pay doctor` (Python)

Python-repo parity for the TypeScript `pop-pay doctor` diagnostic. See the
TS repo's [`docs/DOCTOR.md`](../../pop-pay-npm/docs/DOCTOR.md) for full
documentation; this file notes only the Python differences.

## Usage

```
$ pop-pay doctor
$ pop-pay doctor --json
$ pop-pay-doctor          # equivalent direct entry point
$ python -m pop_pay.cli_doctor
```

Exit codes match the TS version: `0` ok / `1` blocker failed / `2` doctor crashed.

## Checks (10 total)

Same check set as TS, with `python_version` (≥3.10) replacing `node_version`:

| id | Purpose | Blocker? |
|---|---|---|
| `python_version` | Python ≥ 3.10 | yes |
| `chromium` | Chrome / Chromium present | yes |
| `cdp_port` | CDP port free | no |
| `config_dir` | `~/.config/pop-pay/` | no |
| `vault` | `vault.enc` present | no |
| `env_vars` | format-only, never logs values | no |
| `policy_config` | JSON array validation | no |
| `layer1_probe` | `pop_pay.engine` loads | yes |
| `layer2_probe` | TCP reachability; no API request sent | no |
| `injector_smoke` | `chrome --version` | no |

## Privacy & safety

Identical guarantees to the TS doctor:
- `env_vars` checks presence + JSON parse; **never reads or emits values**.
- `layer2_probe` is TCP-only; your `POP_LLM_API_KEY` is never transmitted.

## Remediation catalog

`config/doctor-remediation.yaml` in this repo, same flat schema as the TS repo.
Parsed by an inline minimal YAML-lite parser in `pop_pay/cli_doctor.py`
(no runtime `pyyaml` dependency added).

## KNOWN LIMITATIONS

- **Typed-engine-failure classification deferred — intentional, not oversight.** doctor ships with a local error handler and does not depend on the engine error model. The engine-wide Error Model Refactor is on a separate track (currently paused, pending founder decision — see `workspace/projects/pop-pay/redteam-plan-2026-04-13.md`). A post-refactor round 2 will swap doctor's local handler for the typed engine classifier.
- **`cdp_port`**: TCP probe only; cannot identify the owning process.
- **`injector_smoke`**: `--version` only, does not boot a headless page.
- **No CATEGORIES policy checks yet.** Gated on S0.2 B-class decision, arriving in S1.1.

## Entry points

`pyproject.toml`:
```
pop-pay         = "pop_pay.cli_main:main"   # dispatcher: doctor or dashboard
pop-pay-doctor  = "pop_pay.cli_doctor:main" # direct entry
```

The `pop-pay` script falls through to the dashboard when no subcommand is supplied — preserving the prior `pop-pay` UX.

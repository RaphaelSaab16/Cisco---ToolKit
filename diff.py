from __future__ import annotations

import difflib
import os
from pathlib import Path

CONFIGS_DIR = Path("configs")


def _latest_backup(device_name: str) -> Path | None:
    """Return the most recently saved config file for a device."""
    candidates = sorted(CONFIGS_DIR.glob(f"{device_name}_*.cfg"))
    return candidates[-1] if candidates else None


def _second_latest_backup(device_name: str) -> Path | None:
    """Return the second-most-recent backup (used as baseline when none is given)."""
    candidates = sorted(CONFIGS_DIR.glob(f"{device_name}_*.cfg"))
    return candidates[-2] if len(candidates) >= 2 else None


def diff_configs(
    device_name: str,
    baseline_path: str | Path | None = None,
    current_path: str | Path | None = None,
    context_lines: int = 3,
) -> str:
    """
    Compare two configs and return a unified diff string.

    If baseline_path is omitted, the second-latest backup is used.
    If current_path is omitted, the latest backup is used.
    """
    if current_path is None:
        current_path = _latest_backup(device_name)
        if not current_path:
            raise FileNotFoundError(f"No backups found for '{device_name}' in {CONFIGS_DIR}/.")

    if baseline_path is None:
        baseline_path = _second_latest_backup(device_name)
        if not baseline_path:
            raise FileNotFoundError(
                f"Only one backup exists for '{device_name}'. "
                "Provide an explicit --baseline to compare against."
            )

    baseline_text = Path(baseline_path).read_text().splitlines(keepends=True)
    current_text = Path(current_path).read_text().splitlines(keepends=True)

    diff = list(
        difflib.unified_diff(
            baseline_text,
            current_text,
            fromfile=str(baseline_path),
            tofile=str(current_path),
            n=context_lines,
        )
    )

    return "".join(diff) if diff else ""


def print_diff(device_name: str, baseline_path: str | Path | None = None) -> None:
    """Print a coloured unified diff to stdout."""
    try:
        result = diff_configs(device_name, baseline_path=baseline_path)
    except FileNotFoundError as exc:
        print(f"[diff] ERROR — {exc}")
        return

    if not result:
        print(f"[diff] No differences found for '{device_name}'.")
        return

    # Colour output when stdout is a terminal
    use_colour = os.isatty(1)
    for line in result.splitlines():
        if use_colour:
            if line.startswith("+") and not line.startswith("+++"):
                print(f"\033[32m{line}\033[0m")  # green
            elif line.startswith("-") and not line.startswith("---"):
                print(f"\033[31m{line}\033[0m")  # red
            elif line.startswith("@"):
                print(f"\033[36m{line}\033[0m")  # cyan
            else:
                print(line)
        else:
            print(line)

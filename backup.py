from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path

from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException

CONFIGS_DIR = Path("configs")


def _resolve_password(raw: str) -> str:
    """Expand ${ENV_VAR} references in password fields."""
    match = re.fullmatch(r"\$\{(\w+)\}", raw.strip())
    if match:
        value = os.environ.get(match.group(1))
        if not value:
            raise EnvironmentError(f"Environment variable '{match.group(1)}' is not set.")
        return value
    return raw


def _connect(device: dict) -> ConnectHandler:
    return ConnectHandler(
        device_type=device["device_type"],
        host=device["host"],
        username=device["username"],
        password=_resolve_password(device["password"]),
    )


def backup_device(device: dict) -> Path:
    """Pull running-config from a single device and save it to configs/."""
    name = device["name"]
    print(f"[backup] Connecting to {name} ({device['host']})...")

    try:
        conn = _connect(device)
    except NetmikoAuthenticationException:
        raise RuntimeError(f"Authentication failed for {name}.")
    except NetmikoTimeoutException:
        raise RuntimeError(f"Connection timed out for {name} ({device['host']}).")

    config = conn.send_command("show running-config")
    conn.disconnect()

    CONFIGS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_path = CONFIGS_DIR / f"{name}_{timestamp}.cfg"
    output_path.write_text(config)

    print(f"[backup] Saved {name} config → {output_path}")
    return output_path


def backup_all(devices: list) -> list[Path]:
    """Backup every device in the inventory. Returns list of saved paths."""
    results = []
    errors = []

    for device in devices:
        try:
            path = backup_device(device)
            results.append(path)
        except (RuntimeError, EnvironmentError) as exc:
            print(f"[backup] ERROR — {exc}")
            errors.append(device["name"])

    if errors:
        print(f"[backup] Failed devices: {', '.join(errors)}")
    return results

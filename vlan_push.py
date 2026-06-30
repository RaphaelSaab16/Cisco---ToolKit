from __future__ import annotations

import os
import re
from pathlib import Path

import yaml


def _resolve_password(raw: str) -> str:
    match = re.fullmatch(r"\$\{(\w+)\}", raw.strip())
    if match:
        value = os.environ.get(match.group(1))
        if not value:
            raise EnvironmentError(f"Environment variable '{match.group(1)}' is not set.")
        return value
    return raw


def _build_vlan_commands(vlan: dict) -> list[str]:
    """Return IOS config commands for a single VLAN entry."""
    vlan_id = str(vlan["id"])
    commands = [f"vlan {vlan_id}"]

    if vlan.get("name"):
        commands.append(f" name {vlan['name']}")

    commands.append("exit")
    return commands


def push_vlans(switches_yaml: str | Path, dry_run: bool = False) -> None:
    """
    Push VLANs defined in a YAML file to all listed switches.

    Expected YAML format:
        vlans:
          - id: 10
            name: CORP_DATA
          - id: 20
            name: CORP_VOICE
        switches:
          - name: access-switch-1
            host: 192.168.1.11
            username: admin
            password: ${SW_PASS}
            device_type: cisco_ios
    """
    data = yaml.safe_load(Path(switches_yaml).read_text())
    vlans: list[dict] = data.get("vlans", [])
    switches: list[dict] = data.get("switches", [])

    if not vlans:
        print("[vlan_push] No VLANs defined in the file.")
        return
    if not switches:
        print("[vlan_push] No switches defined in the file.")
        return

    all_commands: list[str] = ["configure terminal"]
    for vlan in vlans:
        all_commands.extend(_build_vlan_commands(vlan))
    all_commands.append("end")
    all_commands.append("write memory")

    if dry_run:
        print("[vlan_push] Dry-run — commands that would be sent:")
        for cmd in all_commands:
            print(f"  {cmd}")
        return

    from netmiko import ConnectHandler, NetmikoAuthenticationException, NetmikoTimeoutException

    for switch in switches:
        name = switch["name"]
        print(f"[vlan_push] Connecting to {name} ({switch['host']})...")
        try:
            conn = ConnectHandler(
                device_type=switch["device_type"],
                host=switch["host"],
                username=switch["username"],
                password=_resolve_password(switch["password"]),
            )
            output = conn.send_config_set(all_commands[1:-1])  # send_config_set wraps in conf t / end
            conn.send_command("write memory")
            conn.disconnect()
            print(f"[vlan_push] {name} — VLANs pushed successfully.")
            if output.strip():
                print(output)
        except NetmikoAuthenticationException:
            print(f"[vlan_push] ERROR — Authentication failed for {name}.")
        except NetmikoTimeoutException:
            print(f"[vlan_push] ERROR — Connection timed out for {name} ({switch['host']}).")
        except EnvironmentError as exc:
            print(f"[vlan_push] ERROR — {exc}")

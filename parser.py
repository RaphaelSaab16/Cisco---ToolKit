from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Interface:
    name: str
    ip_address: str = ""
    subnet_mask: str = ""
    status: str = "unknown"      # up / down / administratively down
    description: str = ""
    vlans: list[str] = field(default_factory=list)


@dataclass
class VlanEntry:
    vlan_id: str
    name: str = ""


def parse_interfaces(config_text: str) -> list[Interface]:
    """Extract per-interface details from a running-config string."""
    interfaces: list[Interface] = []
    # Split on interface blocks
    blocks = re.split(r"(?=^interface\s)", config_text, flags=re.MULTILINE)

    for block in blocks:
        if not block.startswith("interface "):
            continue

        lines = block.strip().splitlines()
        iface = Interface(name=lines[0].split("interface ", 1)[1].strip())

        for line in lines[1:]:
            line = line.strip()

            if line.startswith("description "):
                iface.description = line[len("description "):]

            elif line.startswith("ip address "):
                parts = line.split()
                if len(parts) >= 4:
                    iface.ip_address = parts[2]
                    iface.subnet_mask = parts[3]

            elif line == "shutdown":
                iface.status = "administratively down"

            elif line.startswith("switchport access vlan "):
                iface.vlans = [line.split()[-1]]

            elif line.startswith("switchport trunk allowed vlan "):
                vlan_str = line.split("allowed vlan ", 1)[1]
                iface.vlans = _expand_vlan_range(vlan_str)

        # Default status for non-shutdown interfaces
        if iface.status == "unknown":
            iface.status = "up"

        interfaces.append(iface)

    return interfaces


def parse_vlans(config_text: str) -> list[VlanEntry]:
    """Extract VLAN database entries from a running-config string."""
    vlans: list[VlanEntry] = []
    blocks = re.split(r"(?=^vlan\s\d)", config_text, flags=re.MULTILINE)

    for block in blocks:
        match = re.match(r"^vlan (\d+)", block)
        if not match:
            continue
        entry = VlanEntry(vlan_id=match.group(1))
        name_match = re.search(r"^\s+name\s+(.+)$", block, re.MULTILINE)
        if name_match:
            entry.name = name_match.group(1).strip()
        vlans.append(entry)

    return vlans


def parse_file(config_path: str | Path) -> tuple[list[Interface], list[VlanEntry]]:
    """Parse a saved config file. Returns (interfaces, vlans)."""
    text = Path(config_path).read_text()
    return parse_interfaces(text), parse_vlans(text)


def print_interfaces(interfaces: list[Interface]) -> None:
    header = f"{'Interface':<25} {'IP Address':<18} {'Mask':<16} {'Status':<22} {'Description'}"
    print(header)
    print("-" * len(header))
    for iface in interfaces:
        ip = iface.ip_address or "-"
        mask = iface.subnet_mask or "-"
        desc = iface.description or "-"
        vlans = f" [VLANs: {','.join(iface.vlans)}]" if iface.vlans else ""
        print(f"{iface.name:<25} {ip:<18} {mask:<16} {iface.status:<22} {desc}{vlans}")


def _expand_vlan_range(vlan_str: str) -> list[str]:
    """Expand '10,20-22,30' → ['10', '20', '21', '22', '30']."""
    result = []
    for part in vlan_str.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            result.extend(str(v) for v in range(int(start), int(end) + 1))
        elif part:
            result.append(part)
    return result

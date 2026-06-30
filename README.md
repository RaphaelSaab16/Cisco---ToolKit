# Cisco IOS Config Toolkit

A Python CLI toolkit for automating Cisco IOS device management — config backup, parsing, diff, and VLAN automation. Directly relevant to CCNA lab practice and real-world network operations.

## Stack

| Library | Purpose |
|---|---|
| `netmiko` | SSH connections to Cisco IOS devices |
| `paramiko` | Underlying SSH transport (netmiko dependency) |
| `PyYAML` | Inventory and VLAN definition files |
| `re` | Config parsing |
| `argparse` | CLI interface |
| `difflib` | Config diffing (stdlib) |

## Features

- **Config backup** — pull and timestamp running-config from one or all devices
- **Config diff** — unified diff between backups; coloured output in terminal
- **VLAN automation** — push VLAN configs to switches from a YAML file, with `--dry-run`
- **Interface parser** — extract IP, status, description, and VLAN membership per interface
- **Inventory-based** — define all devices once in `devices.yaml`
- **Secure credentials** — passwords via environment variables only, never hardcoded

## Project Structure

```
cisco-toolkit/
├── main.py          # CLI entry point (argparse)
├── backup.py        # Pull and save running configs
├── parser.py        # Parse interface and VLAN info from saved configs
├── vlan_push.py     # Push VLAN configs to switches
├── diff.py          # Compare configs (coloured unified diff)
├── devices.yaml     # Device inventory
├── switches.yaml    # Example VLAN push target file
├── configs/         # Saved config backups (timestamped)
├── requirements.txt
└── README.md
```

## Setup

```bash
git clone <repo>
cd cisco-toolkit
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

Set credentials as environment variables:

```bash
export SW_PASS="your_switch_password"
export ROUTER_PASS="your_router_password"
```

## CLI Usage

### Backup

```bash
# Backup a single device
python main.py --backup core-switch

# Backup all devices in inventory
python main.py --backup all
```

Configs are saved to `configs/<device-name>_<timestamp>.cfg`.

### Diff

```bash
# Diff the two most recent backups for a device
python main.py --diff core-switch

# Diff against an explicit baseline
python main.py --diff core-switch --baseline configs/core-switch_20240101-120000.cfg
```

Output is a coloured unified diff (green = added, red = removed).

### Push VLANs

```bash
# Push VLANs defined in switches.yaml
python main.py --push-vlans switches.yaml

# Preview commands without sending
python main.py --push-vlans switches.yaml --dry-run
```

### Parse a Saved Config

```bash
python main.py --parse configs/core-switch_20240515-083000.cfg
```

Prints a table of interfaces (IP, mask, status, description, VLANs) and a VLAN list.

## devices.yaml Format

```yaml
devices:
  - name: core-switch
    host: 192.168.1.10
    username: admin
    password: ${SW_PASS}       # references $SW_PASS env var
    device_type: cisco_ios
```

## switches.yaml Format (VLAN push)

```yaml
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
```

## Testing Without Hardware

Use **GNS3** or **Cisco Packet Tracer** to simulate devices locally:

1. In GNS3, add a Cisco IOS router/switch image and start the node
2. Set the management IP on the simulated device
3. Update `devices.yaml` with the GNS3 host IP
4. Run the toolkit against the simulated device

Packet Tracer note: Packet Tracer's SSH implementation may not be fully compatible with netmiko — GNS3 with a real IOS image is recommended for complete testing.

## CCNA Relevance

This toolkit covers several CCNA exam topics in a practical context:

- **VLANs** — creation, naming, trunk/access port assignment (`vlan_push.py`, `parser.py`)
- **SSH management** — connecting to devices via SSH (`backup.py`)
- **Running config** — reading and interpreting `show running-config` output (`parser.py`)
- **Interface states** — up/down/administratively down (`parser.py`)
- **IP addressing** — parsing IP address and subnet mask per interface (`parser.py`)
- **Configuration management** — backup and change tracking (`backup.py`, `diff.py`)

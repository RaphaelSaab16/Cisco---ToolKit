#!/usr/bin/env python3
"""Cisco IOS Config Toolkit — CLI entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml


def _load_inventory(inventory_path: str = "devices.yaml") -> list[dict]:
    path = Path(inventory_path)
    if not path.exists():
        sys.exit(f"[error] Inventory file not found: {inventory_path}")
    data = yaml.safe_load(path.read_text())
    return data.get("devices", [])


def _find_device(devices: list[dict], name: str) -> dict:
    for d in devices:
        if d["name"] == name:
            return d
    sys.exit(f"[error] Device '{name}' not found in inventory.")


def cmd_backup(args: argparse.Namespace, devices: list[dict]) -> None:
    from backup import backup_device, backup_all

    if args.backup == "all":
        backup_all(devices)
    else:
        device = _find_device(devices, args.backup)
        backup_device(device)


def cmd_diff(args: argparse.Namespace) -> None:
    from diff import print_diff

    print_diff(args.diff, baseline_path=args.baseline)


def cmd_push_vlans(args: argparse.Namespace) -> None:
    from vlan_push import push_vlans

    push_vlans(args.push_vlans, dry_run=args.dry_run)


def cmd_parse(args: argparse.Namespace) -> None:
    from parser import parse_file, print_interfaces

    cfg_path = Path(args.parse)
    if not cfg_path.exists():
        sys.exit(f"[error] Config file not found: {cfg_path}")

    interfaces, vlans = parse_file(cfg_path)

    print(f"\nInterfaces in {cfg_path.name}:")
    print_interfaces(interfaces)

    if vlans:
        print(f"\nVLANs in {cfg_path.name}:")
        print(f"  {'ID':<8} Name")
        print("  " + "-" * 30)
        for v in vlans:
            print(f"  {v.vlan_id:<8} {v.name or '(unnamed)'}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="main.py",
        description="Cisco IOS Config Toolkit",
    )
    p.add_argument(
        "--inventory",
        default="devices.yaml",
        metavar="FILE",
        help="Path to device inventory YAML (default: devices.yaml)",
    )

    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--backup",
        metavar="DEVICE|all",
        help="Backup running-config. Use 'all' to backup every device in inventory.",
    )
    group.add_argument(
        "--diff",
        metavar="DEVICE",
        help="Diff the two most recent backups for a device.",
    )
    group.add_argument(
        "--push-vlans",
        metavar="FILE",
        help="Push VLANs from a YAML file to switches.",
    )
    group.add_argument(
        "--parse",
        metavar="CONFIG_FILE",
        help="Parse a saved config file and print interface/VLAN table.",
    )

    p.add_argument(
        "--baseline",
        metavar="FILE",
        help="Explicit baseline config for --diff (default: second-latest backup).",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="With --push-vlans: print commands without sending them.",
    )

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.backup or args.diff or (args.backup and args.backup != "all"):
        devices = _load_inventory(args.inventory)
    else:
        devices = []

    if args.backup:
        cmd_backup(args, devices)
    elif args.diff:
        cmd_diff(args)
    elif args.push_vlans:
        cmd_push_vlans(args)
    elif args.parse:
        cmd_parse(args)


if __name__ == "__main__":
    main()

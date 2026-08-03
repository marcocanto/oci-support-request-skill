#!/usr/bin/env python3
"""Build, but never submit, an OCI Support incident create JSON payload."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SEVERITIES = {"LOW", "MEDIUM", "HIGH", "HIGHEST"}


def required_text(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Missing required text field: {key}")
    return value.strip()


def optional_text(payload: dict[str, Any], data: dict[str, Any], source: str, target: str) -> None:
    value = data.get(source)
    if isinstance(value, str) and value.strip():
        payload[target] = value.strip()


def build_payload(data: dict[str, Any]) -> dict[str, Any]:
    severity = required_text(data, "severity").upper()
    if severity not in SEVERITIES:
        raise ValueError(f"severity must be one of: {', '.join(sorted(SEVERITIES))}")
    payload: dict[str, Any] = {
        "compartmentId": required_text(data, "tenancy_id"),
        "description": required_text(data, "description"),
        "problemType": "TECH",
        "severity": severity,
        "title": required_text(data, "title"),
        "ocid": required_text(data, "user_ocid"),
        "homeregion": required_text(data, "home_region"),
    }
    optional_text(payload, data, "csi", "csi")
    optional_text(payload, data, "domain_id", "domainid")
    optional_text(payload, data, "user_group_id", "userGroupId")
    optional_text(payload, data, "referrer", "referrer")
    contacts = data.get("contacts")
    if contacts is not None:
        if not isinstance(contacts, list) or not all(isinstance(item, dict) for item in contacts):
            raise ValueError("contacts must be a JSON list of contact objects")
        payload["contacts"] = contacts
    if severity == "HIGHEST" and not contacts:
        raise ValueError("HIGHEST severity requires a confirmed 24x7 contact")
    ticket = data.get("ticket")
    if ticket is not None:
        if not isinstance(ticket, dict):
            raise ValueError("ticket must be a JSON object")
        payload["ticket"] = ticket
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--intake", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        data = json.loads(args.intake.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("intake must contain one JSON object")
        payload = build_payload(data)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.output.resolve())
    return 0


if __name__ == "__main__":
    sys.exit(main())

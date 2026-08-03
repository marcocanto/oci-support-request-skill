#!/usr/bin/env python3
"""Plan or run allowlisted read-only OCI CLI evidence commands."""

from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CommandSpec:
    name: str
    description: str
    argv: tuple[str, ...]
    requires: tuple[str, ...]


def spec(name: str, description: str, argv: list[str], requires: list[str]) -> CommandSpec:
    return CommandSpec(name, description, tuple(argv), tuple(requires))


SERVICE_COMMANDS: dict[str, list[CommandSpec]] = {
    "block-volume": [
        spec("volume", "Block Volume configuration and lifecycle", ["bv", "volume", "get", "--volume-id", "{volume_id}"], ["volume_id"]),
        spec("volume-attachment", "Affected volume attachment", ["compute", "volume-attachment", "get", "--volume-attachment-id", "{volume_attachment_id}"], ["volume_attachment_id"]),
        spec("volume-backup", "Affected volume backup", ["bv", "backup", "get", "--volume-backup-id", "{volume_backup_id}"], ["volume_backup_id"]),
    ],
    "compute": [
        spec("instance", "Compute instance configuration and lifecycle", ["compute", "instance", "get", "--instance-id", "{instance_id}"], ["instance_id"]),
    ],
    "dns": [
        spec("dns-zone", "DNS zone configuration", ["dns", "zone", "get", "--zone-name-or-id", "{zone_name_or_id}"], ["zone_name_or_id"]),
    ],
    "database": [
        spec("db-system", "DB system configuration and lifecycle", ["db", "system", "get", "--db-system-id", "{db_system_id}"], ["db_system_id"]),
        spec("autonomous-database", "Autonomous Database configuration and lifecycle", ["db", "autonomous-database", "get", "--autonomous-database-id", "{autonomous_database_id}"], ["autonomous_database_id"]),
    ],
    "postgresql": [
        spec("postgresql-db-system", "Database with PostgreSQL configuration and lifecycle", ["psql", "db-system", "get", "--db-system-id", "{db_system_id}"], ["db_system_id"]),
    ],
    "fastconnect-vpn": [
        spec("virtual-circuit", "FastConnect virtual circuit state", ["network", "virtual-circuit", "get", "--virtual-circuit-id", "{virtual_circuit_id}"], ["virtual_circuit_id"]),
        spec("ipsec-connection", "Site-to-Site VPN IPSec connection state", ["network", "ip-sec-connection", "get", "--ipsc-id", "{ipsec_id}"], ["ipsec_id"]),
    ],
    "file-storage": [
        spec("file-system", "File system configuration and lifecycle", ["fs", "file-system", "get", "--file-system-id", "{file_system_id}"], ["file_system_id"]),
        spec("mount-target", "Mount target configuration and lifecycle", ["fs", "mount-target", "get", "--mount-target-id", "{mount_target_id}"], ["mount_target_id"]),
    ],
    "functions": [
        spec("function", "Function configuration and lifecycle", ["fn", "function", "get", "--function-id", "{function_id}"], ["function_id"]),
        spec("application", "Functions application configuration", ["fn", "application", "get", "--application-id", "{application_id}"], ["application_id"]),
    ],
    "identity": [
        spec("iam-policy", "IAM policy statements and scope", ["iam", "policy", "get", "--policy-id", "{policy_id}"], ["policy_id"]),
    ],
    "oke": [
        spec("oke-cluster", "OKE cluster configuration and lifecycle", ["ce", "cluster", "get", "--cluster-id", "{cluster_id}"], ["cluster_id"]),
        spec("oke-node-pool", "OKE node pool configuration and lifecycle", ["ce", "node-pool", "get", "--node-pool-id", "{node_pool_id}"], ["node_pool_id"]),
    ],
    "load-balancer": [
        spec("load-balancer", "Load Balancer configuration and lifecycle", ["lb", "load-balancer", "get", "--load-balancer-id", "{load_balancer_id}"], ["load_balancer_id"]),
        spec("load-balancer-health", "Aggregate Load Balancer health", ["lb", "load-balancer-health", "get", "--load-balancer-id", "{load_balancer_id}"], ["load_balancer_id"]),
    ],
    "network-load-balancer": [
        spec("network-load-balancer", "Network Load Balancer configuration and lifecycle", ["nlb", "network-load-balancer", "get", "--network-load-balancer-id", "{network_load_balancer_id}"], ["network_load_balancer_id"]),
        spec("network-load-balancer-health", "Aggregate Network Load Balancer health", ["nlb", "network-load-balancer-health", "get", "--network-load-balancer-id", "{network_load_balancer_id}"], ["network_load_balancer_id"]),
    ],
    "object-storage": [
        spec("bucket", "Object Storage bucket configuration", ["os", "bucket", "get", "--namespace-name", "{namespace}", "--bucket-name", "{bucket_name}"], ["namespace", "bucket_name"]),
    ],
    "streaming": [
        spec("stream", "Streaming stream configuration and lifecycle", ["streaming", "admin", "stream", "get", "--stream-id", "{stream_id}"], ["stream_id"]),
    ],
    "vcn": [
        spec("vcn", "VCN configuration and lifecycle", ["network", "vcn", "get", "--vcn-id", "{vcn_id}"], ["vcn_id"]),
        spec("subnet", "Subnet configuration", ["network", "subnet", "get", "--subnet-id", "{subnet_id}"], ["subnet_id"]),
        spec("route-table", "Route table configuration", ["network", "route-table", "get", "--rt-id", "{route_table_id}"], ["route_table_id"]),
        spec("security-list", "Security list configuration", ["network", "security-list", "get", "--security-list-id", "{security_list_id}"], ["security_list_id"]),
        spec("nsg", "Network security group configuration", ["network", "nsg", "get", "--nsg-id", "{nsg_id}"], ["nsg_id"]),
    ],
}

ISSUE_CHOICES = (
    "control-plane",
    "connectivity",
    "performance",
    "authorization",
    "data-recovery",
    "capacity",
    "lifecycle",
    "configuration",
)

AUDIT_ISSUES = {"control-plane", "authorization", "lifecycle", "configuration"}

REDACT_KEYS = {
    "authorization",
    "auth-token",
    "customer-secret-key",
    "defined-tags",
    "extended-metadata",
    "freeform-tags",
    "idtoken",
    "metadata",
    "password",
    "private-key",
    "secret",
    "session-token",
    "ssh-authorized-keys",
    "token",
    "wallet",
}

SECRET_PATTERN = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----|(?i:bearer\s+[a-z0-9._~+/=-]{16,})"
)


def normalize_key(value: str) -> str:
    return value.lower().replace("_", "-")


def sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            normalized = normalize_key(str(key))
            if normalized in REDACT_KEYS or any(part in normalized for part in ("password", "private-key", "secret", "token")):
                cleaned[str(key)] = "[REDACTED]"
            else:
                cleaned[str(key)] = sanitize(item)
        return cleaned
    if isinstance(value, list):
        return [sanitize(item) for item in value]
    if isinstance(value, str) and SECRET_PATTERN.search(value):
        return "[REDACTED]"
    return value


def parse_values(items: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"Expected key=value, received: {item}")
        key, value = item.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key or not value:
            raise ValueError(f"Expected non-empty key=value, received: {item}")
        result[key] = value
    return result


def issue_commands(issue: str) -> list[CommandSpec]:
    commands: list[CommandSpec] = []
    if issue in AUDIT_ISSUES:
        commands.append(
            spec(
                "audit-window",
                "Audit events for the narrow incident window",
                ["audit", "event", "list", "--compartment-id", "{compartment_id}", "--start-time", "{start_time}", "--end-time", "{end_time}"],
                ["compartment_id", "start_time", "end_time"],
            )
        )
    if issue == "performance":
        commands.append(
            spec(
                "monitoring-window",
                "Monitoring data for the affected resource and UTC window",
                ["monitoring", "metric-data", "summarize-metrics-data", "--compartment-id", "{compartment_id}", "--namespace", "{metric_namespace}", "--query-text", "{metric_query}", "--start-time", "{start_time}", "--end-time", "{end_time}"],
                ["compartment_id", "metric_namespace", "metric_query", "start_time", "end_time"],
            )
        )
    if issue == "capacity":
        commands.append(
            spec(
                "service-limits",
                "Current service limit values",
                ["limits", "value", "list", "--compartment-id", "{compartment_id}", "--service-name", "{limit_service_name}"],
                ["compartment_id", "limit_service_name"],
            )
        )
    return commands


def render_command(command: CommandSpec, values: dict[str, str], args: argparse.Namespace) -> list[str]:
    rendered = [token.format(**values) for token in command.argv]
    prefix = ["oci"]
    if args.profile:
        prefix.extend(["--profile", args.profile])
    if args.region:
        prefix.extend(["--region", args.region])
    if args.auth:
        prefix.extend(["--auth", args.auth])
    return prefix + rendered + ["--output", "json"]


def command_plan(service: str, issue: str, values: dict[str, str], args: argparse.Namespace) -> list[dict[str, Any]]:
    plan: list[dict[str, Any]] = []
    for command in [*SERVICE_COMMANDS[service], *issue_commands(issue)]:
        missing = [key for key in command.requires if key not in values]
        item: dict[str, Any] = {
            "name": command.name,
            "description": command.description,
            "required_inputs": list(command.requires),
            "missing_inputs": missing,
            "status": "skipped_missing_inputs" if missing else "planned",
        }
        if not missing:
            item["command"] = render_command(command, values, args)
            item["command_display"] = shlex.join(item["command"])
        plan.append(item)
    return plan


def run_plan(plan: list[dict[str, Any]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for item in plan:
        if item["status"] != "planned":
            continue
        started = datetime.now(timezone.utc)
        try:
            completed = subprocess.run(
                item["command"],
                check=False,
                capture_output=True,
                text=True,
                timeout=90,
            )
        except subprocess.TimeoutExpired:
            item["status"] = "failed"
            item["error"] = "Command timed out after 90 seconds"
            continue
        item["started_utc"] = started.isoformat()
        item["completed_utc"] = datetime.now(timezone.utc).isoformat()
        item["exit_code"] = completed.returncode
        if completed.returncode != 0:
            item["status"] = "failed"
            item["error"] = sanitize(completed.stderr.strip()[-2000:])
            continue
        try:
            payload: Any = json.loads(completed.stdout)
        except json.JSONDecodeError:
            payload = {"text": completed.stdout}
        destination = output_dir / f"{item['name']}.json"
        destination.write_text(json.dumps(sanitize(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        item["status"] = "collected"
        item["file"] = destination.name


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--service", choices=sorted(SERVICE_COMMANDS))
    parser.add_argument("--issue", choices=ISSUE_CHOICES)
    parser.add_argument("--region")
    parser.add_argument("--profile", default="DEFAULT")
    parser.add_argument("--auth", choices=("api_key", "instance_principal", "resource_principal", "security_token"))
    parser.add_argument("--value", action="append", default=[], metavar="KEY=VALUE")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--execute", action="store_true", help="Run the planned read-only commands")
    parser.add_argument("--list-services", action="store_true")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.list_services:
        print(json.dumps({key: sorted({required for command in commands for required in command.requires}) for key, commands in SERVICE_COMMANDS.items()}, indent=2))
        return 0
    if not args.service or not args.issue:
        parser.error("--service and --issue are required unless --list-services is used")
    try:
        values = parse_values(args.value)
    except ValueError as error:
        parser.error(str(error))
    plan = command_plan(args.service, args.issue, values, args)
    manifest: dict[str, Any] = {
        "service": args.service,
        "issue": args.issue,
        "region": args.region,
        "profile": args.profile,
        "mode": "execute" if args.execute else "plan",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "commands": plan,
    }
    if not args.execute:
        print(json.dumps(manifest, indent=2))
        return 0
    output_dir = args.output_dir or Path(f"oci-sr-evidence-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}")
    run_plan(plan, output_dir)
    manifest["completed_utc"] = datetime.now(timezone.utc).isoformat()
    (output_dir / "manifest.json").write_text(json.dumps(sanitize(manifest), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(output_dir.resolve())
    return 0 if all(item["status"] in {"collected", "skipped_missing_inputs"} for item in plan) else 1


if __name__ == "__main__":
    sys.exit(main())

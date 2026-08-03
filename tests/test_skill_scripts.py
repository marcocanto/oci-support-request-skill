from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "prepare-oci-support-request"
COLLECTOR = SKILL / "scripts" / "collect_evidence.py"
PAYLOAD_BUILDER = SKILL / "scripts" / "build_sr_payload.py"
CLAUDE_ADAPTER = ROOT / ".claude" / "skills" / "prepare-oci-support-request" / "SKILL.md"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class CollectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.collector = load_module("collect_evidence", COLLECTOR)

    def test_supported_services_are_listed_without_calling_oci(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(COLLECTOR), "--list-services"],
            check=True,
            capture_output=True,
            text=True,
        )
        services = json.loads(completed.stdout)
        self.assertIn("block-volume", services)
        self.assertIn("compute", services)
        self.assertIn("vcn", services)

    def test_default_mode_only_builds_a_plan(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(COLLECTOR),
                "--service",
                "compute",
                "--issue",
                "lifecycle",
                "--region",
                "us-ashburn-1",
                "--value",
                "instance_id=ocid1.instance.example",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        plan = json.loads(completed.stdout)
        self.assertEqual("plan", plan["mode"])
        self.assertEqual("planned", plan["commands"][0]["status"])
        self.assertEqual("skipped_missing_inputs", plan["commands"][1]["status"])

    def test_sanitizer_redacts_secret_fields_and_bearer_values(self) -> None:
        value = {
            "password": "example-password",
            "nested": {
                "sessionToken": "example-token",
                "safe": "retain-me",
                "header": "Bearer abcdefghijklmnopqrstuvwxyz",
            },
        }
        sanitized = self.collector.sanitize(value)
        self.assertEqual("[REDACTED]", sanitized["password"])
        self.assertEqual("[REDACTED]", sanitized["nested"]["sessionToken"])
        self.assertEqual("[REDACTED]", sanitized["nested"]["header"])
        self.assertEqual("retain-me", sanitized["nested"]["safe"])


class PayloadBuilderTests(unittest.TestCase):
    def test_builds_a_low_severity_technical_payload(self) -> None:
        intake = {
            "tenancy_id": "ocid1.tenancy.example",
            "description": "Example issue description",
            "severity": "LOW",
            "title": "Example technical request",
            "user_ocid": "ocid1.user.example",
            "home_region": "IAD",
            "user_group_id": "example-group",
        }
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            intake_path = directory_path / "intake.json"
            output_path = directory_path / "support-create.json"
            intake_path.write_text(json.dumps(intake), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(PAYLOAD_BUILDER),
                    "--intake",
                    str(intake_path),
                    "--output",
                    str(output_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual("TECH", payload["problemType"])
            self.assertEqual("LOW", payload["severity"])
            self.assertEqual("example-group", payload["userGroupId"])

    def test_highest_severity_requires_a_confirmed_contact(self) -> None:
        intake = {
            "tenancy_id": "ocid1.tenancy.example",
            "description": "Example issue description",
            "severity": "HIGHEST",
            "title": "Example critical request",
            "user_ocid": "ocid1.user.example",
            "home_region": "IAD",
        }
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            intake_path = directory_path / "intake.json"
            output_path = directory_path / "support-create.json"
            intake_path.write_text(json.dumps(intake), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(PAYLOAD_BUILDER),
                    "--intake",
                    str(intake_path),
                    "--output",
                    str(output_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(2, completed.returncode)
            self.assertIn("requires a confirmed 24x7 contact", completed.stderr)
            self.assertFalse(output_path.exists())

    def test_maps_support_severity_label_to_cli_value(self) -> None:
        builder = load_module("build_sr_payload", PAYLOAD_BUILDER)
        base = {
            "tenancy_id": "ocid1.tenancy.example",
            "description": "Example issue description",
            "title": "Example technical request",
            "user_ocid": "ocid1.user.example",
            "home_region": "IAD",
        }
        expected = {
            "Severity 1": "HIGHEST",
            "Significant Impairment": "HIGH",
            "Technical Issue": "MEDIUM",
            "General Guidance": "LOW",
        }
        for label, cli_value in expected.items():
            with self.subTest(label=label):
                intake = dict(base, severity=label)
                if cli_value == "HIGHEST":
                    intake["contacts"] = [{"name": "Confirmed 24x7 contact"}]
                self.assertEqual(cli_value, builder.build_payload(intake)["severity"])


class PackagingTests(unittest.TestCase):
    def test_claude_code_adapter_points_to_the_canonical_skill(self) -> None:
        adapter = CLAUDE_ADAPTER.read_text(encoding="utf-8")
        relative_target = Path("../../../skills/prepare-oci-support-request/SKILL.md")
        resolved_target = (CLAUDE_ADAPTER.parent / relative_target).resolve()
        self.assertEqual((SKILL / "SKILL.md").resolve(), resolved_target)
        self.assertIn("name: prepare-oci-support-request", adapter)
        self.assertIn(str(relative_target), adapter)

    def test_severity_guide_uses_public_sources_and_cli_values(self) -> None:
        guide = (SKILL / "references" / "severity-guide.md").read_text(encoding="utf-8")
        for value in ("HIGHEST", "HIGH", "MEDIUM", "LOW"):
            self.assertIn(f"`{value}`", guide)
        self.assertIn("https://docs.oracle.com/", guide)
        self.assertNotIn("Oracle Restricted", guide)


if __name__ == "__main__":
    unittest.main()

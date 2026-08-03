# OCI Support Request Skill

A Codex skill for preparing evidence-backed OCI technical support requests with the OCI CLI.

The skill selects issue-specific, read-only diagnostic commands, sanitizes collected JSON, generates a support-request payload, and optionally creates or updates an OCI Support service request after explicit user approval.

The repository includes a [GitHub Pages-ready interactive overview](docs/index.html) with the workflow and a copy-ready starter prompt builder.

## What it does

- Collects the affected service, symptom, region, UTC incident window, and resource OCIDs.
- Plans allowlisted OCI CLI `get`, `list`, Audit, and Monitoring commands before execution.
- Redacts common secret-bearing fields, tags, and instance metadata from collected JSON.
- Produces a command manifest, sanitized evidence files, and a paste-ready SR description.
- Builds a validated `TECH` request payload without submitting it.
- Requires an explicit preview and approval before SR creation, comments, attachments, contact changes, or closure.
- Reads the SR back after approved writes to verify the result.

## Supported service families

Block Volume, Compute, DNS, Database, Database with PostgreSQL, FastConnect and Site-to-Site VPN, File Storage, Functions, Identity, OKE, Load Balancer, Network Load Balancer, Object Storage, Streaming, and VCN.

Issue overlays cover control-plane, connectivity, performance, authorization, data-recovery, capacity, lifecycle, and configuration symptoms.

## Install

Copy `skills/prepare-oci-support-request` into your Codex skills directory:

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R skills/prepare-oci-support-request "${CODEX_HOME:-$HOME/.codex}/skills/"
```

Restart Codex after installation so the skill is discovered.

## Prerequisites

- A current OCI CLI installed locally
- A configured OCI CLI profile
- An OCI tenancy eligible for Oracle Support
- My Oracle Cloud Support registration and appropriate Support user-group privileges
- A US West (Phoenix) region subscription for Support Management CLI operations

Oracle documents that Support Management CLI commands are not supported from Cloud Shell.

## Example prompts

```text
Prepare an OCI support request for a Block Volume performance issue in us-ashburn-1.
```

```text
Collect evidence for a VCN connectivity issue between these two subnets from 14:00 to 15:00 UTC.
```

```text
Build the SR description and payload, but do not submit it.
```

```text
Show me the exact SR, comment, or attachment action and ask before sending it.
```

## Collector plan

The collector defaults to plan mode and does not call OCI:

```bash
python3 skills/prepare-oci-support-request/scripts/collect_evidence.py \
  --service block-volume \
  --issue performance \
  --region us-ashburn-1 \
  --value volume_id=ocid1.volume.example \
  --value compartment_id=ocid1.compartment.example \
  --value metric_namespace=oci_blockstore \
  --value 'metric_query=VolumeReadThroughput[1m]{resourceId = "ocid1.volume.example"}.mean()' \
  --value start_time=2026-08-03T14:00:00Z \
  --value end_time=2026-08-03T15:00:00Z
```

Add `--execute` and `--output-dir <directory>` only after reviewing the plan and confirming the tenancy, region, and resource identifiers.

## Build an SR payload

```bash
python3 skills/prepare-oci-support-request/scripts/build_sr_payload.py \
  --intake intake.json \
  --output support-create.json
```

This command only writes a JSON payload. It never submits an SR.

## Safety model

Evidence collection is limited to predefined read-only operations. The skill does not use OCI CLI `--debug`, invoke a shell for collector commands, or perform resource mutations as diagnostics.

Automatic redaction reduces risk but is not a substitute for human review. Inspect every generated file before sharing it with Oracle Support.

## Test

```bash
python3 -m unittest discover -s tests -v
```

The tests run locally and do not access OCI or create support requests.

## Repository layout

```text
skills/prepare-oci-support-request/
├── SKILL.md
├── agents/openai.yaml
├── references/
│   ├── evidence-map.md
│   └── support-cli.md
└── scripts/
    ├── build_sr_payload.py
    └── collect_evidence.py
```

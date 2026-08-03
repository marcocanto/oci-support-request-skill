# OCI Support Request Skill

A portable Agent Skill for Codex, Claude Code, and compatible coding agents that prepares evidence-backed OCI technical support requests with the OCI CLI.

The skill selects issue-specific, read-only diagnostic commands, sanitizes collected JSON, generates a support-request payload, and optionally creates or updates an OCI Support service request after explicit user approval.

Explore the [live interactive overview](https://marcocanto.github.io/oci-support-request-skill/) or view its [HTML source](docs/index.html). The page explains the workflow and includes a copy-ready starter prompt builder.

## Why use it

Customers commonly lose time at two points in the support process:

1. **Getting through intake:** Filing an SR through the Console can require several turns with the support chat interface before the request is created. With a configured OCI Support Management CLI, this skill can prepare the package and offer a direct CLI submission path after the customer reviews and approves the exact request.
2. **Waiting for missing-information requests:** Frontline support engineers often need service-specific resource OCIDs, request IDs, timestamps, configuration details, metrics, or network context before troubleshooting can begin. If those details are absent, the first response may simply ask the customer to collect them, adding another round trip.

The skill moves that discovery work to the beginning. It selects focused read-only checks for the affected service and symptom, packages the results with a concise problem statement, and makes the evidence available with the initial SR.

### Key benefits

- **Faster time to triage:** Give the service team the identifiers and context needed to begin investigation with the first handoff.
- **Fewer support round trips:** Reduce first-response requests for commonly missing evidence.
- **Less repetitive intake:** Produce a paste-ready SR or use the CLI submission workflow when the account supports it.
- **Service-aware evidence:** Collect different information for performance, connectivity, lifecycle, authorization, capacity, configuration, and recovery symptoms.
- **Safer automation:** Keep evidence collection read-only, redact common secret-bearing fields, and require explicit approval before every SR write.

## What it does

- Collects the affected service, symptom, region, UTC incident window, and resource OCIDs.
- Recommends the correct technical SR severity from current operational impact, workaround availability, and contact coverage, then asks the customer to confirm it.
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

The canonical package is `skills/prepare-oci-support-request/`. Its `SKILL.md` uses the portable Agent Skills format: YAML frontmatter for discovery followed by Markdown workflow instructions and relative links to bundled scripts and references.

### Codex

Copy `skills/prepare-oci-support-request` into your Codex skills directory:

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R skills/prepare-oci-support-request "${CODEX_HOME:-$HOME/.codex}/skills/"
```

Restart Codex after installation so the skill is discovered.

Invoke it explicitly with `$prepare-oci-support-request`, or describe an OCI support-intake task that matches the skill description.

### Claude Code

Claude Code uses the same `SKILL.md` structure. For a personal skill available across projects:

```bash
mkdir -p ~/.claude/skills
cp -R skills/prepare-oci-support-request ~/.claude/skills/
```

For a skill committed to a specific project:

```bash
mkdir -p .claude/skills
cp -R skills/prepare-oci-support-request .claude/skills/
```

This repository also includes `.claude/skills/prepare-oci-support-request/SKILL.md`, a project adapter that loads the canonical package without duplicating its implementation. Start or restart Claude Code after the first installation, then invoke the skill with:

```text
/prepare-oci-support-request
```

Claude Code can also load it automatically when a request matches the description in the skill frontmatter.

### Other Agent Skills-compatible agents

Install the complete `skills/prepare-oci-support-request/` directory in the harness's skill-discovery location. Keep `SKILL.md`, `scripts/`, and `references/` together so the relative resource links continue to work. The package intentionally uses only the portable `name` and `description` frontmatter fields; Codex-specific interface metadata remains isolated under `agents/openai.yaml`.

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
.claude/skills/prepare-oci-support-request/
└── SKILL.md              # Claude Code project adapter
docs/
├── assets/
│   └── github-social-preview.jpg
└── index.html
skills/prepare-oci-support-request/
├── SKILL.md
├── agents/openai.yaml
├── references/
│   ├── evidence-map.md
│   ├── severity-guide.md
│   └── support-cli.md
└── scripts/
    ├── build_sr_payload.py
    └── collect_evidence.py
```

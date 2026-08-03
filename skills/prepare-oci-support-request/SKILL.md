---
name: prepare-oci-support-request
description: Collect issue-specific OCI diagnostics with read-only OCI CLI commands, sanitize the evidence, generate a paste-ready technical support request, validate Support Management access, and optionally create, update, or attach files to an OCI Support SR after explicit approval. Use for OCI incident intake, SR preparation, service-specific evidence collection, support request submission, or support request updates through the OCI CLI.
---

# Prepare OCI Support Request

Create a small, evidence-backed SR package. Keep diagnostic collection read-only. Treat SR creation, update, closure, and attachment upload as external writes that require explicit user approval.

## Workflow

1. Confirm the affected service, closest symptom, region, UTC incident window, known resource OCIDs, current operational impact, and workaround status.
2. Read [references/severity-guide.md](references/severity-guide.md). Recommend a severity from the customer's current impact, explain the mapping, and ask the user to confirm it. Never silently choose a severity.
3. Run `oci --version` and confirm authentication with a narrow read-only command.
4. Read [references/evidence-map.md](references/evidence-map.md) for the service inputs and issue overlay.
5. Preview the collector plan:

   ```bash
   python3 scripts/collect_evidence.py \
     --service block-volume \
     --issue performance \
     --region us-ashburn-1 \
     --value volume_id=<volume_ocid> \
     --value compartment_id=<compartment_ocid> \
     --value start_time=2026-08-03T14:00:00Z \
     --value end_time=2026-08-03T15:00:00Z
   ```

6. Show the planned commands and missing inputs. Run with `--execute` only after confirming the target tenancy, region, and resource identifiers.
7. Review every generated file before using it. The collector removes common secret-bearing fields, tags, and instance metadata, but the operator remains responsible for the final review.
8. Generate a concise SR description with problem, impact, resources, UTC timing, exact error and request IDs, expected versus observed behavior, recent changes, troubleshooting, and collected evidence.
9. If the user asks to submit or update the SR, read [references/support-cli.md](references/support-cli.md) completely before proceeding.

## Safety rules

- Use only GET, LIST, validation, and monitoring query operations during evidence collection.
- Never run create, update, delete, attach, detach, reboot, reset, terminate, restore, failover, or policy-changing resource commands as diagnostics.
- Never collect or include passwords, private keys, customer secret keys, auth tokens, session data, CHAP secrets, wallet contents, or unredacted instance metadata.
- Do not use `--debug`; it can expose request details and credentials.
- Do not infer a tenancy, compartment, region, resource OCID, CSI, user group, production impact, workaround status, or 24x7 contact. A severity recommendation must be explained from customer-confirmed impact and explicitly confirmed by the user.
- For business-critical incidents, advise opening the SR immediately and adding evidence afterward. Do not delay submission for a perfect bundle.
- Before creating an SR, show the title, severity, user group, contacts, description, and attachment list. Ask for explicit confirmation.
- Before updating, closing, or attaching to an SR, show the incident key and exact action. Ask for explicit confirmation.
- Never use `--force` for Support Management updates.

## Evidence collector

Use `scripts/collect_evidence.py` to select allowlisted commands by service and issue category. The default mode prints a plan. `--execute` runs only the fixed read-only command templates and writes sanitized JSON plus `manifest.json`.

List supported services and input names:

```bash
python3 scripts/collect_evidence.py --list-services
```

Use repeated `--value key=value` arguments for resource identifiers and issue inputs. Never interpolate user input into a shell command. The script uses argument arrays and does not invoke a shell.

## SR payload

Use `scripts/build_sr_payload.py` to turn a reviewed intake JSON file into an OCI CLI `--from-json` payload. The script does not submit anything.

```bash
python3 scripts/build_sr_payload.py --intake intake.json --output support-create.json
```

Inspect the payload and use the approval-gated submission flow in [references/support-cli.md](references/support-cli.md).

## Output contract

Return:

- `SR Description.txt`: paste-ready customer description
- `manifest.json`: commands attempted, UTC execution times, failures, and missing inputs
- Sanitized evidence JSON files
- `support-create.json`: only when SR submission is requested
- A short attachment recommendation, normally no more than four files

Clearly label collected facts, customer-provided statements, failed checks, and unverified gaps.

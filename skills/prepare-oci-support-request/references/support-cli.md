# OCI Support Management CLI

Read this file completely before creating, updating, closing, or attaching files to a support request.

## Current capabilities

The OCI Support Management CLI supports listing, creating, reading, and updating support requests. Current OCI CLI releases also support attachment upload with `oci support incident put-attachment`.

Official references:

- https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/support.html
- https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/support/incident/create.html
- https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/support/incident/put-attachment.html
- https://docs.oracle.com/en-us/iaas/Content/GSG/support/validate-user.htm
- https://docs.oracle.com/en-us/iaas/Content/GSG/support/known-issues.htm

## Prerequisites

1. Use a paid account that is eligible for Oracle Support.
2. Complete the user's My Oracle Cloud Support registration.
3. Obtain create or edit privileges in the appropriate Support user group from the Customer User Administrator.
4. Confirm the tenancy is subscribed to US West (Phoenix). Support Management API, SDK, and CLI calls can be rejected otherwise.
5. Run Support Management commands from a locally configured CLI. Oracle documents that these commands are not supported in Cloud Shell.
6. Use the tenancy OCID as `--compartment-id`.
7. Supply the OCI user OCID. Supply `--domainid` for a non-default identity domain.
8. Supply the tenancy home region with `--homeregion` when applicable.
9. Inspect `oci support incident create --help` because required fields and supported severity values differ across OCI CLI versions. Older releases can require CSI and omit `LOW` severity.

Before preparing a technical request, read [severity-guide.md](severity-guide.md), recommend the closest severity from the current customer-confirmed impact, and ask the user to confirm it.

## Read-only preflight

Run these without changing Support state:

```bash
oci --version
oci iam region-subscription list --tenancy-id <tenancy_ocid>
oci support validation-response validate-user \
  --problem-type TECH \
  --ocid <user_ocid> \
  --homeregion <home_region> \
  --region us-phoenix-1
oci support incident-resource-type list \
  --problem-type TAXONOMY \
  --compartment-id <tenancy_ocid> \
  --ocid <user_ocid> \
  --homeregion <home_region> \
  --region us-phoenix-1
```

Use the validation response to identify eligible user groups. Do not invent or select a user group without user confirmation.

## Prepare the create request

Generate a template that matches the installed CLI:

```bash
oci support incident create --generate-full-command-json-input
```

Or use `scripts/build_sr_payload.py` with a reviewed intake file. The core technical request fields are:

- Tenancy OCID as `compartmentId`
- `problemType` set to `TECH`
- Title
- Detailed description
- Confirmed severity accepted by the installed CLI (`HIGHEST`, `HIGH`, `MEDIUM`, or `LOW` in current releases)
- OCI user OCID
- Home region
- Support user group ID for technical requests when required
- CSI when required by the installed version or support-account configuration
- 24x7 contact details for `HIGHEST`

## Approval gate for creation

Show the complete title, severity, user group, contacts, description, and attachment list. Ask the user to explicitly approve submission. Only then run:

```bash
oci support incident create \
  --from-json file://support-create.json \
  --region us-phoenix-1
```

Capture the returned incident key. Support requests do not have OCIDs.

## Attachment upload

First check availability:

```bash
oci support incident put-attachment --help
```

If the installed CLI does not expose the command, upgrade the OCI CLI or use the Support portal. Review the file for secrets and personal information. Ask for explicit approval for each attachment. Then run:

```bash
oci support incident put-attachment \
  --compartment-id <tenancy_ocid> \
  --incident-key <support_request_id> \
  --file <reviewed_file> \
  --is-restricted-flag <true_or_false> \
  --region us-phoenix-1
```

Set the restricted flag to true when the attachment contains personal information or protected health information.

## Updates

Adding a comment, changing the problem description, closing a request, and other updates are external writes. Show the incident key, activity type, and exact comment. Ask for explicit approval. Do not use `--force`.

## Failure handling

- `4xx` in Cloud Shell: use a locally configured CLI.
- Rejected Support API call: verify Phoenix subscription, home region, user registration, user OCID, domain ID, CSI compatibility, and Support user-group privileges.
- Read-only SR: ask the Customer User Administrator for edit privileges in the associated user group.
- Missing `put-attachment`: the local CLI is older than the current attachment-capable command set.

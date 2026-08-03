# OCI Support Severity Guide

Use this guide for technical support requests. Severity must reflect the issue's current operational impact, not the desired response speed. Recommend a level from the facts below, explain the reason in one sentence, and ask the user to confirm it before building or submitting the SR.

## OCI CLI mapping

| OCI CLI value | Support label | Use when |
| --- | --- | --- |
| `HIGHEST` | Severity 1, Critical Outage | A critical production system or business function is unavailable or unstable, the situation is an emergency, and work cannot reasonably continue. A confirmed contact must be available to work the issue 24x7 if needed. |
| `HIGH` | Severity 2, Significant Impairment | A critical system or business function has a severe loss of service with no acceptable workaround, but operations can continue in a restricted manner. |
| `MEDIUM` | Severity 3, Technical Issue | A functionality, error, or performance issue affects some operations, or a minor loss of service creates an inconvenience that might require a workaround. |
| `LOW` | Severity 4, General Guidance | The request is for product or service usage information, setup help, an enhancement, or documentation clarification, with no immediate operational impact or loss of service. |

## Selection questions

Ask these questions in order and record the answers as customer-provided statements:

1. Is a production system or critical business function unavailable or unstable?
2. Can the customer reasonably continue work?
3. Is there an acceptable workaround?
4. If operations can continue, are they severely restricted or is only some functionality affected?
5. Is the request only for information, setup help, an enhancement, or documentation clarification?
6. For `HIGHEST`, who is the confirmed technical contact available 24x7?

Use the highest level whose complete definition is supported by the answers. Do not silently infer impact, workaround status, production status, or contact availability. If the answers are incomplete, present the closest candidate and the missing fact that prevents confirmation.

## Guardrails

- Do not select `HIGHEST` solely because the issue is urgent, visible to executives, or tied to a deadline.
- Do not delay a business-critical SR while collecting a perfect evidence bundle. Open it promptly and add reviewed evidence afterward.
- State the business function affected, scope, user or transaction impact, start time in UTC, workaround status, and whether the impact is ongoing.
- Reassess severity when impact improves or worsens. A severity change is not the same as a management escalation.
- Verify the accepted values with `oci support incident create --help`; older OCI CLI releases can expose a different subset.

## Public Oracle sources

- OCI support severity levels: https://docs.oracle.com/en-us/iaas/Content/dedicated/dedicated-region/customer-support.htm
- Creating an OCI support request: https://docs.oracle.com/en-us/iaas/Content/GSG/support/create-incident.htm
- OCI CLI create command and accepted severity values: https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/support/incident/create.html

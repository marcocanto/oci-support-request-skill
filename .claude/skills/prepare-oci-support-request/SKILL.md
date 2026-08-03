---
name: prepare-oci-support-request
description: Collect issue-specific OCI diagnostics with read-only OCI CLI commands, sanitize the evidence, generate a paste-ready technical support request, validate Support Management access, and optionally create, update, or attach files to an OCI Support SR after explicit approval. Use for OCI incident intake, SR preparation, service-specific evidence collection, support request submission, or support request updates through the OCI CLI.
---

# Prepare OCI Support Request

Use the repository's canonical portable skill package.

1. Read [the canonical SKILL.md](../../../skills/prepare-oci-support-request/SKILL.md) completely before taking task actions.
2. Resolve its `references/` and `scripts/` paths relative to `../../../skills/prepare-oci-support-request/`.
3. Follow every read-only collection rule and explicit approval gate in the canonical skill.

This adapter exposes the shared skill to Claude Code's project-level `.claude/skills/` discovery without maintaining a second implementation.

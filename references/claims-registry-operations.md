# Claims-Registry Operations

Use these mechanics when parallel scouting or adversarial checking produces claims that will feed a report.

## Aggregate parallel batches before checking

Give each concurrent scout separate `drafts/sources_<group>.jsonl` and `drafts/claims_<group>.jsonl` files instead of a shared registry; concurrent appenders can lose writes and invent incompatible record shapes. In the main context, aggregate deterministically before Round 3:

1. Normalize every record to the source and claim schemas.
2. Recompute `source_id` from the canonical locator and deduplicate sources by that locator.
3. Remap claims to sequential `C`-IDs while retaining the authored source linkage.
4. Set unchecked claims to `candidate`, then run `claims_check.py`.

Do not treat a scout's nonstandard `kind`, lifecycle label, or self-assigned confidence as validated evidence. Preserve useful scout caveats in the checker notes or claim locator rather than extending the schema ad hoc.

## Check the whole statement

Compare every clause with the source, not merely whether `evidence_quote` appears in it. A valid quote can support the first clause while the statement adds an unsupported cause, drops a qualifier, or expands the population. Reject or correct the entire claim accordingly.

Recheck every checker-generated replacement in a fresh context. Discard a replacement that repeats the original overreach; correction authorship does not make the correction self-validating.

Verify delegated file writes by absolute path and readback before aggregation. A subagent's success report does not prove that a vault-relative note landed in the intended report directory; path resolution can place it at the vault root. Check each artifact's `source_url`, ingestion metadata, and body hash mechanically rather than trusting its manifest.

For protocol and security incidents, verify order-sensitive mechanics and arithmetic against the normative specification plus raw transaction, log, or event data when secondary accounts disagree. A source can list the same numeric range but omit the ordering that determines how many operations apply. Save raw verifier output under `artifacts/` so the conclusion can be reproduced without trusting the checker’s summary.

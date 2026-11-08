# Security Incident Analysis

Use this reference for incident reconstruction, attacker-TTP comparison, claims of technical sophistication or novelty, and cross-domain security parallels. It supplements the claims pipeline; it does not replace source verification.

## Reconstruct by control plane

1. Split the incident into initial access, lateral movement, credential or privilege use, authorization decision, durable authority created, monetization, containment, and recovery.
2. Label each link as first-party established fact, source-attributed assessment, independent inference, or unknown. Keep the label in the prose when it changes what the reader should believe.
3. Separate the decision point from the artifact it creates. A signing service, OAuth grant, build signature, and on-chain delegation are different objects with different owners and revocation paths.
4. Leave the crucial connective gap explicit when a source jumps from endpoint or container access to a high-value action. Do not invent the missing API, token permission, or approval path.

## Verify disputed protocol behavior with raw data

When postmortems disagree about transaction shape or protocol semantics, reproduce the decisive observation rather than selecting the most confident source.

- Fetch the raw transaction and relevant account state; cross-check block hashes across independent providers.
- Inspect payload length and ordering, account nonces before and after the block, other transactions in that block, execution status, and gas where it discriminates between explanations.
- Test order-dependent and state-dependent rules against the actual ordering and state. A correct general protocol property can still yield the wrong result for a particular transaction.
- Save the machine-readable capture, register it as a primary source, and quote its exact fields in the claim. Keep derived calculations in `analysis/`.

## Test causal sufficiency

For every proposed cause, ask whether it explains all observations and what else would have to be true.

- If the same architecture performed both the malicious action and the defensive action, architecture alone does not explain why one succeeded and the other was delayed. Consider shutdown choices, quorum availability, runbooks, transaction construction, approval process, and verification.
- Attribute a victim's causal explanation to the victim, then state independently whether the public record proves it. Consistency with the timeline is not causal proof.
- Treat a plausible operational rationale as an interpretation, not an observed motive. Include alternatives such as pre-positioning, queued batches, or bounded operational risk when the record does not distinguish them.
- Do not turn the absence of key theft evidence into evidence that no key was stolen. State whether the mechanism made key theft unnecessary.

## Make antecedent and novelty claims falsifiable

Include the closest structural analogue, an older base case, and at least one case that does not fit the proposed pattern. A sample selected for a mechanism cannot establish that the mechanism is universal. Scope conclusions to the sample unless the search justifies a broader claim.

Separate novelty of primitive, target, composition, operating conditions, and effect. Prior art for the primitive does not settle novelty of its use against a different control plane; conversely, a new target does not create a new primitive. Avoid first-ever claims without a documented search boundary.

Compare magnitude against the strongest relevant precedent or a small range of precedents, not the smallest convenient comparator. Preserve distinctions between initial burst duration and the full incident window.

## Keep analogies operationally precise

Distinguish producer-side controls from consumer-side controls. Producers must constrain what a trusted service may authorize; consumers must verify provenance and prepare for trusted publishers to fail. Do not offer one roadmap for both.

Compare revocation mechanics explicitly. An administrator-revocable OAuth grant and a subject-signed, per-network on-chain revocation share an inventory problem but not an administrative unset or severity model. Preserve evaluation, sandbox, intent, and oversight context when comparing autonomous systems with human-directed intrusions.

For AI involvement, distinguish human-directed abuse of a victim's tool, actor-directed automation of existing tradecraft, and no human direction of individual steps. Autonomous execution with real impact does not by itself establish an external malicious campaign or intent.

## Ground recommendations in the known failure

When the failed architecture is unknown, give conditional controls rather than declaring one fix. Raw or blind signing requires object-type restrictions; a policy-engine bypass requires intent binding and independent verification of the final object.

Contain both the existing credential and the authority it created. Where appropriate, stop crediting inbound funds, verify revocation on the external plane, retire the compromised address or identity, and migrate assets. Use organization-specific baselines for alerts instead of universal thresholds. Treat response times from slower control planes as structural comparisons, not targets for faster attacks.

## Deduplicate after parallel drafting

Explain each decisive mechanism once at full depth. Later sections should add a comparison, implication, or recommendation rather than repeat the transaction shape, timing, and rationale. Independently drafted sections otherwise repeat the strongest details and make the report feel longer without adding evidence.

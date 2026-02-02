# RouteGuard Protocol (Field Manual)

RouteGuard is a constraint layer for multi-agent systems. It enforces *route integrity* (non-drifting behavior)
by requiring provenance, decay, falsification, residuals, and explicit uncertainty accounting before
memory commits or tool execution.

RouteGuard is not a moral framework. It is a control and verification framework.

---

## 0. Definitions

- **ClaimRecord**: A memory item with provenance + uncertainty + decay.
- **UpdateEvent**: A state change log entry with before/after hashes + uncertainty delta + audit trail.
- **Cycle**: A structured multi-role reasoning step: Proposer → Challenger → Anchor → Integrator (+ Auditor).
- **Gate**: A deterministic rule that must pass before high-impact actions (memory/tool/commit).
- **Residual**: A logged disagreement / uncertainty remainder that survives integration.

---

## 1. Core Axiom: Form–Measure Compensation

Any change in belief *form* must be accompanied by a compensating change in *measure* (uncertainty).

Operationally:
- Confidence cannot rise without stronger grounding OR explicit residual/uncertainty payment.
- Summarization/compression must declare loss (what was omitted and how uncertainty changed).
- New structure without verification must increase uncertainty, not decrease it.

RouteGuard uses discrete deltas (Δ) because agents operate in steps.

---

## 2. Memory Discipline

### 2.1 Checkable Memory
Every ClaimRecord must contain:
- source (self/agent/external), timestamp
- confidence AND uncertainty
- decay rate or TTL
- support and counter-support entries

### 2.2 Decay
Memory decays unless reinforced by:
- external checks
- adversarial survival tests
- repeated observation

Decay prevents scripture accumulation and stops “canon by repetition.”

### 2.3 No Canon Without Source
A claim may not become canonical unless:
- it has provenance
- it passed gates
- it survived challenge
- residuals are logged

---

## 3. Update Discipline (Molting Rule)

Every UpdateEvent must emit:
- before_state_hash, after_state_hash
- changed_fields
- invariants_preserved
- uncertainty_delta
- justification
- audit trail (what was written/deleted)

Forbidden:
- silent overwrites
- confidence inflation without grounding
- deletion without replacement or retraction rationale

---

## 4. Role-Separated Cycle

RouteGuard requires a minimum cycle for high-impact outputs:

1) **PROPOSER**: proposes hypothesis and creates initial ClaimRecords
2) **CHALLENGER**: attempts falsification, lists failure modes + repairs
3) **ANCHOR**: checks external grounding OR flags missing evidence
4) **INTEGRATOR**: merges, produces core agreement + residuals + UpdateEvent
5) **AUDITOR**: runs gates; PASS allows commit/execution

Residual disagreement is mandatory. “No residuals” is suspicious unless grounded.

---

## 5. Gates (Verification Before Action)

## Execution Gates

Before any tool call or memory commit, RouteGuard emits a GateEvent.
A GateEvent records whether an action is permitted based on:
- context trust
- required approvals
- role separation

No action executes without a GateEvent decision.

A standard gate order:

1. SOURCE_AND_FIELDS_PRESENT
2. TAINTED_CONTEXT_CHECK (v0.2)
3. SIGNAL_GROUNDING
4. FALSIFICATION_ATTEMPTED
5. RESIDUALS_REPORTED
6. INVARIANT_PRESERVED_OR_UNCERTAINTY_PAID
7. TOOL_PERMISSION_GATE (v0.2)
8. NO_FORBIDDEN_PRACTICES

If a gate FAILS, the system must produce:
- violations
- minimal repairs
- rerun plan

---

## 6. Forbidden Practices (Anti-Amplification)

- Recursive summary without new input
- Canon without source
- Agreement without challenger
- Identity claims without uncertainty
- Tool execution based on untrusted/tainted context

These are not “ethics.” They are known amplification pathways.

---

## 7. v0.2 Additions (Execution Controls)

### 7.1 Tool Permissions
Tool use is gated by:
- allowlist of actions
- sandbox profile requirement
- dry-run requirement for destructive ops
- human approval requirements for high-risk domains
- rate limits (anti-loop runaway)

### 7.2 Tainted Context
Any input from untrusted sources sets a flag:
- tainted_context=true
This forces:
- Anchor step required
- Tool execution blocked OR requires human approval
- Memory writes become QUARANTINED until verified

### 7.3 TTL Policy
Claims have TTL classes; high-risk claims expire fast unless reinforced.

---

## 8. Minimal Implementation Guidance

A practical integration pattern:

Agent output → RouteGuard validator → gates → (PASS) commit memory/tool calls
                                        → (FAIL) return repair plan to agent

RouteGuard works best as middleware:
- before memory writes
- before tool execution
- before publication / propagation to other agents

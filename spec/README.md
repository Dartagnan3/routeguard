# RouteGuard Spec

Formal protocol definition for RouteGuard.

This directory defines:
- Record schemas
- DecayEvent — marks claim expiry via TTL.
- Invariants
- Validation rules

These schemas define the minimal grammar for non-drifting belief systems.

## Subject requirements (policy-level)

The `interaction_event` schema allows `subject` to be omitted to support system-level events.

However, RouteGuard policy treats certain action namespaces as **agency-bearing** and requires a `subject` for them:

- `tool.*`
- `data.*`
- `exec.*`
- `network.*`
- `coordination.*` (recommended)

If an agency-bearing action omits subject, the event is considered an underdetermined relation and must be denied or require anchoring before execution.

# RouteGuard

**RouteGuard** is a constraint layer for multi-agent systems.  
It enforces **non-drifting behavior** using provenance, decay, falsification, and execution gates.

> *Change is allowed. Drift is not. All transformation must be measured.*

---

## Why RouteGuard exists

Agents are now good at **execution**.  
What’s missing is **route integrity**:

Common failure modes in agent systems:
- Memory becomes canon without source  
- Summaries recurse into hallucinations  
- Consensus forms without challenge  
- Tools execute based on untrusted context  
- Systems converge too fast on bad beliefs  

RouteGuard adds the missing primitives:
**provenance, uncertainty, decay, challenge, and gates**.

It is not a moral framework.  
It is a **control and verification layer**.

---

## What RouteGuard does

RouteGuard enforces four invariants:

### 1. Checkable memory  
Every stored belief must include:
- source  
- timestamp  
- confidence *and* uncertainty  
- decay / TTL  

No anonymous canon. No eternal scripture.

---

### 2. Invariant-preserving updates  
Every update must declare:
- before/after hashes  
- changed fields  
- invariants preserved  
- uncertainty delta  
- audit trail  

No silent overwrites.  
No confidence inflation without grounding.

---

### 3. Verifier-first swarm cycles  
High-impact outputs must pass:

**PROPOSER → CHALLENGER → ANCHOR → INTEGRATOR (+ AUDITOR)**

Residual disagreement is mandatory.

Consensus reduces variance, not necessarily error.

---

### 4. Execution gates  
Before tools or memory commits:

- tainted context is detected  
- sandbox + permission profiles are enforced  
- high-risk actions require approval  
- TTL rules are applied  

Execution is bounded by verification.

---

## What RouteGuard is *not*

- ❌ Not an AI alignment theory  
- ❌ Not a safety policy document  
- ❌ Not a moral framework  
- ❌ Not an agent architecture  

It is a **protocol + schema + validator**  
that you can put **between agents and actions**.

---

## Repo contents

``` 
spec/        Protocol JSON (MSP / RouteGuard)
examples/    Example ClaimRecords, UpdateEvents, Cycles
src/         Minimal validator + gates
docs/        Field manual and design notes
``` 
---

## Integration pattern

Typical placement:

``` 
agent output
↓
RouteGuard validator + gates
↓
(memory write / tool execution / publish)

```

RouteGuard works best as middleware:
- before memory writes  
- before tool calls  
- before propagation to other agents  

---
## Behavior Examples

RouteGuard enforces policy decisions on model outputs and events.

Pass → Run examples
Pass
```bash
python -m routeguard.cli --policy examples/policy.json --file examples/model_output_good.txt
```

Expected:

```
ALLOW: Output passed RouteGuard policy.
```
Deny
```bash
python -m routeguard.cli --policy examples/policy.json --file examples/model_output.txt
```

Expected:

```
DENY: Output violated RouteGuard policy.
```
Invariant violation
```bash
python -m routeguard.cli --policy examples/policy.json --file examples/invariant_violation_event.json
```

Expected:

```
DENY: Invariant violation detected.
```
Tool Permission Denied
```bash
python -m routeguard.cli --policy examples/policy.json --file examples/tool_permission_send_external_email_deny.json
```

Expected:

```
DENY: Tool permission not granted.
```
---
## Core axiom

> Any change in belief form must be accompanied  
> by a compensating change in uncertainty.

Discrete operational form:

Δ(form) + Δ(measure) ≈ 0

This is enforced through:
- decay  
- residuals  
- falsification  
- gating  

---

## Roadmap

- v0.2: tool permissions + tainted context + TTL policy  
- v0.3: prompt-injection detectors  
- v0.4: Python + TypeScript middleware  
- v1.0: stable spec + CI compliance badges  

---

## Who this is for

- builders of agent systems  
- researchers doing multi-agent reasoning  
- teams running tool-using agents  
- anyone who has seen agents drift  

If your system can act, it needs constraints.

---

## Quick Start

### 1. Install (editable mode)
```bash
pip install -e .
```

  2. Run RouteGuard on a known-good example
```
python -m routeguard.cli \
  --policy examples/policy.json \
  --file examples/model_output_good.txt
```
Expected:
```
✅ ALLOW: Output passed RouteGuard policy.
```

  3. Run RouteGuard on a failing example
```
python -m routeguard.cli \
  --policy examples/policy.json \
  --file examples/model_output.txt
```
Expected: 
```
DENY: Output violated RouteGuard policy.
```
  4. Use in Python
```
from routeguard import RouteGuardEngine

engine = RouteGuardEngine("examples/policy.json")

with open("examples/model_output_good.txt") as f:
    text = f.read()

result = engine.evaluate_output(text)
print(result)
```
     
## License

MIT or Apache-2.0 (recommended)

---

## One-line summary

> RouteGuard is a constraint grammar for fast-moving agent systems.

<!-- GENERATED FILE - do not edit. Run: python3 scripts/generate_index.py -->

# Doctrine router

Consult this router for consequential operations work: architecture,
self-healing design, authority, integration, publication, or anything touching a
named critical service. Routine lookups and mechanical execution should not
incur doctrine ceremony.

Each entry states when retrieval **changes the decision** (consult) and when it
would only add ceremony (skip). Respect both.

## Knowledge

### [documentation-placement](doctrine/knowledge/documentation-placement.md)

Place knowledge by how long it stays true, not by how important it feels; one subject per document, update rather than duplicate, and verify the store's render contract before writing to it.

`status: active` · `authority: adopted` · `confidence: high`

**Consult when:**

- deciding which store a new piece of knowledge belongs in
- about to create a document that may overlap an existing one
- writing to a store whose markup or render behavior you have not verified
- a store has become unreliable, duplicated, or unsearchable
- ranking conflicting information from documentation, memory, and the live system

**Skip when:**

- reading from a store rather than writing to it
- the store has exactly one obvious home for the material and no overlap risk

**Decision effect:** Route material to a store by lifetime, update the existing owner instead of creating a near-duplicate, and confirm the markup a store actually renders before writing content into it.

## Operations

### [work-tracking-lifecycle](doctrine/operations/work-tracking-lifecycle.md)

Open or find a record before acting, read the environment's own documentation before diagnosing, checkpoint resumably while working, write findings back, and hand the record to the operator for verification rather than closing it yourself.

`status: active` · `authority: adopted` · `confidence: high`

**Consult when:**

- starting any operational task, however small it appears
- deciding whether work needs a tracking record
- a task is multi-step, long-running, or at risk of interruption
- about to perform a long-running, quota-risky, or hard-to-reverse operation
- work is finished and needs to reach the operator
- deciding who may close a record
- designing or reviewing automation that files, updates, or closes records

**Skip when:**

- answering a question that changes no system state
- a conversational or clarifying exchange with no operational work attached
- the operator has explicitly waived tracking for a specific throwaway action

**Decision effect:** Bracket every task with a durable external record - search or create first, checkpoint during, document after, hand off at the end - so that an interrupted session resumes without re-derivation and no agent marks its own work verified.

## Reliability

### [verification-before-claiming-done](doctrine/reliability/verification-before-claiming-done.md)

An accepted command is not an achieved effect; confirm state through a channel independent of the one that issued the command before reporting anything as done.

`status: active` · `authority: adopted` · `confidence: high`

**Consult when:**

- about to report an action as done
- commanding a physical device, actuator, or anything with real-world consequence
- chaining automation steps where a later step assumes an earlier one succeeded
- an integration reports success while observed state disagrees
- designing a confirmation, retry, or reconciliation path
- deciding whether an entity's reported state is trustworthy

**Skip when:**

- the action is a pure local read with no state change
- the tool's return value is itself the verification, and independently so
- a human is directly observing the effect in real time

**Decision effect:** Insert an independent state confirmation between action and report, and treat a reporting integration's own success value as insufficient evidence for a physical or stateful change.

### [watchdog-blast-radius](doctrine/reliability/watchdog-blast-radius.md)

Bound remediation to the smallest unit that can carry the fault; wider remediation converts one component's failure into an outage and erases the evidence identifying it.

`status: active` · `authority: adopted` · `confidence: high`

**Consult when:**

- designing or modifying an automated healer, watchdog, or restart policy
- a watchdog is firing repeatedly and the underlying fault is not identified
- deciding the unit of remediation for a detected fault
- an intermittent fault has resisted diagnosis while self-healing was active
- choosing escalation tiers or their frequency caps

**Skip when:**

- performing a one-off manual restart with a human watching the result
- the service is genuinely a single indivisible unit with no independent components
- the question is whether a health check is correct, rather than what it should remediate

**Decision effect:** Choose the remediation unit from the detection unit, cap escalation frequency, and treat repeated escalation as an unresolved fault signal rather than as successful recovery.

## Reading this router

`status` is whether guidance applies now. `authority` is whether it is adopted
policy or advisory judgment. `confidence` is how well the grounds support it.
These are independent axes - `active` + `advisory` + `low` means use it now as
the best bounded model while staying ready to revise it.

A retrieval miss during real work is a doctrine defect, not a user error. Fix
the trigger, the placement, or the SOUL residue according to the cause.

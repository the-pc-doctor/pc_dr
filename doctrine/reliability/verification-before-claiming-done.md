---
id: verification-before-claiming-done
type: doctrine
status: active
authority: adopted
confidence: high
confidence_basis:
  - Repeatedly observed where an agent commands physical actuators and stateful services through an intermediary API.
  - The mechanism is structural - an accepted command proves the request was received, never that the effect occurred.
  - Failure is asymmetric and cheap to prevent, which justifies a rule rather than a principle.
scope:
  - Any report that an action was completed
  - Any command issued through an API, queue, broker, or bridge to a physical device or stateful service
  - Any automation whose next step assumes the previous step took effect
consult_when:
  - about to report an action as done
  - commanding a physical device, actuator, or anything with real-world consequence
  - chaining automation steps where a later step assumes an earlier one succeeded
  - an integration reports success while observed state disagrees
  - designing a confirmation, retry, or reconciliation path
  - deciding whether an entity's reported state is trustworthy
do_not_use_when:
  - the action is a pure local read with no state change
  - the tool's return value is itself the verification, and independently so
  - a human is directly observing the effect in real time
router_summary: "An accepted command is not an achieved effect; confirm state through a channel independent of the one that issued the command before reporting anything as done."
decision_effect: "Insert an independent state confirmation between action and report, and treat a reporting integration's own success value as insufficient evidence for a physical or stateful change."
implemented_by:
  - watchdogs/lib/watchdog_common.sh
lineage: LINEAGE.md
known_failures:
  - Verification through the same integration that issued the command is not independent and can confirm a state that never happened.
  - A cached or stale state source can confirm the desired state indefinitely; freshness must be checked alongside value.
  - Over-applied to trivial reversible reads, this adds latency and ceremony with no decision effect.
review_when:
  - a report of completion is contradicted by later observation
  - an integration's reported state is found to be stale rather than wrong
  - a reconciliation loop begins fighting a legitimate manual override
  - verification cost becomes disproportionate to the consequence of the action
last_material_revision: 2026-07-29
---

# Verification before claiming done

"I sent the command" and "the thing happened" are different claims. Only the second one is a report.

## Why the gap exists

An agent acting on the physical world reaches it through layers: agent → automation platform → integration → cloud service or broker → device firmware → actuator. Each layer returns success for *its own* step. A `200 OK` from the automation platform means the platform accepted the request. It says nothing about the last four layers.

Ways the chain breaks while every layer reports success:

- The integration queues the command and the connection drops before delivery.
- A cloud-dependent device is unreachable; the vendor API accepts and buffers.
- The device receives the command and refuses it — obstruction, interlock, low battery, safety stop.
- The command succeeds and something else immediately reverts it, such as a competing automation.
- The entity's reported state is **cached** and reflects the last successful poll, not the present.
- Name resolution fails inside a container, and the failure surfaces as a generic timeout that a retry wrapper swallows.

None of these produce an error at the layer the agent can see.

## The rule

**Confirm the effect through a channel independent of the one that issued the command, before reporting completion.**

Independence is the operative word. Reading state back through the same integration that just sent the command is one source agreeing with itself. Useful, insufficient.

Independent confirmation, in descending order of strength:

1. **Direct physical observation** — a camera frame, a snapshot, a still image showing the actual position or state. Strongest available evidence in a lab that has cameras. If cameras are present, this is not an exotic option; it is the ordinary one.
2. **A different sensor on the same physical fact** — a contact sensor, a power draw change, a temperature response.
3. **A different transport to the same device** — a local API rather than the cloud path, or the reverse.
4. **The same integration's state, with a freshness check** — acceptable only when nothing better exists, and only if you verify the timestamp advanced. A value without a timestamp is not a state; it is a memory.

## Freshness is part of the check

A state source that has stopped updating will happily confirm whatever it last saw. This produces the worst class of error: confident, specific, and wrong.

Check that the reading is *new*, not merely correct. When an entity's state and its underlying telemetry disagree — the summary says idle while the detailed sensors show activity — trust the detailed source and treat the summary as stale. When an entity is known to freeze in a particular state, do not use it as a verification source at all; document that and route around it.

## Reconciliation, not fire-and-forget

Edge-triggered automation with no confirmation loop fails silently the first time the edge is missed. If the trigger fires once and the command is lost, nothing ever retries, and the system sits in a state nobody intended.

For any action with real-world consequence, pair the edge trigger with a **reconciliation check**: periodically compare intended state against observed state, and correct the difference. Two constraints on the loop:

- **Bound the retries.** A loop that retries forever against a physical obstruction is a hazard, not persistence.
- **Respect manual override.** A human who deliberately changed something must be able to win. Reconciliation that fights an operator is worse than no reconciliation, because it is unpredictable.

## Reporting language

The distinction must survive into the words used:

| Do not write | Write |
|---|---|
| "Closed the door." | "Sent the close command; camera confirms closed at 14:02." |
| "Restarted and it's healthy." | "Restarted; health endpoint returned healthy on the third poll." |
| "Fixed." | "Changed X; the failing check now passes. Have not verified under load." |

Stating what was **not** verified is part of the report, not a hedge. A report that omits the unverified portion is asserting more than the evidence supports.

## Scope limit

This is a rule for consequential and stateful actions. It is not a mandate to double-check every read. A local file read, a status query, a directory listing — the tool result is the evidence, and adding a confirmation step there is ceremony with no decision effect.

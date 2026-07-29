---
id: watchdog-blast-radius
type: doctrine
status: active
authority: adopted
confidence: high
confidence_basis:
  - Repeatedly observed in production self-healing on a single-host container lab.
  - The mechanism is structural rather than statistical - a healer that restarts a shared parent necessarily interrupts every child.
  - Independently supported by the standard supervision-tree argument that recovery should occur at the smallest unit that can contain the fault.
scope:
  - Design and review of any automated healer, watchdog, health check, or restart policy
  - Incident review where automated remediation was active during the incident
consult_when:
  - designing or modifying an automated healer, watchdog, or restart policy
  - a watchdog is firing repeatedly and the underlying fault is not identified
  - deciding the unit of remediation for a detected fault
  - an intermittent fault has resisted diagnosis while self-healing was active
  - choosing escalation tiers or their frequency caps
do_not_use_when:
  - performing a one-off manual restart with a human watching the result
  - the service is genuinely a single indivisible unit with no independent components
  - the question is whether a health check is correct, rather than what it should remediate
router_summary: "Bound remediation to the smallest unit that can carry the fault; wider remediation converts one component's failure into an outage and erases the evidence identifying it."
decision_effect: "Choose the remediation unit from the detection unit, cap escalation frequency, and treat repeated escalation as an unresolved fault signal rather than as successful recovery."
implemented_by:
  - watchdogs/lib/watchdog_common.sh
  - watchdogs/systemd/
lineage: LINEAGE.md
known_failures:
  - Narrow remediation alone does not fix a fault whose true scope really is the parent; scope must follow evidence, not a preference for smallness.
  - A frequency cap with no alerting path converts a loud failure into a silent one.
  - Per-component restart can mask a shared upstream cause - a common dependency failing looks like several components failing independently.
review_when:
  - a healer's remediation repeatedly succeeds while the same fault keeps recurring
  - an escalation cap is reached and nothing surfaces to a human
  - narrowing remediation scope leaves a fault unrecovered
  - a fault turns out to be shared upstream rather than per-component
last_material_revision: 2026-07-29
---

# Watchdog blast radius

Automated healing is the most dangerous code in a homelab, because it is the only code with standing authority to take services down.

## The failure mode

A health check watches a multi-component service. One component becomes intermittently unhealthy. The check fires. Remediation restarts the **whole service**, because that is the easiest thing to script and it does resolve the symptom.

Three things follow:

1. Every other component is interrupted, including healthy ones. On a service with continuous work — recording, ingesting, streaming, logging — each restart is a data gap.
2. The restart clears the unhealthy state, so the check passes again. The fault is now invisible to the mechanism watching for it.
3. Because the fault is intermittent, this repeats. The system reports itself as self-healing while steadily losing availability, and the component actually at fault is never identified.

The observable signature is a healer with a high success rate, a high firing rate, and no corresponding fix. The self-healing is real; it is healing the wrong thing.

## The rule

**Remediation scope must not exceed detection scope.**

If the check can tell you *which* component is unhealthy, remediation must act on that component. Escalating to the parent is a fallback, not a first tier — and it needs its own justification, because a fallback that fires routinely is not a fallback.

## Designing the tiers

Escalate on evidence, not on a timer:

| Tier | Scope | Precondition |
|---|---|---|
| 1 | The failing component only | Detection identified the component |
| 2 | The component plus its direct dependencies | Tier 1 did not restore health |
| 3 | The whole service | Detection cannot localize the fault, **or** tiers 1 and 2 failed |

Each tier needs a frequency cap. The cap exists so that **hitting it produces a signal**, not so that the healer stops quietly. A tier that can fire without limit is a mechanism for converting an intermittent component fault into a chronic service outage.

Setting a top-tier cap to zero — disabling whole-service restarts entirely — is a legitimate configuration when experience shows that tier is doing more damage than good. It forces the fault to stay visible.

## Diagnosis in the presence of a healer

An intermittent fault plus active self-healing is a nearly unfalsifiable combination: the healer removes the evidence before you can inspect it.

When a fault resists diagnosis, check whether a healer has been erasing it. The cheapest evidence is the **count of remediation events per component over time** — a distribution concentrated on one component names the culprit immediately, and is often the only thing needed. Ensure every remediation logs its trigger, its scope, its tier, and its outcome; a healer that acts without recording why is untraceable by construction.

To diagnose actively, disable the healer for a bounded window and let the fault persist long enough to inspect. This trades availability for information. Do it deliberately, with the operator's knowledge, and not on a named critical service without a window.

## Interaction with resource pressure

On memory-constrained hardware, a watchdog and an out-of-memory killer can fight. The killer reclaims memory by terminating a process; the watchdog restarts it; the restart allocates again. This loop presents as instability with no single cause.

Resolve it by precedence, not by tuning both independently: name the critical services, protect them explicitly in the reclaim policy, and make the watchdog's restart decision aware that a kill it did not cause has occurred. `earlyoom` and similar tools support per-process protection for exactly this reason.

## Anti-pattern: the healer that hides its own trigger

A watchdog that restarts a service *and* clears the diagnostic state — the log, the metric, the error counter — has removed the only record of why it acted. Preserve the trigger evidence before remediating. Copy the relevant log window somewhere durable, then restart.

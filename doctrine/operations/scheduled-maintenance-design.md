---
id: scheduled-maintenance-design
type: doctrine
status: active
authority: advisory
confidence: medium
confidence_basis:
  - The failure modes are directly observed in a lab running many unattended jobs on constrained hardware.
  - Cadence and staggering recommendations are judgment calibrated to one environment and may not transfer to larger or better-provisioned ones.
  - The dead-man-switch and idempotence requirements are structural and hold generally.
scope:
  - Design and review of unattended scheduled work
  - Diagnosis of a scheduled job that is not producing its expected effect
consult_when:
  - creating or revising a scheduled job, timer, or unattended maintenance task
  - a scheduled job appears not to have run
  - several jobs are contending for the same resource
  - deciding the cadence of a maintenance pass
  - a maintenance job needs to touch a machine that may be powered off
do_not_use_when:
  - running a maintenance task manually and watching it
  - the schedule is externally imposed and not yours to design
router_summary: "Unattended work must be idempotent, observable in its absence, staggered against contention, and safe to run against a target that is asleep, missing, or already in the desired state."
decision_effect: "Design a scheduled job for the case where nobody is watching - make reruns safe, make a missed run detectable, and stagger jobs that share a resource."
implemented_by:
  - automation/cron/
lineage: LINEAGE.md
known_failures:
  - Staggering advice is tuned to a single constrained host and is unnecessary ceremony on hardware with headroom.
  - Aggressive idempotence can mask a job that is failing to do anything at all, since a no-op and a success look identical.
  - Dead-man monitoring adds a second system that can itself fail silently.
review_when:
  - a job is found to have been dead for an extended period
  - concurrent jobs cause resource exhaustion
  - a rerun after a partial failure causes damage
  - maintenance consistently runs against powered-off targets
last_material_revision: 2026-07-29
---

# Scheduled maintenance design

Unattended work is defined by what is *not* there: nobody watching, nobody to answer a prompt, nobody to notice it stopped.

## Design for nobody watching

**Idempotent.** A job must be safe to run twice, and safe to run after a partial failure. Assume it will be — schedulers overlap, retries happen, and someone will run it by hand while it is already running. Where the work genuinely cannot be repeated safely, take a lock, and make the lock expire so a crashed run does not block every future one.

**Non-interactive.** No prompts, no confirmations, no pagers. A job that blocks on input at 03:00 holds a lock and produces nothing until someone finds it. Set the flags that force non-interactive behavior explicitly rather than relying on the tool detecting it is not on a terminal.

**Bounded.** A timeout on the job, and a timeout on anything it calls over a network. Unbounded scheduled work is how one hung request becomes a permanently held lock.

**Quiet on success.** An audit or maintenance pass that finds nothing to do produces no message and no record. See `doctrine/operations/notification-discipline.md`.

## Make absence detectable

Quiet-on-success has a sharp edge: **a job that never runs looks exactly like a job with nothing to do.**

Resolve it in the monitoring layer, not by reintroducing success reports. The job pushes a heartbeat on completion, and the monitor alerts when the heartbeat does not arrive within the expected window. Push-style monitors exist for this; `uptime-kuma` supports them directly.

This inverts the responsibility correctly. The job's obligation is to say "I finished." The monitor's obligation is to notice that it did not.

## Stagger against contention

On constrained hardware, the scheduler is a resource allocator whether you designed it to be or not.

Jobs starting on the hour, all at once, contend for CPU, memory, disk, and network at the same moment. On a small board this is enough to trigger memory pressure and get something important killed — often the very services the maintenance existed to protect.

Practical rules:

- Offset start times. Nothing important should start at `:00`.
- Never overlap a backup with an image pull or a package upgrade; both are I/O-heavy and one of them will be starved.
- Keep heavy maintenance away from the busiest period for the services people actually use.
- Give long jobs a lock so the next scheduled run skips rather than doubling up.

## Cadence

Match the interval to how fast the underlying state actually changes, and to the cost of the check:

| Cadence | Fits |
|---|---|
| Every few minutes | Liveness probes and self-healing checks, if they are cheap |
| Hourly | Freshness and reconciliation checks against drifting state |
| Daily | Log rotation, cache trimming, lightweight audits |
| Weekly | Backups, per-service health passes, certificate checks |
| Monthly | Host package upgrades, container image refresh, image and volume pruning |

More frequent is not safer. A liveness check every minute against an expensive endpoint is a self-inflicted load problem, and a self-healing check that runs faster than the service can start will restart-loop it. Give a probe a start-up grace period longer than the service's real cold-start time.

## Targets that are not there

A scheduled job that maintains other machines must handle the machine being off, asleep, unreachable, or renamed.

- **Wake it first** if the platform supports it, then wait for it to actually answer — sending a wake packet is not the same as the host being up, and the check for readiness is a probe, not a sleep.
- **Fail cleanly and record it** when the target does not come up. A maintenance job that silently skips an unreachable host every week produces the appearance of coverage with none of the substance.
- **Never treat unreachable as healthy.** It is unknown, and unknown should be visible.

## Reporting

Per-target results belong in the work tracker as records, not as messages. A maintenance sweep across several machines produces one record per machine so the outcome is attributable, and durable findings graduate to the documentation store.

If the sweep found nothing anywhere, it produces nothing.

---
name: service-health-pass
description: Run the recurring per-service health and maintenance pass across the lab - container state, real health signals, storage headroom, certificate runway, backup freshness, watchdog activity, and pending updates. Use for the scheduled weekly or monthly maintenance window, or when asked for an overall state-of-the-lab check. Do not use for diagnosing an active incident.
---

# Service health pass

A scheduled sweep. Its output is **findings only** — if nothing needs attention, it produces nothing.

That silence is the point. An audit that reports every clean run turns the tracker and the notification channel into the noise they exist to surface signal from. See `doctrine/operations/notification-discipline.md`.

## Before

Open or bind a record. One record **per service that has a finding** — not one giant record, which cannot be assigned, tracked, or closed independently.

Check the operating record first for known-recurring items, so you recognize a familiar finding instead of investigating it fresh.

## The pass

Work each section. Record a finding; do not fix in place unless the fix is trivial, reversible, and inside an authorized scope. A maintenance window is for maintenance, not for redesign.

### 1. Container and unit state

- Any container not running that should be, or restarting repeatedly.
- Any enabled systemd unit in a failed state.
- Any watchdog timer that has not fired recently — a dead watchdog is silent, and its silence reads as health.

A container in a restart loop is a finding, not something to restart again.

### 2. Real health signals, not liveness

For each service, the signal from its reference page in `reference/services/` — not just whether the port answers:

| Service class | Signal that matters |
|---|---|
| Home automation | Share of entities unavailable, not just API up |
| NVR | Detection rate per camera; recording file recency on disk |
| Edge | A known route's status **and** direct-vs-proxied agreement |
| Observability | The monitor's own heartbeat, observed externally |
| Records | An authenticated API call, not a page load |

### 3. Storage

- Headroom on the host disk and on network storage.
- Mounts present **and writable** — a stale handle mounts fine and fails on write.
- Retention actually enforced: recordings, metrics, logs, container images, and **backup artifacts**. Timestamped backups beside live configuration accumulate silently until they become the storage incident.

### 4. Certificates

Days remaining, not renewal success. Renewal fails quietly and breaks everything external at once, on the expiry date rather than the failure date. Under three weeks is a finding.

### 5. Backups

- Did the last scheduled run complete?
- Is the destination growing as expected? A backup writing zero bytes succeeds every time.
- **When was a restore last verified?** An unverified backup is a belief. If the answer is "never", that is the most important finding in the pass.

### 6. Watchdog activity

Remediation counts per component since the last pass. Two patterns to look for:

- **Concentrated on one component** — that names an unresolved fault the healer has been masking.
- **A cap repeatedly reached** — the signal is the point; something is not being fixed.

A watchdog with a high firing rate and a high success rate is healing the wrong thing.

### 7. Pending updates

Available image and package updates, noted rather than applied — unless this is the monthly window and applying them is the job. When applying:

- Back up first.
- One stack at a time, so a regression is attributable.
- Verify each named critical service afterward, from the path that actually matters.
- Confirm architecture compatibility before pulling anything new.

## After

**Findings → the record.** One per service, with evidence.

**Durable discoveries → the documentation store.** If the pass revealed that a service is configured differently than documented, fix the documentation as part of this task. Stale documentation is worse than none, because it is trusted.

**Nothing found → produce nothing.** No record, no message, no all-clear.

**Hand off.** Transfer records to the operator with a recommendation. Do not close them.

## Guardrails

- Named critical services get a maintenance window, not an opportunistic restart. Confirm before taking one down.
- Do not batch unrelated changes into one window — attribution matters more than efficiency here.
- If the host is already under memory pressure, defer the heavy parts. A maintenance pass that triggers a reclaim event has caused the outage it was meant to prevent.

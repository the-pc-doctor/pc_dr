---
name: incident-triage
description: Triage a vague failure report - "it's down", "it's slow", "nothing works" - by localizing the fault to a tier before touching anything. Use at the start of any unplanned investigation, when several things appear broken at once, or when a service is reported down but may actually be reachable. Do not use when the failing component is already identified.
---

# Incident triage

The goal of triage is **localization**, not repair. Most wasted incident time is spent fixing a healthy component.

Work the steps in order. Each one is cheap and eliminates a whole class of cause.

## 0. Open the record first

Search the tracker, bind or create, before investigating. See `agent/skills/work-lifecycle/SKILL.md`.

This is not ceremony. In a mature lab a large share of incidents are recurrences, and the previous record usually contains the diagnosis, the remedies that failed, and the permanent fix. Skipping it is how an agent spends an hour re-deriving a solved problem and then applies a remedy the record already says does not work.

## 1. Has this happened before?

Listed first because it is the cheapest and most often decisive:

- The operating record and recurring-failure notes.
- Prior records for this subject, **including their failed attempts**.
- Documentation for the affected service.

If you find a match, jump straight to its documented permanent fix. Do not repeat a temporary one.

## 2. Is the host healthy?

Before blaming any service. Memory pressure on a small board makes every service look broken at once, and a swapping host is responsive enough to pass a liveness check while being unusable.

```bash
free -h
cat /proc/pressure/memory 2>/dev/null
df -h
uptime
```

A sluggish-but-alive host under memory pressure explains a multi-service report on its own. Check whether the reclaim daemon has killed anything recently — a kill followed by a watchdog restart followed by another kill presents as instability with no single cause.

## 3. Does it fail from every vantage point?

**This single check resolves the most common misdiagnosis in a proxied lab.**

```bash
curl -fsS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:<port>/<health>   # direct
curl -fsS -o /dev/null -w '%{http_code}\n' https://<external-name>/<health>   # proxied
```

| Direct | Proxied | Fault is |
|---|---|---|
| ok | fail | **The path** — proxy, DNS, certificate, or auth gateway. The service is fine; do not restart it. |
| fail | fail | The service, or something under it |
| ok | ok | Not reachability. Look at behavior, freshness, or the reporter. |

`wd_probe_both_paths` in `watchdogs/lib/watchdog_common.sh` implements this.

## 4. One component or a shared parent?

If several things broke together, find what they share before opening several investigations. Consult the failure-domain table in `reference/topology.md` — host, broker, network storage, proxy, resolver, uplink.

Two specific disguises worth checking early:

- **A dropped or stale network mount** presents as a write-heavy service failing, with a perfectly healthy container. Check the mount before the service.
- **A resolver answering "no data"** surfaces several layers up as a generic connection timeout, so a DNS fault reads as an unrelated API outage. Resolve the hostname explicitly.

## 5. Is the reporter telling the truth?

Before acting on a state you have not observed:

- Is the reading **fresh**? A stale entity reports its last value indefinitely, confidently.
- Does the **detail agree with the summary**? A rolled-up status can lag or fail independently of the telemetry under it.
- Does the **collection have members**? An empty group accepts every command and does nothing, reporting success each time.

See `doctrine/knowledge/source-authority.md`.

## 6. Has self-healing been erasing the evidence?

An intermittent fault plus an active watchdog is nearly unfalsifiable — the healer removes the evidence before you can inspect it, then reports a high success rate.

Check the per-component remediation counts. A distribution concentrated on one component names the culprit outright, and is often the entire diagnosis. If a watchdog has been firing repeatedly without the fault being identified, the watchdog is part of the problem.

## Then act

Only now. Restore service first if someone is waiting, then find the cause and fix the configuration so it does not recur — a restart that clears a symptom without explaining it is a deferred outage.

Verify the effect through an independent channel, checkpoint what you did, and hand the record to the operator. Do not close it yourself.

## What not to do

| Anti-pattern | Why |
|---|---|
| Restart first, diagnose after | Destroys the evidence that would have localized the fault |
| Restart the service on a "down" report without checking the path | Costs an outage on a healthy component |
| Open one record per symptom when several broke together | Fragments a single shared-cause investigation |
| Retry a remedy the record says failed | The most expensive avoidable mistake available |
| Report "fixed" on the strength of the command succeeding | Command issued is not effect achieved |

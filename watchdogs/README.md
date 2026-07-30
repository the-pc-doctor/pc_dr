# Watchdogs

Self-healing units. **The most dangerous code in the lab** — the only code with
standing authority to take services down.

Read `doctrine/reliability/watchdog-blast-radius.md` before adding one.

## Contract

`lib/watchdog_common.sh` implements it. Sourced by every watchdog:

| Function | Purpose |
|---|---|
| `wd_init <service>` | Set up state and evidence directories |
| `wd_probe_http <url>` | Liveness probe |
| `wd_probe_both_paths <direct> <proxied>` | **Localizes path faults vs service faults** (returns 2 for a path fault) |
| `wd_capture_evidence <unit> <reason>` | Save the trigger before remediating |
| `wd_tier_allowed <tier>` | Escalation cap; reaching it emits a SIGNAL |
| `wd_remediate <unit> <tier> <reason>` | Bounded restart with accounting |
| `wd_verify <url>` | Confirm the effect, with retries |
| `wd_verify_restarted <unit> <before>` | Confirm a restart actually took effect |
| `wd_guard_critical <name>` | Refuse to take a named critical service down outside a window |

## Rules

1. **Remediation scope must not exceed detection scope.** If the check knows
   which component failed, act on that component.
2. **Tier 3 (whole-service restart) defaults to a cap of zero.** Raise it only
   with evidence that the fault's true scope is the service.
3. **Reaching a cap is a signal, not a stop.** It means an unresolved fault, and
   it must be visible.
4. **Capture evidence before remediating.** A restart that clears the log that
   triggered it has destroyed the record of its own reason to act.
5. **Verify the effect.** An issued restart is not a restored service.
6. **Check shared dependencies first.** A dropped storage mount presents as the
   service failing; restarting the service accomplishes nothing.
7. **Guard against restart loops.** A watchdog that adds restarts to a
   restart-looping service makes the loop look like recovery.

## Installing

```bash
sudo cp systemd/lab-watchdog@.service systemd/lab-watchdog@.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now lab-watchdog@nvr.timer
sudo systemctl enable --now lab-watchdog@edge.timer
sudo systemctl enable --now lab-watchdog@home-automation.timer
```

The instance name selects the script: `lab-watchdog@nvr` runs `nvr-watchdog.sh`.

Per-instance cadence goes in a drop-in, not in the shared template:

```bash
sudo systemctl edit lab-watchdog@nvr.timer
```

## Included watchdogs

- `nvr-watchdog.sh` — checks the storage mount first, then liveness, then
  per-camera detection rate. Remediates the camera, never the service.
- `edge-watchdog.sh` — recreates a missing proxy container, localizes path vs
  service faults, tracks certificate runway.
- `home-automation-watchdog.sh` — restart-loop guard first, then liveness, then
  the share of unavailable entities broken down by integration domain.

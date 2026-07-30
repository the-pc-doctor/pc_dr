# Automation

Unattended work.

- `cron/` — the schedule. Nothing on the hour, everything bounded and locked,
  quiet on success with a heartbeat so absence is detectable.
- `lib/job_common.sh.tmpl` — the shared job contract: non-interactive
  enforcement, findings accumulation, wake-and-probe for sleeping targets, and
  the heartbeat push.
- `ha/` — home-automation patterns: closed-loop actuation, reconciliation,
  freshness guards, and empty-group guards.

Doctrine: `doctrine/operations/scheduled-maintenance-design.md`.

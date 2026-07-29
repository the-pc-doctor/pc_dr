# Doctrine — operations

How operational work is bracketed, tracked, scheduled, and handed off.

- `work-tracking-lifecycle.md` — the five stages: find or open a record before
  acting, read the environment before diagnosing, checkpoint resumably, write
  findings back, hand off for verification rather than closing.
- `change-backup-and-rollback.md` — back up before editing, change the narrowest
  surface, write through the owning process, verify the effect not the file.
- `notification-discipline.md` — interrupt a human for decisions only; routine
  success reporting destroys the channel it travels on.
- `scheduled-maintenance-design.md` — unattended work must be idempotent,
  detectable in its absence, staggered, and safe against targets that are off.

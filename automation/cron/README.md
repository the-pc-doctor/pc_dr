# Scheduled maintenance

`crontab.tmpl` renders to a crontab. Watchdogs are NOT here — they run as
systemd timers, which give per-instance cadence, boot delay, and randomized
spread that cron does not.

Two rules the layout encodes:

- **A job that reports nothing may have completed, or may never have run.** Every
  job pushes a heartbeat on completion; the uptime monitor alerts on the
  heartbeat not arriving. That is what makes quiet-on-success safe.
- **An audit that finds no work returns silence**, not a report — otherwise the
  audit becomes the noise it exists to surface signal from.

Nothing starts at `:00`. On a small host, simultaneous jobs contend for memory
and I/O hard enough to trigger a reclaim event.

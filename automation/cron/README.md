# Scheduled maintenance

Crontab and timer templates. Two rules carried from doctrine:

- A job that reports nothing may have completed or may never have run. Design
  for positive confirmation and make a missing signal detectable.
- An audit that finds no work returns silence, not a report — otherwise the
  audit becomes the noise it exists to detect.

Phase 3.

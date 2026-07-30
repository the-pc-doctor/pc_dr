# Reference

Topology and per-service shape, as templates. Reference describes what a class
of component *is*; it does not argue for a design — that belongs in `doctrine/`.
When a reference page starts making a case, split it.

- `topology.md` — tiers, dependency order, failure domains, and what to check
  first given a vague report.
- `services/` — one page per service class: dependencies, health signals, and
  how it fails.

Every address, hostname, and port is a placeholder resolved from `vars.yml`.

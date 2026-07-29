# Agent

- `config/` — runtime configuration shape, including the provider chain.
- `lib/` — helpers the skills call. `worktracker.py.tmpl` implements the work
  lifecycle against a Zammad-compatible tracker and an ITFlow-compatible
  documentation store, and owns both stores' response and render contracts so
  they are fixed in one place.
- `skills/` — repeatable procedures.
- `hooks/` — harness hooks.

Hooks are still pending; everything else here is in place.

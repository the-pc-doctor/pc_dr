# Agent

- `config/` — runtime configuration shape, including the provider chain.
- `lib/` — helpers the skills and hooks call.
  - `worktracker.py.tmpl` — the work lifecycle against a Zammad-compatible
    tracker and an ITFlow-compatible documentation store; owns both stores'
    response and render contracts so they are fixed in one place.
  - `credentials.sh.tmpl` — runtime secret resolution. Closes three leak paths:
    the file, the process list, and the transcript.
- `skills/` — repeatable procedures.
- `hooks/` — harness-executed enforcement of the lifecycle.

## The credential rule

A secret is never a literal in a script, a command line, a config file, or a
hook's injected context.

The third one is the least obvious and the worst. Anything a prompt-submit hook
injects is written into every stored session transcript — numerous, long-lived,
and not obviously credential-bearing. Point at a helper that resolves the secret
at call time.

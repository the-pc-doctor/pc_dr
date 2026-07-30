# Hooks

Harness-executed enforcement of the work lifecycle.

| Hook | Event | Enforces |
|---|---|---|
| `ticket-first.sh.tmpl` | Prompt submit | Stage 1 — find or open a record before acting |
| `auto-checkpoint.py.tmpl` | Session stop, pre-compaction | Stage 3 — a resumable checkpoint |
| `settings.example.json` | — | Wiring shape |

## Why hooks and not instructions

Both behaviors are otherwise model-executed, and a model-executed contract
degrades exactly when it matters most: under a long context, or after a provider
chain has failed over to a weaker tier. Those are the moments an interruption is
most likely and a checkpoint most valuable.

A hook is run by the harness. It fires identically regardless of which model is
behind the endpoint.

## Three rules

**1. No credential in a hook — especially not in injected text.**

A prompt-submit hook's output is injected into model context, which means it is
written into every stored session transcript. A credential embedded there is the
hardest leak to clean up: the transcripts are numerous, long-lived, and not
obviously credential-bearing. Point at a helper that resolves the secret at call
time. See `agent/lib/credentials.sh.tmpl`.

**2. Never block on a remote service.**

A prompt-submit hook is on the critical path of every prompt. A tracker that
answers in 4 seconds against a 2.5-second budget means the fetch *never*
completes — and the hook still emits, just without data. The failure is
invisible and can persist indefinitely. Serve from cache, refresh detached.

**3. Always exit 0.**

A non-zero exit from a prompt hook blocks the prompt, turning a tracker outage
into a total work stoppage. A checkpointer must never be able to break the work
it is recording. Every failure path degrades to silence.

## Installing

Render the templates, then wire them per `settings.example.json`. Verify by
running each hook directly with a synthetic stdin payload before relying on it —
a hook that fails silently is indistinguishable from one that is working.

# Lineage

## Adapted from

[`bobert-agent-template`](https://github.com/robertaustinbell/bobert-agent-template) — MIT licensed.

That project is a runtime-neutral starter for agent **identity and judgment**. It states explicitly that procedures, live domain facts, credentials, permissions, and personal memory do not belong in it.

`pc_dr` is the complement. It carries the operational half: service stacks, self-healing, monitoring, backup, scheduled maintenance, and the doctrine that governs operating a real always-on lab through an agent.

### What was adopted as design

- Multidimensional authority: operational status, authority, and confidence are separate axes, never collapsed into one field.
- Frontmatter-driven doctrine with **both** positive (`consult_when`) and negative (`do_not_use_when`) retrieval triggers.
- A generated router (`index.md`) that is never independently edited and never becomes an authority of its own.
- One canonical editable home per operative rule.
- A mechanical publish gate rather than reviewer diligence alone.
- A one-way private-to-public projection policy with no parity-commit obligation.

### What was written independently

- All doctrine content. It is generalized from operating a real lab, not adapted from the source project's doctrine pages.
- `SANITIZATION.md` and `scripts/check_sanitization.py`. The source project greps a handful of secret patterns; publishing infrastructure rather than prose requires a deny-by-default model with an external identity denylist.
- `scripts/generate_index.py`, `scripts/check_template.py`, and `scripts/render.py` — reimplemented from scratch with a stdlib-only frontmatter parser and no fixed doctrine-page count.
- Everything under `reference/`, `stacks/`, `watchdogs/`, `automation/`, and `agent/`.

### Attribution policy

References identifying the source project are **provenance and are meant to remain**. They are not an identity for an adopting agent to inherit. No relationship, permission, credential, or authority transfers by copying a template.

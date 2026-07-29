# pc_dr — Agent-Operated Homelab Template

A runtime-neutral template for a **single-board-computer homelab operated by an AI agent**: identity, doctrine, service stacks, watchdogs, monitoring, backup, notification discipline, and scheduled maintenance.

This repository ships **parameterized templates and generalized judgment**. It contains no credentials, no private addressing, no personal records, and no live configuration. Every environment-specific value is a placeholder resolved from your own `vars.yml`.

## What this is

Most agent starter kits give an agent a personality. This one gives an agent a **job**: keep a real always-on lab running, with a defensible record of why it is built the way it is.

| Layer | Purpose |
|---|---|
| `SOUL.md` | Always-loaded identity: an operator agent with production responsibility |
| `GOVERNANCE.md` | Placement, authority, status, confidence, and revision rules |
| `doctrine/` | On-demand judgment for consequential operations problems |
| `index.md` | Generated problem router; never edited by hand |
| `reference/` | Topology and service reference, as templates |
| `stacks/` | Parameterized container stacks |
| `watchdogs/` | Self-healing units and the shared watchdog contract |
| `automation/` | Scheduled maintenance and home-automation patterns |
| `agent/` | Agent runtime config shape, skills, and hooks |
| `SANITIZATION.md` | Threat model and deny classes for publishing from a live lab |
| `SYNC.md` | One-way private-to-public projection policy |
| `scripts/` | Deterministic generation and integrity checks |

## What this is not

- Not a mirror of a private lab. It is a curated projection. See `SYNC.md`.
- Not a source of truth for any running system. Rendered output is, and it stays private.
- Not proof of good judgment. A repository that validates cleanly can still be wrong.

## Give this to a blank agent

> Read `ADOPT.md` in this repository and follow it. Use `SOUL.md` as your initial identity and `index.md` as the router for operating doctrine. Treat every capability, host, credential, and permission as unavailable until you have verified it in *my* environment. Do not assume any address, hostname, container, or service in this template exists here.

## Quick start

```bash
python3 scripts/generate_index.py
python3 scripts/check_template.py
```

To use it for a real lab:

```bash
cp vars.example.yml ../pc_dr-src/vars.yml   # keep this OUTSIDE the repo
python3 scripts/render.py --vars ../pc_dr-src/vars.yml --out ../pc_dr-src/rendered
```

Rendered output is private by definition. It must never be committed here.

## Before you publish anything derived from your own lab

Read `SANITIZATION.md` first. The short version: **generate public artifacts from hand-authored templates; never copy a live file and scrub it.** Scrubbing a copy is the leak path — one missed pattern is permanent once it is in git history.

```bash
python3 scripts/check_sanitization.py
```

## Zero dependencies

Python 3.8+, standard library only. No YAML library, no package install, no network access required for validation.

## License and lineage

MIT. The governance model, frontmatter-driven router, and mechanical publish gate are adapted with thanks from [`bobert-agent-template`](https://github.com/robertaustinbell/bobert-agent-template) (MIT). See `LINEAGE.md`. That project deliberately carries identity and judgment only; this one carries the operational half.

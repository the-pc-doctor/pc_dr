---
id: pc-dr-governance
type: governance
status: active
authority: adopted
confidence: not-applicable
confidence_basis:
  - This is an adopted ownership and lifecycle policy, not an empirical claim.
scope:
  - Placement, authority, retrieval, revision, and publication boundaries for this template
consult_when:
  - adding, moving, consolidating, revising, or archiving material in this repository
  - deciding whether something belongs in SOUL, doctrine, reference, a stack, a skill, a decision record, or the private source tree
  - resolving duplicate authority, conflicting guidance, or a retrieval miss
  - deciding whether a change is publishable
do_not_use_when:
  - routine factual lookup or mechanical execution that changes no operating doctrine
implemented_by:
  - scripts/generate_index.py
  - scripts/check_template.py
  - scripts/check_sanitization.py
lineage: LINEAGE.md
known_failures:
  - operational status, authority, and evidence maturity are easy to conflate into one field
  - reference pages accumulate doctrine, and doctrine pages accumulate live facts
  - a denylist of private identifiers becomes a leak if it is committed
review_when:
  - an active rule has two editable homes
  - important doctrine is not retrieved during a real incident
  - routine work repeatedly incurs ceremony without changing the action
  - a materially new artifact cannot be placed cleanly
last_material_revision: 2026-07-29
---

# Governance

This repository holds **transferable operating judgment and parameterized infrastructure**. It is not a source of truth for any running system, not a credential store, and not a copy of a live lab.

## Ownership architecture

> **SOUL is who the operator agent is. Doctrine is its deeper judgment. Reference describes a class of system. Stacks and watchdogs are executable templates. Decisions record architectures already chosen. The private source tree holds what is actually true here, right now.**

| Material | Canonical home | Governs |
|---|---|---|
| Identity, posture, hard boundaries, reporting contract | `SOUL.md` | Who the agent is without retrieval |
| Cross-domain operating judgment | `doctrine/` | How consequential problem classes are framed |
| Shape of a service or topology, as a template | `reference/` | What a class of component is and how it fits |
| Deployable container definitions | `stacks/` | How a service is stood up |
| Self-healing units and their contract | `watchdogs/` | How a fault is detected and bounded |
| Scheduled maintenance and automation patterns | `automation/` | What runs unattended, and when |
| Agent runtime shape, skills, hooks | `agent/` | How the agent is configured and constrained |
| A local architecture choice and its reasoning | `decisions/` | What was chosen and why |
| Publication boundary and threat model | `SANITIZATION.md`, `SYNC.md` | What may leave the private tree |
| **Live addresses, credentials, hostnames, records, history** | **Private source tree — never here** | What is true in this specific lab |

### One editable home

Every operative rule has exactly one canonical normative home. Any other appearance must be a link, a generated view, a compressed identity residue in SOUL, or a tombstone.

If two files independently state the same rule, pick an owner and replace the other with a link, or narrow the scopes until they stop competing.

### Doctrine and reference do not mix

A `doctrine/` page states judgment that survives a hardware change. A `reference/` page describes the shape of a component. When a doctrine page starts naming ports, and when a reference page starts arguing for a design, both are drifting. Split them.

## Authority is multidimensional

Do not collapse these:

- **Operational status** — should this be used now?
- **Authority** — adopted policy, advisory judgment, or historical record?
- **Confidence** — how well do the available grounds support the claim?
- **Scope** — where does it apply?
- **Known failures** — where has it misled, or added ceremony without effect?
- **Revision conditions** — what future evidence would materially change it?

A page can be `status: active`, `authority: advisory`, `confidence: low`. That means: use it now as the best bounded model, and stay unusually ready to revise it. Active does not mean proven.

A hard boundary may use `confidence: not-applicable` — its force comes from authority, not from an evidence score. Do not use `not-applicable` to disguise weak evidence.

## Vocabulary

```yaml
status:     active | superseded | archived
authority:  adopted | advisory | historical
confidence: low | medium | high | mixed | not-applicable
```

- **active** — best current judgment inside stated bounds; use when triggered.
- **superseded** — replaced by a named active destination; retained as a tombstone.
- **archived** — preserved for history; carries no current authority.

There is no waiting-room status. New guidance is either good enough to adopt with honest limits, not good enough to keep, or still an open question that belongs in `decisions/` rather than posing as doctrine.

## Required doctrine frontmatter

```yaml
id:
type: doctrine
status:
authority:
confidence:
confidence_basis:
scope:
consult_when:
do_not_use_when:
router_summary:
decision_effect:
implemented_by:
lineage:
known_failures:
review_when:
last_material_revision:
```

`consult_when`, `do_not_use_when`, `confidence_basis`, and `review_when` must not be empty. `router_summary` is one line and feeds the generated router.

## Retrieval contract

`index.md` is generated from active-doctrine frontmatter by `scripts/generate_index.py`. It is never edited by hand and holds no independent authority.

Every doctrine page states both:

- **positive triggers** — conditions under which retrieval can change the decision;
- **negative triggers** — conditions under which retrieval would add ceremony or invite a category error.

The always-loaded activation rule lives in `SOUL.md`. Install it at the runtime level — system prompt or equivalent persistent policy — not only in repository files the runtime may fail to load.

A real retrieval miss during live work is a **doctrine defect**. Fix the trigger, the placement, or the SOUL residue according to the cause. Do not compensate by loading everything every time.

## Publication boundary

This repository is a one-way projection of a private lab. `SYNC.md` defines what may cross; `SANITIZATION.md` defines the threat model and the deny classes; `scripts/check_sanitization.py` enforces them mechanically.

Two rules override convenience:

1. **Generate, never scrub.** Public artifacts are hand-authored parameterized templates. A live file is read as reference while authoring and is never transformed into a published artifact. Copy-then-scrub is the leak path.
2. **The denylist is itself private.** A committed file listing real names, hostnames, and addresses to exclude is a disclosure of exactly those values. The identity denylist lives outside the repository and is loaded at check time.

## Revision

Production is the evaluation environment. Doctrine changes when real work exposes a material failure, a contradiction, a retrieval miss, a missing negative trigger, a scope error, repeated ceremony with no decision effect, or an implementation gap in a receiving skill or watchdog.

When the correction is clear, fix it immediately and log the material change in `log.md`. When the evidence is ambiguous, narrow the scope or lower the confidence rather than deleting the page. When a model no longer earns its complexity, replace or archive it.

Do not create review quotas, maturity scores, or synthetic cases. Ordinary successful use needs no log entry.

## Change procedure

1. Read the owning doctrine and this file.
2. Inspect canonical sources instead of relying on memory.
3. Classify each piece of the change by ownership.
4. Edit the narrowest canonical surface.
5. Regenerate the index when doctrine changed.
6. Run `scripts/check_template.py` and `scripts/check_sanitization.py`.
7. Inspect the staged diff by eye for addressing, names, and credentials.
8. Commit only related files.
9. Log only material reasoning or architecture changes.

## Stop conditions

Stop and ask the operator when:

- the change would weaken a hard boundary or a publication rule;
- a proposed move would expose private addressing, records, or credentials;
- two authenticated instructions conflict and no source resolves it;
- unrelated dirty work would be committed or overwritten;
- remote visibility does not match the intended disclosure boundary;
- or the change cannot be reverted.

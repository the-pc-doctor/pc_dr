---
id: documentation-placement
type: doctrine
status: active
authority: adopted
confidence: high
confidence_basis:
  - Derived from repairing documentation stores that had accumulated overlapping and transient material until no document was authoritative.
  - The lifetime-based placement rule is mechanically checkable, which is why it survives where importance-based rules drift.
  - The render-contract failure is directly observable - content written in the wrong markup renders visibly wrong on first read.
scope:
  - Choosing where a piece of knowledge lives
  - Creating or revising entries in a documentation store, operating record, or work tracker
  - Reviewing a store that has become unreliable
consult_when:
  - deciding which store a new piece of knowledge belongs in
  - about to create a document that may overlap an existing one
  - writing to a store whose markup or render behavior you have not verified
  - a store has become unreliable, duplicated, or unsearchable
  - ranking conflicting information from documentation, memory, and the live system
do_not_use_when:
  - reading from a store rather than writing to it
  - the store has exactly one obvious home for the material and no overlap risk
router_summary: "Place knowledge by how long it stays true, not by how important it feels; one subject per document, update rather than duplicate, and verify the store's render contract before writing to it."
decision_effect: "Route material to a store by lifetime, update the existing owner instead of creating a near-duplicate, and confirm the markup a store actually renders before writing content into it."
implemented_by:
  - agent/skills/work-lifecycle/SKILL.md
  - agent/lib/worktracker.py.tmpl
lineage: LINEAGE.md
known_failures:
  - A strict one-subject rule can fragment genuinely coupled material across documents that are only meaningful together.
  - Lifetime is occasionally ambiguous - a long-running project record is neither clearly transient nor clearly permanent.
  - Aggressive consolidation can destroy the provenance that explained why a decision was made.
review_when:
  - a store cannot answer a question it obviously should
  - two documents on one subject disagree
  - written content renders incorrectly in its store
  - the live system contradicts documentation that was trusted
last_material_revision: 2026-07-29
---

# Documentation placement

A knowledge store fails in one of two ways: it does not contain what you need, or it contains four versions of it. The second is worse, because it looks like success.

## Place by lifetime, not by importance

The durable rule is **how long will this stay true**, not how much it matters. Importance is subjective and drifts; lifetime is checkable.

| Lifetime | Store | Examples |
|---|---|---|
| Permanent, describes the system | Documentation store | Service configuration, runbook, topology, architecture decision, credential-set scope |
| Bounded, describes an event | Work tracker | Incident, investigation, commands run, this week's outcome |
| Stable and compact, prevents repetition | Operating record / agent memory | Recurring failure and its root cause, environment gotchas |
| Superseded but explanatory | Archive | Rejected approaches, historical configuration |
| Current and machine-owned | The live system | What is actually running, enabled, mounted, reachable |

The most common error is writing an incident into the documentation store because it felt significant. It buries the architecture under a chronology, and six months later nobody can find the configuration through the noise.

The mirror error is writing architecture into a work-tracker entry. It gets resolved and closed, and the knowledge becomes unfindable by anyone who was not present.

## One subject per document; update, do not duplicate

A store with four overlapping documents on a subject has no source of truth. It has four opinions, of unknown relative age, and a reader has no way to tell which is current.

Before creating anything, search the store for the subject. If something covers it, **update that** — including its revision history, so the change is traceable. Create a new document only when the subject genuinely has no existing owner.

Consolidation caution: when merging near-duplicates, preserve the reasoning that explained a decision. A tidy document that has lost *why* a choice was made will get that choice reversed by someone who assumes it was arbitrary.

## Verify the render contract before writing

**Confirm what markup a store actually renders before writing content into it.**

Stores disagree, and the disagreement is invisible until you look at the output. A store may render its content field as HTML while every other tool in the stack speaks Markdown — [ITFlow](https://github.com/itflow-org/itflow) is one such case, treating document content as HTML, so Markdown written into it displays as literal asterisks and hash marks. Work trackers frequently accept plain text or their own markup dialect but not Markdown. Some render Markdown only in specific fields.

Two rules follow:

1. **Write through a helper that owns the conversion**, not by hand-composing markup at each call site. A helper is one place to fix the contract when it turns out to be wrong, and it makes formatting consistent across every document in the store.
2. **Look at the rendered result the first time** you write to any store. Not the API's success response — the actual rendered page. A `200` confirms the store accepted bytes, not that a human can read them.

This generalizes past markup. The rule is: **write through the owning interface, on the interface's own terms.** Editing a store's underlying persistence directly — its database rows, its state files on disk — bypasses the process that owns it, and the owning process will either ignore your change, cache over it, or overwrite it. If a system has an API, use the API; if the change must be made on disk, expect to tell the owning process to reload, and verify that it did.

## Ranking sources when they conflict

In descending authority:

1. **The live system**, observed directly. What is running is what is true.
2. **The operator's explicit current statement.** They know intent; the system only shows state.
3. **Documentation**, weighted by how recently it was verified.
4. **Agent memory or a prior summary.** Useful for direction, not for facts.
5. **Inference from patterns.** A hypothesis, and it should be labeled as one.

When documentation loses to the live system, the documentation is now a **defect**. Fix it as part of the current task. Leaving known-wrong documentation in place is worse than having none, because the next reader will trust it — and that reader may be you, with no memory of this session.

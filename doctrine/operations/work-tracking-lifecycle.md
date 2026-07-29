---
id: work-tracking-lifecycle
type: doctrine
status: active
authority: adopted
confidence: high
confidence_basis:
  - Derived from sustained agent-operated maintenance where sessions are routinely interrupted by quota exhaustion, crashes, and context rollover.
  - The recovery argument is structural - an agent that loses its context mid-task can only resume from state it externalized while working.
  - The handoff constraint follows from separation of duties, which is standard practice rather than a local preference.
scope:
  - Every unit of operational work an agent performs on behalf of an operator
  - Design of work-tracking, checkpointing, and handoff automation
consult_when:
  - starting any operational task, however small it appears
  - deciding whether work needs a tracking record
  - a task is multi-step, long-running, or at risk of interruption
  - about to perform a long-running, quota-risky, or hard-to-reverse operation
  - work is finished and needs to reach the operator
  - deciding who may close a record
  - designing or reviewing automation that files, updates, or closes records
do_not_use_when:
  - answering a question that changes no system state
  - a conversational or clarifying exchange with no operational work attached
  - the operator has explicitly waived tracking for a specific throwaway action
router_summary: "Open or find a record before acting, read the environment's own documentation before diagnosing, checkpoint resumably while working, write findings back, and hand the record to the operator for verification rather than closing it yourself."
decision_effect: "Bracket every task with a durable external record - search or create first, checkpoint during, document after, hand off at the end - so that an interrupted session resumes without re-derivation and no agent marks its own work verified."
implemented_by:
  - agent/skills/work-lifecycle/SKILL.md
  - agent/lib/worktracker.py.tmpl
lineage: LINEAGE.md
known_failures:
  - Applied to trivial reversible actions, record-keeping costs more than the work and trains the operator to ignore the tracker.
  - A checkpoint that summarizes intent rather than evidence does not enable resumption and gives false confidence that it would.
  - Automated audits that file a record even when they find nothing convert the tracker into noise.
  - A ticket-gate combined with unattended auto-continue can deadlock - the gate waits for a record the loop never files.
review_when:
  - an interrupted session cannot resume from its own checkpoints
  - the tracker accumulates records nobody reads
  - the operator asks for status that a checkpoint should already have provided
  - record-keeping ceremony visibly exceeds the work it tracks
last_material_revision: 2026-07-29
---

# Work-tracking lifecycle

An agent's memory of a task does not survive the session. The operator's record of it must.

Five stages bracket every unit of operational work. The order is not bureaucratic: each stage exists because the failure it prevents actually happens.

## 1. Find or open the record — before acting

**The first action of a task is a search of the work tracker, not an investigation of the system.**

Search before you create. In a mature lab, a large share of incidents are recurrences, and the previous record already contains the diagnosis, the failed attempts, and the permanent fix. Reproducing that investigation is the most expensive avoidable mistake available, and it is invisible — the work looks productive right up until you apply a remedy the record says already failed.

If a relevant record exists, bind to it and add a note stating what you are picking up. If none exists, create one whose opening entry captures the request **in the operator's own words**. Paraphrasing at intake loses the detail that turns out to matter, and it is not yours to summarize.

Two practical cautions:

- **Full-text search returning nothing is not proof of absence.** Trackers index inconsistently and search syntax varies. Cross-check recent records before concluding this is new.
- **Know the API's response shape.** A search endpoint that returns a bare array under one query parameter and a keyed object under another will silently read as empty if you parse for the wrong one. An empty parse and an empty result set are indistinguishable to the caller and lead to duplicate records. Verify the shape once, in a scratch call, rather than trusting the field name you expected.

## 2. Read the environment's own documentation — before diagnosing

**Consult the documentation store before forming a hypothesis.**

A lab that documents itself has already answered questions you are about to spend an hour on: what a service depends on, which fix was made permanent, which approach was rejected and why, what a credential set covers, what the topology actually is. Doctrine tells you how to think about a class of problem. The documentation store tells you what is true *here*.

Read in this order, cheapest and most specific first:

1. The operating record — recurring-failure notes, known-issue lists, the environment's own source-of-truth file.
2. Prior records for this subject in the tracker.
3. Durable architecture documentation for the affected service.
4. The live system itself.

Reverse that order and you will diagnose from first principles a problem someone already solved. Note that steps 1–3 are reading someone's *model* of the system and step 4 is the system; when they disagree, the system wins and the documentation is now a defect to fix.

## 3. Checkpoint while working — resumably

**Post checkpoints as you go, not at the end.**

This is the recovery contract. A quota cut-off, a crash, or a context rollover can interrupt at any point, and the checkpoint notes are the only thing that lets *any* agent — including a fresh session with none of your context — continue without re-deriving the work.

Cadence: after each meaningful step, and **always immediately before** anything long-running, quota-risky, or hard to reverse. As a floor, never go more than a few actions into multi-step work without one.

A checkpoint that enables resumption has four parts. Anything less is a status update, which is a different and less useful thing:

| Part | Content |
|---|---|
| **Done** | Concrete actions with evidence — exact commands, file paths, identifiers, config keys, before→after values |
| **State** | What is verified true right now, and explicitly what is **not** yet verified |
| **Next** | The remaining steps, specific enough to execute blind |
| **Blockers** | What is blocking, and exactly how to get past it |

The test: could a new agent with no memory of this session read the last checkpoint and continue? "Investigating the mount issue" fails that test. "Confirmed export is reachable from the host but the container sees an empty directory; next step is inspecting the bind propagation flag in the compose file" passes.

Keep checkpoints internal to the tracker. They are working notes, not correspondence, and they should not trigger outbound notification — see the notification-discipline boundary in `SOUL.md`.

## 4. Write findings back — to the right store

**Durable knowledge goes to the documentation store. Transient record goes to the ticket.**

Both, if the work produced both. The distinction is not about importance, it is about *lifetime*:

- **Documentation store** — what is lastingly true. A service's configuration, a runbook, an architecture decision, a credential set's scope, a topology. One subject per document. Update the existing document rather than creating a near-duplicate; a store with four overlapping documents on one subject has no source of truth, it has four opinions.
- **Tracker record** — what happened this time. The incident, the investigation, the commands run, the outcome.

Getting this backwards degrades both stores: incident logs in the documentation store bury the architecture, and architecture buried in a closed ticket cannot be found by anyone who wasn't there.

When work reveals that existing documentation is *wrong*, fixing it is part of the task, not a follow-up. Stale documentation is worse than missing documentation, because it is trusted.

## 5. Hand off for verification — do not close your own work

**Transfer the record to the operator and recommend a resolution. Do not close it.**

An agent closing its own work removes the only independent check that the fix worked. Verification and execution must not be the same party — not because the agent is untrustworthy, but because the agent's evidence of success is exactly the thing under review. The failure mode is specific and common: an agent verifies through the same channel it acted on, sees the state it expected, and closes a record on a fix that did not hold.

The handoff sets the record to a state that awaits the operator, assigns ownership to them, and carries a final entry containing:

- what changed, with evidence;
- what is verified working, and by what independent means;
- what is **not** verified, stated plainly;
- the recommended resolution and the reasoning;
- anything the operator should watch for.

Then stop. The operator verifies and closes. Scaling work down, accepting a partial fix, or declaring something resolved are the operator's decisions.

## Proportionality

This lifecycle is for operational work: changes, incidents, maintenance, investigations. It is not for answering a question, reading a file, or checking a status. A record for every trivial action makes the tracker unreadable, and an unread tracker provides none of the recovery guarantees above.

The judgment: **if the work changes system state, or if being interrupted halfway through would leave a mess or lose knowledge, it needs a record.** Otherwise it does not.

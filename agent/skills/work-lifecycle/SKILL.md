---
name: work-lifecycle
description: The mandatory five-stage procedure for every unit of operational work - find or open a tracking record before acting, read the environment's own documentation before diagnosing, checkpoint resumably while working, write durable findings back to the documentation store, and hand the record to the operator for verification. Use at the start of any task that changes system state, and at every stage boundary within it. Do not use for questions that change nothing.
---

# Work lifecycle

Doctrine: `doctrine/operations/work-tracking-lifecycle.md`, `doctrine/knowledge/documentation-placement.md`
Helper: `agent/lib/worktracker.py` (rendered from `agent/lib/worktracker.py.tmpl`)

Five stages. The order is load-bearing. Each stage exists because the failure it prevents actually happens.

## Applies when

The work **changes system state**, or being interrupted halfway would leave a mess or lose knowledge.

Skip it for questions, file reads, and status checks. A record for every trivial action makes the tracker unreadable, and an unread tracker provides none of the recovery guarantees below.

---

## Stage 1 — Find or open the record, before acting

**The first action of a task is a tracker search, not a system investigation.**

```bash
python3 agent/lib/worktracker.py find "<subject keywords>"
```

Then:

- **Match exists** → bind to it. Post a note stating what you are picking up. Read the whole record first, especially the failed attempts.
- **No match** → create one. The opening entry carries the request **verbatim**.

```bash
python3 agent/lib/worktracker.py open "<short descriptive title>" \
    --body "<the operator's request, word for word>"
```

Do not paraphrase at intake. Summarizing loses the detail that turns out to matter, and the wording is the operator's.

**Two traps:**

- An empty search result is **not proof of absence**. Trackers index inconsistently. Cross-check recent records before concluding the subject is new.
- Verify the search endpoint's **response shape** once, in a scratch call. A bare array versus a keyed object parses as "empty" if you guess wrong — and an empty parse looks exactly like no results, which is how duplicate records get created. The helper handles both shapes; hand-rolled calls often do not.

**Gate:** do not investigate, edit, restart, or install until a record exists and you know its id.

---

## Stage 2 — Read the environment, before diagnosing

**Consult what the environment already knows before forming a hypothesis.**

```bash
python3 agent/lib/worktracker.py context "<service or subject>"
```

Read cheapest and most specific first:

1. The operating record — recurring-failure notes, known-issue lists, the environment's source-of-truth file.
2. Prior tracker records for this subject, including their failed remedies.
3. Durable documentation for the affected service — dependencies, config, runbook, past decisions.
4. The live system.

Doctrine tells you how to think about a class of problem. **Documentation tells you what is true here.** Reverse this order and you will re-derive a solved problem from first principles, applying a remedy the record already says failed — the most expensive avoidable mistake available, and invisible, because the work looks productive.

Steps 1–3 are someone's *model* of the system; step 4 is the system. **When they disagree, the system wins** and the documentation is now a defect to fix in stage 4.

**Gate:** you can state what is already known about this subject, and what was already tried.

---

## Stage 3 — Checkpoint while working, resumably

**Post checkpoints as you go, not at the end.** This is the recovery contract: a quota cut-off, crash, or context rollover can interrupt at any point, and these notes are the only thing letting any agent — including a fresh session with none of your context — continue without re-deriving the work.

```bash
python3 agent/lib/worktracker.py checkpoint <id> \
    --done     "commands run, files touched, before→after values" \
    --state    "what is verified true now; what is NOT yet verified" \
    --next     "the remaining steps, executable blind" \
    --blockers "what is blocking and exactly how to get past it"
```

**Cadence:** after each meaningful step, and **always immediately before** anything long-running, quota-risky, or hard to reverse. Floor: never more than a few actions into multi-step work without one.

**The test:** could an agent with no memory of this session read your last checkpoint and continue?

| Fails | Passes |
|---|---|
| "Investigating the mount issue." | "Export is reachable from the host but the container sees an empty directory; next is the bind-propagation flag in the compose file." |
| "Made some progress on the proxy." | "Rewrote the location block, reloaded twice (first reload is a no-op on this build); LAN path returns 200, WAN path still 502." |

Checkpoints are internal working notes. They do not trigger outbound notification.

---

## Stage 4 — Write findings back, to the right store

Route by **lifetime**, not by importance. Do both when the work produced both.

**Durable → documentation store.** What stays true: service configuration, runbook, topology, an architecture decision, a credential set's scope.

```bash
python3 agent/lib/worktracker.py document "Service: <name>" --file notes.md
```

- **One subject per document.** Search first; update the existing owner rather than spawning a near-duplicate. Four overlapping documents on one subject means four opinions of unknown relative age.
- **The helper owns the render contract.** ITFlow treats document content as HTML, so Markdown written straight in renders as literal asterisks. Pass plain Markdown to the helper and let it convert; never hand-compose markup at the call site, and never write to the store's database directly.
- **Look at the rendered page** the first time you write to any store. A `200` means bytes were accepted, not that a human can read them.
- If stage 2 turned up documentation that was **wrong**, fixing it is part of this task. Stale documentation is worse than none, because it is trusted — and the next reader may be you, with no memory of this session.

**Transient → the tracker record.** The incident, the investigation, the commands, the outcome. Never architecture: it gets closed and becomes unfindable.

---

## Stage 5 — Hand off for verification; do not close

**Transfer the record to the operator and recommend a resolution.**

```bash
python3 agent/lib/worktracker.py handoff <id> \
    --summary      "what changed, with evidence" \
    --verified     "what is confirmed working, and by what independent means" \
    --not-verified "what is NOT confirmed - required, never empty" \
    --recommend    "recommended resolution and reasoning"
```

This assigns ownership to the operator and sets a state that awaits them. It **does not close the record**, and there is no close command.

Verification and execution must not be the same party — not because the agent is untrustworthy, but because the agent's evidence of success is exactly what is under review. The specific failure: an agent verifies through the same channel it acted on, sees the state it expected, and closes a record on a fix that did not hold.

Independent means matter. A camera frame beats an entity state; a different sensor beats the same integration reporting back to itself. See `doctrine/reliability/verification-before-claiming-done.md`.

`--not-verified` is mandatory. If everything genuinely was verified, say so explicitly — the field exists to stop an unverified remainder from being quietly omitted.

Then **stop**. The operator verifies and closes. Accepting a partial fix, scaling the work down, and declaring something resolved are their decisions.

---

## Failure modes to avoid

| Anti-pattern | Why it fails |
|---|---|
| Investigate first, file the record afterward | The record exists to prevent the duplicate investigation you just performed |
| One checkpoint at the end | Provides zero recovery value; the interruption it guards against happens mid-task |
| Checkpoint stating intent, not evidence | Cannot be resumed from, and gives false confidence that it could |
| Incident narrative in the documentation store | Buries the architecture under a chronology |
| Architecture in a tracker record | Gets closed; becomes unfindable to anyone not present |
| Agent closes the record | Removes the only independent check on its own work |
| Automated audit files a record with nothing to report | Turns the tracker into the noise it exists to surface signal from |
| Record-keeping for trivial reversible actions | Trains the operator to ignore the tracker |

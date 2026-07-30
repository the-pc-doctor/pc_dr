# Records: work tracker and documentation store

The two stores the work lifecycle depends on. Together they are what lets an interrupted session resume and a solved problem stay solved.

Reference implementations: [Zammad](https://github.com/zammad/zammad) for the work tracker; [ITFlow](https://github.com/itflow-org/itflow) for the documentation store, images `itflow` and `mariadb`.

Doctrine: `doctrine/operations/work-tracking-lifecycle.md`, `doctrine/knowledge/documentation-placement.md`. Implementation: `agent/lib/worktracker.py.tmpl`.

## Placement

These belong **off the core host** where possible — typically on the storage host. Two reasons:

1. They are how you find out what happened during an incident. A tracker that is down because the core host is down is useless exactly when needed.
2. Both are database-backed and comparatively memory-hungry, which is the resource a small board has least of.

The tradeoff is honest: they now depend on the storage host and its own availability. Neither is a named critical service, so this is acceptable.

## Work tracker

**Health:** the API responds to an authenticated request. A web UI that loads proves less than one authenticated API call.

**How it fails:**

- **Search returns nothing when matches exist.** Full-text indexing can lag or miss, and the search endpoint's response shape varies with query parameters — a bare array under one form, a keyed object with an assets map under another. Parsing for the wrong shape is indistinguishable from an empty result and produces duplicate records. Handle both shapes and cross-check recent records before concluding a subject is new.
- **Authentication failing silently in automation.** A poller with stale credentials logs errors nobody reads and quietly stops filing anything. Monitor that records are still being created, not merely that the service is up.
- **Automated audits flooding it.** A recurring job that files a record on every clean run makes the tracker unusable for real work. Audits with nothing to report produce nothing.

**State model:** the agent files, updates, and hands off. It does not close. Handoff sets an owner and a state that awaits the operator — see the lifecycle doctrine.

## Documentation store

**Health:** the API responds, and a document round-trips — write, read back, and **look at the rendered page**.

**How it fails:**

- **Render contract mismatch.** ITFlow treats document content as HTML, not Markdown. Markdown written straight in renders as literal asterisks and hash marks. Write through a helper that owns the conversion, and inspect the rendered output the first time you write to any store. A `200` means bytes were accepted, not that a human can read them.
- **Access-path assumptions.** A store configured for HTTPS-only will refuse or misbehave on a plain-HTTP port that still appears to be listening. Confirm the working access path and record it; do not assume the container's exposed port is the supported entry point.
- **Duplicate accumulation.** Without a search-before-create discipline, near-duplicate documents pile up until no document is authoritative. One subject per document, and update the existing owner.
- **Transient content pollution.** Incident logs, session summaries, and one-off troubleshooting notes written here bury the architecture. Those belong in the tracker.

## The division

| Goes to the tracker | Goes to the documentation store |
|---|---|
| This incident | What the service is and how it is configured |
| Investigation and commands run | The runbook |
| Checkpoints during work | The architecture decision and why |
| The handoff and its evidence | Credential-set scope and where secrets live |
| An audit finding | Topology |

The test is lifetime, not importance. A major incident is still transient; a boring port assignment is still permanent.

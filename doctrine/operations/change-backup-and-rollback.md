---
id: change-backup-and-rollback
type: doctrine
status: active
authority: adopted
confidence: high
confidence_basis:
  - The sequencing rules are standard change-management practice, independently supported outside this environment.
  - The unverified-backup failure and the reload-after-edit failure were both observed directly in a running lab.
  - Failure is asymmetric - the cost of an unnecessary backup is seconds, the cost of a missing one is unbounded.
scope:
  - Any change to configuration, state, or infrastructure
  - Design and verification of backup and restore procedures
consult_when:
  - about to edit configuration, state, or infrastructure
  - about to make a change that is hard or impossible to reverse
  - planning a change touching a named critical service
  - designing or reviewing a backup or restore procedure
  - a change did not take effect despite the file being correct
  - several changes need to land and one of them may be the culprit
do_not_use_when:
  - the action is a read with no state change
  - the change is trivially reversible and already under version control with a clean tree
router_summary: "Back up before editing, change the narrowest surface that can work, land one change at a time when attribution matters, tell the owning process to reload, and verify the effect rather than the file."
decision_effect: "Bracket every change with a restorable snapshot and an explicit post-change verification, and treat an untested restore as no backup at all."
implemented_by:
  - watchdogs/lib/watchdog_common.sh
lineage: LINEAGE.md
known_failures:
  - Applied uniformly, backup ceremony on trivial reversible edits wastes time and trains the operator to skip it when it matters.
  - Timestamped backup copies accumulate until they themselves become a storage-pressure problem.
  - One-change-at-a-time is wrong during an outage when several known-good fixes should land together to restore service.
review_when:
  - a restore is attempted and fails
  - a change is found not to have taken effect despite a correct file
  - backup artifacts contribute to a storage incident
  - change ceremony is visibly slowing incident response
last_material_revision: 2026-07-29
---

# Change, backup, and rollback

Most infrastructure damage is not caused by a bad change. It is caused by a bad change that could not be undone.

## Before

**Back up before you edit.** Not for changes that look risky — for changes. The judgment about which edits are risky is made with the information you have *before* you understand the problem, which is exactly when it is worst.

A backup that is useful for rollback is:

- **Taken immediately before the edit**, not last night;
- **Named for its reason**, so the intent survives — a filename carrying the reason and a timestamp beats a numbered sequence nobody can decode a month later;
- **On a different failure domain** than the thing it protects, when the change could take out storage;
- **Verified restorable**, at least once, for anything you would actually need.

**An unverified backup is a belief, not a backup.** A restore procedure that has never been executed is an assumption about file formats, permissions, ownership, and completeness. Test it on a schedule, on a copy, and record what the test showed. Ownership is a common quiet failure: files restored as the wrong user leave a service unable to read its own configuration, and the error surfaces as something unrelated.

## During

**Change the narrowest surface that can work.** Prefer the specific setting over the file, the file over the directory, the service over the host. The narrower the change, the smaller the space you have to search when something breaks.

**Land one change at a time when attribution matters.** If three edits go out together and the service breaks, you have three suspects and no way to separate them without undoing all three. The exception is a live outage where several known-good fixes should land together to restore service — restore first, attribute after.

**Prefer reversible mechanisms.** A setting is better than a patch; a patch is better than a rewrite; a rewrite is better than a deletion. When you must do the irreversible thing, do the reversible things first and confirm they were insufficient.

## Write through the owner

**Editing a file is not making a change.** The owning process holds its configuration in memory, and a correct file it has not read is inert.

Three distinct failure shapes:

1. **The process must be told.** Edit, then reload or restart, then confirm the new value is live — not that the file contains it.
2. **The process owns the store.** Editing a running service's database or state files directly is bypassing the process that owns them; it will ignore, cache over, or overwrite your change. Use the API when there is one.
3. **The reload itself is unreliable.** Some services need more than one reload for certain change classes, or silently keep serving the old configuration when the new one fails to parse. Validate the configuration before reloading where the tool offers it, and verify the effect afterward regardless.

## After

**Verify the effect, not the file.** `grep` confirming your line is present proves you edited a file. It proves nothing about behavior.

For a named critical service, verification is mandatory and independent: confirm the service is up, confirm it is reachable **from the path that actually matters**, and confirm the specific behavior you changed. See `doctrine/reliability/verification-before-claiming-done.md`.

**Know your rollback before you need it.** Before the change, be able to state in one sentence how to undo it. If you cannot, that is the finding — stop and solve that first.

## Retention

Backup artifacts are not free. Timestamped copies alongside live configuration accumulate silently until they become the storage incident. Set a retention rule when you set the backup, and let something enforce it.

The same applies to snapshots, container images, and logs. Unbounded retention on a small disk is not caution; it is a scheduled outage.

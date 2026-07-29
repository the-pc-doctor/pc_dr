# Hooks

Harness hooks: work-tracking gate on task start, checkpoint on stop and before
context compaction.

Phase 4. Note the constraint that makes these publishable at all: a hook must
read credentials from an environment variable or a mode-0600 credential file.
A hook with an inline credential cannot be projected, and is a liability in the
private tree too.

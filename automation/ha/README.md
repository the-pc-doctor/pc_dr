# Home-automation patterns

Automation structure that stays editable in the platform UI: one included file,
every entry carrying a stable unique id, and no split-directory merge include.
Writing through the platform API rather than its persistence layer is the
general form of the rule — see `doctrine/reliability/`.

Phase 3.

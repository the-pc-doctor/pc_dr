# Home-automation patterns

`automations.example.yaml` carries four shape patterns: closed-loop actuation,
reconciliation against a missed edge trigger, a freshness guard against stale
entities, and an empty-group guard.

Two constraints keep automations editable in the platform UI:

1. Every automation has a stable unique `id`.
2. All automations live in the single file the main configuration includes — a
   split-directory merge include breaks the UI edit path, silently.

Prefer writing through the platform configuration API, which assigns and
preserves ids. Direct file edits need a backup first and a reload after, then a
check that the API can address the new entry.

This is the concrete case of a general rule: write through the owning interface,
not its persistence layer. See `doctrine/knowledge/documentation-placement.md`.

# Home automation platform

The integration hub. It owns device state, runs automations, and is usually the service people notice first when it is down.

Reference implementation: [Home Assistant](https://github.com/home-assistant/core), image `ghcr.io/home-assistant/home-assistant`.

## Depends on

- The container runtime and the core host.
- The message broker, for anything MQTT-based.
- Network reachability to local devices — often host networking, because discovery protocols (mDNS, SSDP) do not cross a bridge.
- External vendor clouds, for cloud-dependent integrations. Those inherit `doctrine/capabilities/external-capability-governance.md`.

## Depended on by

Dashboards, voice assistants, notification flows, and any automation that reads or writes device state. Also, usually, by the operator's expectation that the house works.

## Health

| Signal | Meaning |
|---|---|
| API responds | Process is alive. Not the same as functional. |
| Share of entities unavailable | The useful signal. A platform that is up with half its integrations dead is not healthy. |
| Integration reload succeeds | A specific integration's connection is recoverable |
| Automation last-triggered timestamps | Automations are actually firing, not merely enabled |

Probe the API *and* the unavailable-entity ratio. A liveness check alone will report green through the outage that matters.

## How it fails

**Restart loop.** A bad configuration or a failing integration causes repeated startup failure. Any watchdog covering this service must detect that it is restarting repeatedly and stop, rather than adding restarts — see `doctrine/reliability/watchdog-blast-radius.md`.

**Mass entity unavailability.** One integration losing its connection can mark hundreds of entities unavailable. The cause is one integration; the symptom is the whole platform looking broken. Reload the specific integration before restarting the platform.

**Stale entity state.** An entity that stops updating reports its last known value indefinitely, confidently. It will confirm whatever you hoped. See `doctrine/knowledge/source-authority.md`.

**Empty group.** A group, list, or collection resolving to no members accepts every command and does nothing, returning success each time. Verify membership, not existence.

**Configuration edited but not applied.** The platform holds config in memory. Validate the configuration, reload or restart, then confirm the new value is live — not that the file contains it.

## Automation storage

Two constraints that keep automations editable in the platform's own UI:

1. **Every automation carries a stable unique identifier.** Without one, the UI cannot address it for editing.
2. **All automations live in the single file the main configuration includes.** A split-directory merge include breaks the UI edit path, and the breakage is silent — the automations run, they just stop being editable.

Prefer writing through the platform's own configuration API, which assigns and preserves identifiers automatically. Direct file editing is acceptable when the API is unavailable; back up first, append with a unique identifier, reload, then confirm the API can address the new entry. If it cannot, the entry went to the wrong place.

This is the concrete case of a general rule: write through the owning interface, not its persistence layer. See `doctrine/knowledge/documentation-placement.md`.

## Registry and permissions

The platform's internal registries and storage directory are frequently owned by a privileged user. Editing them requires elevation, and **restoring the original ownership afterward is part of the edit** — files left owned by the wrong user leave the platform unable to read its own state, and the error surfaces as something unrelated.

Some changes, notably entity renames, require a full restart rather than a reload to take effect.

## Dashboards

Dashboards stored in the platform's internal storage cannot be updated by editing the file alone; the running process holds its own copy and will overwrite yours. Push the change through the platform's API.

Where dashboards are declared in configuration, each declaration usually needs a distinct URL path meeting the platform's format rules. A malformed path can drop the whole configuration into a recovery mode on the next full restart — which will happen at the next restart, not at the time of the edit, making it hard to attribute. Validate the configuration before restarting.

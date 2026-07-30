# Topology

Reference describes the *shape* of a system. It does not argue for a design — that belongs in `doctrine/`.

Every address, hostname, and port below is a placeholder resolved from your own `vars.yml`. Nothing here describes a real deployment.

## Tiers

```
  Internet
     │
  [ router / gateway ]  ──────────────  DNS + DHCP for the lab
     │
  [ switch ]
     │
     ├── core host        containers, agent runtime, watchdogs, scheduler
     ├── storage host     bulk media, recordings, backups, work tracker
     └── media host       playback and offload  (optional)
```

The core host is a single small board. That is the defining constraint of this architecture and the reason several rules elsewhere exist — see `doctrine/capabilities/architecture-constraints.md`.

## Dependency order

Restore in this order during an outage. Anything below a broken tier will report failures that are not its own fault.

| Tier | Component | If it is down |
|---|---|---|
| 0 | Power, router, switch | Everything. Nothing else is worth checking. |
| 1 | DNS resolution | Every name-based integration fails with generic timeouts, not name errors |
| 2 | Core host | All containers |
| 3 | Container runtime | All services |
| 4 | Reverse proxy / auth gateway | Everything reachable by name or from outside — but the services behind it are fine |
| 5 | Individual services | Only themselves and their dependents |

**The most common misdiagnosis in this shape is tier 4 reported as tier 5.** A service is healthy on the host and unreachable through its name, and the report arrives as "the service is down." Probe both paths before believing either — see `watchdogs/lib/watchdog_common.sh`.

## Failure domains

Things that fail *together* because they share something:

| Shared | Members |
|---|---|
| The core host | Every container on it. A host-level memory event takes unrelated services simultaneously. |
| The message broker | Every integration that publishes or subscribes through it. One broker restart looks like several integrations breaking at once. |
| Network storage | Recording, backup, and archive writers. Presents as *the service stopped working* with a perfectly healthy container. |
| The reverse proxy | Every named or externally reachable service. |
| The resolver | Every cloud integration, disguised as unrelated API timeouts. |
| Internet uplink | All cloud-dependent devices and any model provider without a local tier. |

When two things break together, look for the shared member before opening two investigations.

## Placement rules

**Separate by restart risk, not by category.** The reverse proxy and auth gateway must survive a restart of everything else, because they are how you get back in. The monitoring stack must not share a failure domain with what it monitors — a monitor that dies with the host reports nothing at the moment you need it most.

This is why `stacks/` is split rather than being one compose file. A single `docker compose down` that takes out your access path, your monitoring, and your recovery tooling at the same time is a bad afternoon.

**Bulk data goes to network storage.** Local flash on a small board is small and wears under continuous writes. Accept the mount as a new dependency and monitor it explicitly.

**Externally reachable services go behind the proxy and an auth gateway.** Do not expose service ports directly. Where a single certificate and hostname are available, subpath routing behind one entry point is simpler to secure and to reason about than a port per service.

## What to check first

Given a vague report — "it's down", "it's slow", "nothing works":

1. **Is the host healthy?** Memory pressure, load, disk. A sluggish-but-alive host under memory pressure looks like every service failing at once.
2. **Does it fail from every vantage point, or only some?** Local versus proxied versus external separates tier 4 from tier 5 immediately.
3. **Is it one component or the shared parent?** Check the failure-domain table above.
4. **Has this happened before?** The operating record and prior work-tracker entries usually answer the question outright — see `doctrine/operations/work-tracking-lifecycle.md`.

Step 4 is listed last but is often the cheapest. Run it first when the symptom sounds familiar.

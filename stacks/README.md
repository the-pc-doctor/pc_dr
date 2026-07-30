# Stacks

Parameterized container definitions. Rendered by `scripts/render.py` against a
private `vars.yml`; rendered output is private and never committed here.

## Why these are separate

Split by **restart risk and failure domain**, not by category. A single compose
file for everything means one `docker compose down` takes out your access path,
your monitoring, and your recovery tooling simultaneously.

| Stack | Contents | Restart profile |
|---|---|---|
| `edge/` | Reverse proxy, auth gateway | Up first, down last — it is how you get back in |
| `core/` | Home automation, NVR, broker, metrics | Contains the named critical services |
| `observability/` | Uptime monitor, dashboard | Must not die with what it watches |
| `agent/` | Model-provider gateway | Independent of everything it helps operate |

See `reference/topology.md` for the dependency order to restore in.

## Architecture

Every image must have a build for the host CPU architecture. Some upstreams ship
an architecture-specific tag rather than a multi-arch manifest, and the default
tag will either fail or run without hardware acceleration. Check the manifest
before deploying — see `doctrine/capabilities/architecture-constraints.md`.

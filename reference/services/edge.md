# Edge: reverse proxy and authentication gateway

The single entry point. Terminates TLS, routes by name or path, and gates access before anything reaches a service.

Reference implementations: [Nginx Proxy Manager](https://github.com/NginxProxyManager/nginx-proxy-manager), image `jc21/nginx-proxy-manager`; [Authelia](https://github.com/authelia/authelia), image `authelia/authelia`.

## Depends on

- The container runtime and the core host.
- DNS, both external resolution of your name and internal resolution of backends.
- A certificate authority for issuance and renewal.

## Depended on by

Everything reachable by name or from outside. Nothing on the LAN reached by address depends on it — which is precisely what makes it diagnosable.

## Health

| Signal | Meaning |
|---|---|
| Container up | Necessary, nowhere near sufficient |
| Configuration test passes | The config it would load is valid |
| A known route returns its expected status | Routing actually works |
| Certificate expiry date | Days of runway left |
| The same route direct vs proxied | **Separates a proxy fault from a service fault** |

The last row is the one that matters. It is a two-line check that resolves the single most common misdiagnosis in this architecture.

## How it fails

**Reported as the backend being down.** A service is healthy on the host and unreachable through its name, and the report arrives as "the service is down." Restarting the healthy service accomplishes nothing and costs an outage. Probe both paths first — `wd_probe_both_paths` in `watchdogs/lib/watchdog_common.sh` exists for this.

**The container is gone rather than broken.** An update, a prune, or a failed recreate can remove the proxy container entirely. The symptom is total external unreachability with every backend healthy. A watchdog for this tier must be able to *recreate* the container, not merely restart it — restarting something that does not exist fails silently.

**Certificate renewal failed silently.** Renewal is periodic and its failure is quiet until the expiry date, at which point everything external breaks at once. Monitor days-to-expiry as a metric, not renewal success as an event.

**Hand-edited configuration lost on regeneration.** Where a proxy manager generates its configuration from a database, hand edits to the generated files are overwritten whenever it regenerates. If a hand edit is genuinely required, document that it exists and expect to reapply it. Some builds also require more than one reload before a change takes effect — verify the served behavior, not the reload's exit code.

**Locking yourself out.** The auth gateway sits in front of the admin interface of the thing that routes to it. A bad rule can make both unreachable simultaneously. Keep a LAN-direct path to the proxy admin interface that does not traverse the gateway, and test any auth change from a second browser session before closing the working one.

## Placement

**The edge tier must survive a restart of everything else.** It belongs in its own stack, brought up first and taken down last, because it is how you get back in. See `reference/topology.md`.

Do not expose service ports directly to the internet. Where a single certificate and hostname are available, subpath routing behind one entry point is easier to secure and reason about than a port per service — and it avoids a per-service certificate renewal that can fail independently.

## Auth gateway scope

Gate the administrative and sensitive surfaces. Deliberately consider what must *not* be gated: services with their own authentication, mobile clients that cannot complete an interactive auth flow, and webhook endpoints that need to be callable by an external system.

Record which paths are exempt and why. An undocumented exemption looks like a misconfiguration to the next reader, who will "fix" it and break a client.

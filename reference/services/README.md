# Service reference

One page per service class: what it does, what depends on it, what it depends
on, how to tell it is healthy, and how it fails.

These describe a *class* of component, not a deployment. Ports and addresses are
placeholders resolved from `vars.yml`.

| Page | Class | Named critical by default |
|---|---|---|
| `home-automation.md` | Automation platform and device integration hub | yes |
| `nvr.md` | Camera recording and detection | yes |
| `edge.md` | Reverse proxy and authentication gateway | no, but blocks all remote access |
| `observability.md` | Uptime monitoring, dashboard, metrics | no |
| `records.md` | Work tracker and documentation store | no |

"Named critical" means the operator has said people depend on it directly. It is
asked, not inferred — see `CUSTOMIZE.md`. Critical services get resource
protection, watchdog coverage, verification after every risky change, and a
maintenance window rather than an opportunistic restart.

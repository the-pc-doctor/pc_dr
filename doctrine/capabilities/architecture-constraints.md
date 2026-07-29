---
id: architecture-constraints
type: doctrine
status: active
authority: adopted
confidence: high
confidence_basis:
  - Image availability by CPU architecture is a hard mechanical fact, verifiable before deployment.
  - The memory-pressure and reclaim-precedence failures were observed directly on a memory-constrained single-board host.
  - Thermal and I/O behavior claims are calibrated to small-board hardware and stated as such.
scope:
  - Feasibility of any deployment or workload on constrained single-board hardware
  - Resource protection for named critical services
consult_when:
  - proposing to deploy any container, service, or workload
  - selecting a container image or tag
  - a host is unstable, sluggish, or killing processes
  - deciding what to protect under resource pressure
  - planning concurrent workloads on one small host
  - a service works on one machine and not another
do_not_use_when:
  - the workload is already running successfully on this hardware
  - the host has ample headroom and the question is not resource-bound
router_summary: "Hardware capability is a hard boundary - verify the image exists for this CPU architecture and that memory, thermal, and I/O headroom exist before proposing a deployment."
decision_effect: "Check architecture and headroom before committing to a deployment, and give named critical services explicit reclaim protection rather than relying on default kill heuristics."
implemented_by:
  - stacks/core/docker-compose.yml.tmpl
  - watchdogs/lib/watchdog_common.sh
lineage: LINEAGE.md
known_failures:
  - Treated as an absolute veto, this blocks workloads that would run acceptably with tuning or offloading.
  - Multi-architecture manifests are increasingly common, so pessimism about image availability is sometimes unwarranted - check rather than assume either way.
  - Protecting too many processes from reclaim leaves nothing eligible and turns a recoverable pressure event into a hard failure.
review_when:
  - a workload rejected on architecture grounds turns out to have a viable build
  - reclaim protection prevents recovery instead of enabling it
  - headroom estimates prove consistently wrong
last_material_revision: 2026-07-29
---

# Architecture constraints

On small hardware, capability is not a preference to be balanced against others. It is a boundary, and it is cheap to check before committing to a plan.

## Verify the image exists for this architecture

**Check before proposing, not after pulling.**

An image without a build for the host's CPU architecture does not run, and no amount of configuration changes that. On 64-bit ARM boards this is the single most common wasted effort: a plan is made, documentation is written, and the pull fails on a manifest that has no matching platform.

Three cases to distinguish:

1. **Multi-architecture manifest.** The plain tag resolves correctly per platform. Common now, and the happy path.
2. **Architecture-specific tag.** The project ships a suffixed tag for particular hardware, and the plain tag is x86-only. You must select the right tag explicitly; the default will fail or, worse, run without hardware acceleration.
3. **No build at all.** Either build from source on the host, find an alternative, or offload the workload to a different machine. Say which, rather than leaving it implied.

Inspect the manifest to answer this. Do not infer availability from the project's popularity.

Hardware acceleration deserves the same scrutiny separately. Decode and inference accelerators are exposed as platform-specific device nodes, and a container that starts happily without them will fall back to software and consume several times the CPU you budgeted. Confirm the device node exists on the host, not just that the compose file references it.

## Memory is the usual ceiling

On a small board, RAM runs out before CPU does, and the way it runs out is not graceful.

Under pressure, the system swaps. On flash-based storage, swapping is slow enough that a loaded host becomes unresponsive while remaining technically alive — the worst failure shape, because monitoring says up and nothing works. From there, the kernel's out-of-memory killer eventually terminates something, chosen by a heuristic that does not know what you care about.

Consequences for planning:

- **Know the headroom before adding a workload.** Check current usage and pressure metrics, not just total installed memory. Pressure-stall information tells you whether the host is already struggling in a way that a free-memory number hides.
- **Reduce swappiness** so the host prefers reclaiming cache over swapping process memory. Slower-but-working beats faster-then-catatonic.
- **Bound the memory-hungry things** — retention windows, cache sizes, worker counts, log volume. Unbounded retention on a small host is a scheduled outage.
- **Do not schedule heavy jobs concurrently.** See `doctrine/operations/scheduled-maintenance-design.md`.

## Reclaim precedence must be explicit

**Name the critical services and protect them from reclaim deliberately.** The default kill heuristic optimizes for reclaiming the most memory, which frequently means terminating the largest and most important process on the box.

A userspace reclaim daemon that acts earlier than the kernel — `earlyoom` and equivalents — allows preferring or avoiding specific processes by name. Use it to encode which services must survive.

Two cautions:

- **Protecting everything protects nothing.** If nothing is eligible for reclaim, a recoverable pressure event becomes a hard failure. Something must be killable.
- **Reclaim and self-healing can fight.** The daemon kills a process to free memory; a watchdog restarts it; the restart allocates again. This presents as instability with no single cause. Resolve by precedence — the watchdog needs to know a kill it did not cause has occurred, and back off rather than immediately re-allocating. See `doctrine/reliability/watchdog-blast-radius.md`.

## Thermal and I/O

**Sustained load throttles.** A board that benchmarks well for thirty seconds may hold a fraction of that indefinitely. If a workload is continuous — video decoding, inference, transcoding — the sustained figure is the real one. Active cooling changes this materially, and if a fan-control service is what keeps the board in its performance envelope, that service is load-bearing and belongs under watchdog coverage like any other critical component.

**Local flash is not bulk storage.** Continuous writes wear it and it is usually small. Recordings, backups, and archives belong on network storage.

That relocation introduces a dependency worth designing for: a stale or dropped network mount presents as *the service stopped working* with a perfectly healthy container. When a write-heavy service loses its data, check the mount before the service. Mount verification belongs in the watchdog, not in your memory of past incidents.

## State the constraint in the proposal

When architecture or headroom rules something out, say so with the specific limit and the alternative — "no ARM64 build; would need a source build or offload to the other host" is a usable answer. "That may not work well" is not.

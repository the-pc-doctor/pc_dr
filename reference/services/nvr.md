# Network video recorder

Ingests camera streams, runs detection, writes recordings and clips.

Reference implementation: [Frigate](https://github.com/blakeblackshear/frigate), image `ghcr.io/blakeblackshear/frigate`.

## Depends on

- The cameras, each of which is an independent failure source.
- Network storage for recordings — a shared failure domain with backups and archives.
- Hardware decode and inference accelerators, exposed as platform-specific device nodes.
- The message broker, for publishing detection events.

## Depended on by

The home automation platform (detection events, camera entities), dashboards, and any notification driven by detection.

## Health

| Signal | Meaning |
|---|---|
| API version endpoint responds | Process is alive |
| Detection frames per second | Actually processing. Zero on a running process is a wedge, not idleness. |
| Per-camera frame rate | Which camera is failing — the signal that makes bounded remediation possible |
| Recording file recency on disk | The write path works end to end |
| Storage mount present and writable | The most common cause of "recording stopped" |

Detection rate at zero while the process is up is the characteristic backend wedge. It will not show on a liveness check.

## How it fails

**One flaky camera, whole-service remediation.** The canonical blast-radius failure. A single intermittent camera trips a health check whose remediation restarts everything, gapping recordings on all other cameras and clearing the evidence that would have identified the culprit. Bound remediation to the camera. Cap whole-service restarts — zero is a legitimate setting. See `doctrine/reliability/watchdog-blast-radius.md`.

The diagnostic that usually resolves it outright: count remediation events per camera over time. A distribution concentrated on one camera names the culprit immediately.

**Storage mount stale or dropped.** Recordings stop; the container is healthy; the API responds normally. Check the mount before the service. Mount verification belongs in the watchdog.

**Architecture and accelerator mismatch.** This class of software commonly ships hardware-specific image tags rather than a single multi-architecture manifest. The wrong tag either fails to start or starts without acceleration and quietly consumes several times the expected CPU. Confirm the device node exists on the host, not merely that the compose file references it. See `doctrine/capabilities/architecture-constraints.md`.

**Stream-level incompatibility.** Some cameras produce streams that need explicit handling at ingest — timestamp resets, stream copying, or bitstream filtering — and without it, recordings are corrupt or absent while the camera appears connected. This is per-camera configuration, not a global setting.

**Frontend staleness mistaken for backend failure.** A UI or dashboard card that caches will show frozen clips while recording is fine. Distinguish before restarting anything: check file recency on disk. Restarting the backend to fix a stale frontend is a wasted outage.

## Retention

Recordings grow without bound by default. Set a retention window when you deploy, not after the first storage incident. Retention is a storage-pressure control, and unbounded retention on shared storage eventually takes out the backups that share the volume.

# Observability: uptime, dashboard, metrics

Answers "is it up", "what does it look like right now", and "what did it look like before".

Reference implementations: [Uptime Kuma](https://github.com/louislam/uptime-kuma), image `louislam/uptime-kuma`; [Glance](https://github.com/glanceapp/glance), image `glanceapp/glance`; [InfluxDB](https://github.com/influxdata/influxdb), image `influxdb`.

## The placement rule

**A monitor must not share a failure domain with what it monitors.**

A monitoring stack that dies with the host reports nothing at the moment you most need it. On a single-host lab this cannot be fully solved, but it can be mitigated:

- Keep monitoring in its own stack so a restart of the core stack does not take it with it.
- Use an external or third-party check for the one signal that matters most — is the lab reachable at all — since no on-host monitor can answer that.
- Never let the monitor depend on the reverse proxy to reach the services it checks. Probe backends directly, or the proxy failing will report as every service failing.

## Three distinct jobs

**Uptime monitoring** — is a thing responding, and has it stopped. Its most valuable and most overlooked feature is the **push monitor**: a scheduled job reports in on completion, and the monitor alerts when the report does not arrive. This is how "quiet on success" stays safe, and it is the only way a job that never ran becomes visible. See `doctrine/operations/scheduled-maintenance-design.md`.

**Dashboard** — a single view a human actually looks at. Its value is proportional to how little it shows: a dashboard with sixty tiles is a wall, not a signal. Host-level statistics generally require explicit host mounts into the container, and remote hosts require an agent — neither works by default, and both fail quietly by simply showing nothing.

**Metrics** — the time series that answers "when did this start" and "is this getting worse". The questions that need history are exactly the ones you cannot answer retroactively, which is the argument for collecting before you need it. Set a retention window at deployment; unbounded series on a small disk is a scheduled outage.

## Health

| Signal | Meaning |
|---|---|
| Monitor container up | The monitor is running |
| Monitor's own heartbeat observed externally | The monitor is actually reporting |
| Count of monitors in a failed state | The lab's overall state, in one number |
| Metrics write path accepting | History is still being recorded |

The second row is the one people skip. A monitor with no external observer can be silently dead for weeks, and its silence reads as everything being fine.

## How it fails

**Alert fatigue.** Too many checks, or checks too sensitive, produce alerts nobody reads — and the real one is lost with them. Fewer, better-chosen checks beat comprehensive coverage. See `doctrine/operations/notification-discipline.md`.

**Monitoring the wrong layer.** A check that hits the reverse proxy tests the proxy, DNS, the certificate, and the service all at once, and cannot tell you which failed. Probe the specific thing you want to know about, and check the path separately.

**Empty dashboard mistaken for healthy.** A dashboard whose data source is misconfigured shows no problems, which looks identical to no problems existing. Verify a dashboard shows real data at least once after any change to it.

**Metrics retention consuming the disk it monitors.** Unbounded series eventually cause the pressure event the monitoring existed to warn about.

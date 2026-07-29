---
id: model-provider-failover
type: doctrine
status: active
authority: adopted
confidence: high
confidence_basis:
  - Every failure listed was observed directly while running an agent through an aggregating gateway over multiple upstream providers.
  - The silent-schema and shared-identifier failures are structural consequences of how such configuration is parsed and matched, not incidental bugs.
  - The gateway-versus-agent placement argument follows from the observation that failover logic runs exactly when the agent is least able to reason.
scope:
  - Configuring or reviewing model provider chains and failover behavior for an agent runtime
consult_when:
  - configuring or changing model providers, failover order, or an aggregating gateway
  - an agent is flapping between providers or failing under rate limits
  - a fallback tier appears configured but never engages
  - a configuration change to the provider chain has no effect
  - an agent hangs indefinitely without timing out
  - an agent invents tool names or claims capabilities it lacks
do_not_use_when:
  - selecting a model for quality reasons rather than availability
  - the runtime has exactly one provider and no failover requirement
router_summary: "Put failover in an aggregating gateway rather than the agent, make tiers share model identifiers or they will never engage, and assert the chain's shape at startup because its failure mode is silence."
decision_effect: "Expose one gateway endpoint to the agent, verify tiers advertise matching model identifiers, restart after configuration edits, and add a startup assertion for any config whose misconfiguration is silent."
implemented_by:
  - agent/config/agent-runtime.yaml.tmpl
lineage: LINEAGE.md
known_failures:
  - A single gateway is itself a single point of failure; when it is down, every tier behind it is unreachable.
  - Routing everything through one endpoint obscures which upstream served a response, complicating attribution of quality problems.
  - Aggressive failover to a much weaker tier can be worse than failing outright, because degraded output is harder to detect than an error.
review_when:
  - the gateway becomes the cause of an outage
  - a quality problem cannot be attributed to an upstream
  - failover to a weak tier produces confidently wrong work
  - a provider's interface changes in a way the gateway does not model
last_material_revision: 2026-07-29
---

# Model provider failover

An agent that manages infrastructure needs to keep working when a model provider rate-limits, expires, or disappears. The design question is where the resilience lives.

## Put failover in the gateway, not the agent

**Expose one endpoint to the agent and let something else decide which upstream serves it.**

Failover logic inside the agent runs precisely when the agent is degraded — mid-request, out of quota, possibly on a weaker model. That is the worst available moment to execute conditional retry logic, and the code path is the least exercised in the system.

An aggregating gateway that speaks a single OpenAI-compatible interface solves this structurally. The agent has one base URL and one model name; tier health, priority, and retry are the gateway's problem. CLIProxyAPI (published as the `eceasy/cli-proxy-api` image) is one such multiplexer: register several upstream credentials, give each a priority, and it serves whichever tier is healthy.

The cost is honest and worth naming: **the gateway becomes a single point of failure.** Keep it trivially restartable, monitor it independently of the agent, and make sure a local or on-host tier exists so the agent is not entirely dependent on the internet — which is exactly when you tend to need it.

## Tiers must share model identifiers

**A fallback tier that advertises different model names is not a fallback.**

Failover matches on the model identifier. If the primary serves `some-model-name` and the fallback serves `some-other-name`, a request for the first simply fails when the primary is unavailable — the second tier is present, healthy, and never consulted. The configuration looks correct and the chain does nothing.

Verify by asking each tier what it serves and comparing the lists, not by reading the configuration and assuming.

## Configuration is read at start

Most gateways parse configuration once. Edit the file, and you are still running the old chain until you restart the process.

This produces a specific waste: you change a priority, test, see the old behavior, conclude the change was wrong, and change something else. Restart first, then test. Verify the running configuration rather than the file on disk — see `doctrine/operations/change-backup-and-rollback.md`.

## Assert the shape of silent-failure configuration

Some configuration is wrong in a way that produces no error.

The canonical example: a failover list whose entries must be structured objects, each naming a provider and a model. Written as bare strings, it parses cleanly, starts cleanly, logs nothing — and never fails over. The chain appears configured and is not, and you discover it during the outage it was supposed to cover.

**Where misconfiguration is silent, add a startup assertion rather than documentation.** Validate the shape, log what chain was actually loaded, and refuse to start on a structure that cannot work. Documentation does not execute; an assertion does.

The general rule extends past provider chains: any configuration whose failure mode is *nothing happening* needs a positive check that it loaded as intended.

## Bound the tail, and distrust it

A low-priority free or best-effort tier is useful for bulk work. Two constraints:

**Rate limits are its normal state, not an exception.** Place it below anything you depend on and do not route critical work to it.

**Weak models hallucinate tool names rather than admitting they cannot call a tool.** This is worse than an error: the agent proceeds confidently against a tool that does not exist, and the failure surfaces somewhere unrelated. Either keep the tail tier capable enough for real tool use, or disable tool access when the chain has degraded to it. Degraded output is harder to detect than a clean failure, which is why failing outright is sometimes the better outcome.

## Timeouts and hangs

Two timeout classes are needed, and they fail differently:

- **Idle timeout** — no data for N seconds. Necessary but insufficient.
- **Wall-clock ceiling** — total elapsed time, regardless of activity.

Without the second, a keepalive or streaming proxy that emits periodic data resets the idle counter forever, and a watchdog built only on idleness can never fire. The session hangs indefinitely while looking healthy. Bound total duration independently.

Separately, tool discovery over a network hop is slower than a local call. A discovery timeout tuned for local tools makes remote tool servers look permanently unavailable — the symptom reads as "the tool server is down" when the real fault is a timeout measured in a fraction of what the round trip needs.

## Provider churn is the normal case

Upstream providers get deprecated, restricted, rate-limited, priced out, or retired outright — sometimes returning a hard protocol-level rejection with no warning period.

Design for replacement rather than for any particular provider:

- Keep provider identity out of prompts, skills, and application logic. Only the gateway configuration should name a provider.
- Keep at least one tier that does not depend on an external account.
- Record what the chain was when it worked, so a regression has a known-good state to compare against — see `doctrine/operations/change-backup-and-rollback.md`.

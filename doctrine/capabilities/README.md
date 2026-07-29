# Doctrine — capabilities

What the system can actually do, and what it depends on but does not control.

- `architecture-constraints.md` — verify the image exists for this CPU
  architecture, know the memory ceiling, make reclaim precedence explicit.
- `model-provider-failover.md` — put failover in a gateway, make tiers share
  model identifiers, assert the shape of silent-failure configuration.
- `external-capability-governance.md` — a capability you do not operate can be
  withdrawn, throttled, or silently degraded; acceptance is not execution.

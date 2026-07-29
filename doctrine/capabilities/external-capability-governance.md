---
id: external-capability-governance
type: doctrine
status: active
authority: adopted
confidence: high
confidence_basis:
  - Every failure mode listed was observed directly against consumer cloud-dependent devices and vendor APIs in a running lab.
  - The accept-and-buffer and resolver-NODATA failures are structural properties of the interfaces involved rather than transient bugs.
  - The account-sharing and revocation consequences follow from how vendor authorization is scoped, not from local configuration.
scope:
  - Depending on any capability owned and operated by someone else
  - Design of integrations against vendor cloud APIs and cloud-dependent devices
consult_when:
  - integrating a cloud-dependent device or vendor API
  - a vendor integration works intermittently or fails in one direction only
  - deciding how much of a workflow may depend on an external service
  - a vendor account is shared, changed, or re-authorized
  - name resolution failures surface as generic integration timeouts
  - an external interface changes or is retired
do_not_use_when:
  - the capability runs entirely on hardware you control
  - diagnosing a fault already localized to a local component
router_summary: "A capability you do not operate can be withdrawn, rate-limited, or silently degraded at any time - design for its absence, verify effects locally, and never let it hold the only copy of state you need."
decision_effect: "Assume any external dependency can vanish or lie about success, add a local verification path and a degraded mode, and treat vendor acceptance of a command as receipt rather than execution."
implemented_by:
  - agent/config/agent-runtime.yaml.tmpl
lineage: LINEAGE.md
known_failures:
  - Building a local fallback for every external capability is often more expensive than tolerating the outage.
  - Some capabilities have no local equivalent at all, so the doctrine can only inform expectations rather than change the design.
  - Over-caution here can block genuinely useful integrations that happen to be cloud-dependent.
review_when:
  - a vendor change breaks an integration in a way the design did not anticipate
  - a local fallback costs more to maintain than the outage it prevents
  - a degraded mode is never exercised and is discovered not to work
last_material_revision: 2026-07-29
---

# External capability governance

Anything you do not operate can be withdrawn without notice, rate-limited without warning, or changed without a migration path. Convenience is not ownership.

## The three questions

Before depending on an external capability:

1. **What happens when it is unavailable?** If the answer is "the lab stops working," that dependency needs a degraded mode.
2. **Who can revoke it?** A vendor, an account owner, an expiring credential, or a terms change.
3. **Does it hold the only copy of anything?** State that exists only in someone else's service is state you can lose without recourse.

The answers are usually acceptable. The point is having them before the outage rather than during it.

## Acceptance is not execution

**A vendor API returning success means it received your request.** Nothing more.

Cloud-dependent devices route commands through the vendor's infrastructure to the device. Any hop can accept, queue, and lose a command while every layer reports success. The device may also be unreachable, asleep, or refusing the command for a local reason the API never learns.

Consequence: never treat an external API's success response as evidence of a physical effect. Confirm through something local — a sensor, a camera, a power draw change, a different transport. See `doctrine/reliability/verification-before-claiming-done.md`.

## Failures arrive disguised

External dependencies rarely fail as clean errors. Recurring disguises:

**Name resolution returning empty rather than failing.** A resolver that answers "no data" for a vendor host produces a generic connection timeout several layers up. The symptom looks like an API outage, a network problem, or a broken integration — the actual fault is one DNS answer. When a vendor integration fails with a nonspecific timeout, resolve the hostname explicitly before diagnosing anything else. Where a resolver is unreliable for a specific host, pinning it locally is a legitimate fix.

**Silent regional or account-level degradation.** The service is up, your account is throttled. Status pages report the former.

**Interface changes without deprecation.** A client that worked yesterday receives a hard protocol-level rejection today, with no warning window and no migration path. Design so replacing the client is a configuration change, not a rewrite.

**Partial capability.** Read works, write does not. Or the reverse. An integration that is up in one direction reports as healthy in most monitoring.

## Shared accounts

When a vendor's model requires sharing an account to grant access — a family plan, a shared login, a delegated device — understand the coupling before you rely on it:

- Re-authenticating in one place can invalidate sessions elsewhere.
- A password change by the account owner revokes your integration silently.
- Rate limits are shared, so someone else's usage becomes your outage.
- Switching the account an integration authenticates as can lose device pairings, permissions, or history that do not transfer.

Record which account an integration uses and why, in the documentation store. This is exactly the kind of fact that is obvious while you configure it and unrecoverable six months later — and re-deriving it usually means breaking the integration to find out.

## Local paths beat cloud paths

Where a device supports both a local interface and a cloud one, prefer local: fewer hops, no vendor availability dependency, lower latency, and it survives an internet outage.

Two honest caveats:

- Local interfaces are often less complete. Some functionality genuinely only exists through the cloud.
- Local transports have their own reliability characteristics. A short-range wireless protocol may be unreliable at the distance you actually need, and "local" does not mean "dependable" — measure it rather than assuming.

When both exist and disagree, prefer the one closer to the device, and treat the disagreement as a finding.

## Design for withdrawal

- **Keep the vendor's identity in configuration**, not spread through prompts, skills, and automation logic. Replacing a provider should be a config change.
- **Cache what you need locally** when the data matters and the service is the only source.
- **Define the degraded mode explicitly**, and exercise it occasionally. An untested fallback is an assumption, and it will be discovered wrong at the least convenient moment.
- **Monitor the dependency separately** from the thing that uses it, so the integration failing and the vendor failing are distinguishable.

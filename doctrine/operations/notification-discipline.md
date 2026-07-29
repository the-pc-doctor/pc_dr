---
id: notification-discipline
type: doctrine
status: active
authority: adopted
confidence: high
confidence_basis:
  - Directly observed - a channel carrying routine automated success reports stopped being read, including the messages that required action.
  - The mechanism is well established as alarm or alert fatigue in operations and clinical settings, so it is not a local peculiarity.
  - Cheap to prevent and expensive to discover late, which justifies a rule rather than a principle.
scope:
  - Any outbound message an agent sends to a human
  - Design of alerting, reporting, and approval automation
consult_when:
  - about to send a message, alert, or report to the operator
  - designing automated alerting, reporting, or approval flows
  - deciding whether an event warrants interrupting a human
  - an operator has stopped responding to a channel
  - building an approval prompt with selectable actions
do_not_use_when:
  - replying in a conversation the operator is already having with you
  - writing to a work-tracking record, which is a store rather than a channel
  - the operator has explicitly asked for a specific report
router_summary: "Interrupt a human only for decisions they must make; routine success reporting destroys the channel's signal value and takes the important messages down with it."
decision_effect: "Send only decisions and genuine exceptions to a human channel, route everything else to a store the operator can read on their own schedule, and verify any action or link before offering it."
implemented_by:
  - agent/lib/worktracker.py.tmpl
lineage: LINEAGE.md
known_failures:
  - Over-applied, an agent can go silent during a long incident when the operator genuinely wants progress visibility - silence is a default, not a prohibition on answering.
  - A decision prompt sent with no deadline and no fallback can stall work indefinitely if the operator is unavailable.
  - Suppressing routine reporting hides a scheduled job that has stopped running entirely; absence of messages must be independently detectable.
review_when:
  - the operator stops responding to a channel
  - an important message is missed
  - an agent stalls waiting on an approval that never arrives
  - a silent job is discovered to have been dead for some time
last_material_revision: 2026-07-29
---

# Notification discipline

A notification channel has a fixed budget of human attention. Every routine message spends some of it. Spend it on status and there is none left for the message that mattered.

## The rule

**Interrupt a human for decisions. Route everything else to a store.**

A message is worth sending when the operator must choose something, authorize something, or physically do something. Everything else — progress, successful completion, routine health, audit results with nothing in them — belongs in a record they can read when they choose to.

This is a reliability control, not a style preference. The failure is specific and measured: a channel that carries routine automated success reports gets muted, filtered, or scrolled past, and the *next* message that required action is lost with it. The system that generated the noise also destroyed the delivery guarantee it depended on.

## What earns a message

| Send | Do not send |
|---|---|
| A decision the operator must make | "Task started" / "Task completed" |
| An authorization request before an irreversible action | Routine health-check passes |
| A genuine exception with a consequence they can act on | An audit that found nothing |
| Something physically requiring them | Progress on work they already know about |
| A hard blocker that stops all further work | Confirmation that a scheduled job ran normally |

The test: **if the operator can do nothing differently after reading it, it is not a notification.** It is a log entry that took a piece of their attention.

## Silence must be detectable

The dangerous corollary: if a job only speaks when something is wrong, a job that has stopped running entirely is indistinguishable from a job that is fine.

Do not solve this by reintroducing routine success messages. Solve it where it belongs — the monitoring layer watches for the *absence* of an expected run, and alerts on that. A dead-man switch is a monitor concern, not a notification concern. `uptime-kuma` and similar tools support push-style monitors precisely for this.

## Audits return silence

An automated audit that finds no work must produce **nothing** — no message, no record, no "all clear."

An audit that reports every clean run converts the tracker and the channel into the noise they exist to surface signal from. Worse, it produces a stream of records that make the tracker unusable for the real work.

## Decision prompts

When you do ask for a decision, the prompt must be actionable on its own:

- **State the decision, not the situation.** The operator should not have to reconstruct what is being asked.
- **Offer the actual options**, with the consequence of each.
- **Use only action names the receiving system actually implements.** A custom action label that the bot does not recognize renders as a button that does nothing — the operator taps it, nothing happens, and they lose confidence in the whole channel. Check what the integration handles before inventing an option.
- **Verify any link before sending it.** A dead link in a notification trains the operator to ignore notifications. Request it first and confirm it resolves.
- **Include enough context to decide without opening anything** — the subject, the change, the risk, and where to look for more.

Then wait. If the decision is blocking and the operator is unavailable, that is a fact to record in the tracker, not a reason to proceed on your own judgment.

## Channel choice

Direct, personal channels are for decisions. Group or topic channels accumulate participants who did not opt into your automation and cannot act on it.

When routing is ambiguous, prefer the narrower channel. An unnecessary message to one person is a small cost; the same message to a shared channel teaches several people to mute it.

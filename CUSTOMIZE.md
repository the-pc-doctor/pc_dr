# Customize

Ask only the questions whose answers change what you do. Everything else can be discovered by inspection.

## Consequential questions

**1. Which services are load-bearing for people?**
Name them explicitly. These get resource protection, watchdog coverage, verification after every risky change, and a maintenance window rather than an opportunistic restart. Do not infer this list from the architecture diagram.

**2. What is the hardware constraint?**
CPU architecture, memory ceiling, storage layout, and thermal behavior. This is a hard boundary. On single-board hardware it decides which images can run at all and whether concurrent workloads are viable.

**3. Where is the operating record, and where do incidents go?**
Which file or system holds recurring-failure knowledge? Which holds durable architecture documentation? Which holds transient per-incident notes? Putting an incident log in the architecture store, or architecture in a ticket, is the most common information-placement failure and it makes both unusable.

**4. What is the notification policy?**
Specifically: what is worth interrupting a human for? The default in this template is decisions and approvals only — no automated status reporting. An operator who receives routine success messages stops reading all messages, including the one that mattered.

**5. What is the rollback path?**
Before the first material change: what is backed up, how often, verified how, and restored by what procedure. An unverified backup is a belief, not a backup.

**6. What may the agent do unsupervised?**
Draw the line at: restart a service, edit a config, reboot a host, change a firewall or proxy rule, publish anything outward, delete anything. Reversibility and blast radius, not convenience, should set each boundary.

## Fill in `vars.yml`

Copy `vars.example.yml` to your **private** source tree — outside this repository — and fill it in. Every key is documented inline.

Secrets are not values in `vars.yml`. They are `*_ref` pointers to entries in a mode-0600 credential file. This keeps rotation in one place and keeps secrets out of anything that could be synced, backed up to a shared location, or committed.

## Do not answer by inspection

Two things the agent must **not** infer:

- **Authorization.** Being able to reach a service does not mean it may be changed. Ask.
- **Criticality.** Uptime graphs show what has been stable, not what matters. Ask.

# Synchronization model

This repository is a curated **one-way projection** of a private lab. It is deliberately not a mirror.

Two trees:

| Tree | Contents | Visibility |
|---|---|---|
| Private source | `vars.yml`, rendered configuration, credentials, denylist, incident history | Never published |
| This repository | Templates, doctrine, reference, checkers | Published |

Information flows private → public only, and only through authoring. Nothing is copied.

## Update trigger

Every material change to the lab's architecture, self-healing design, operating doctrine, or maintenance model gets a publication review in the same work cycle. Two valid outcomes:

1. **Transferable** — generalize it, author the template change, run the checks, publish, verify a fresh clone.
2. **No public delta** — keep it private because it concerns local addressing, credentials, capability state, records, or history rather than reusable architecture.

No parity commit is required. Commit histories are independent by design.

## Projection boundary

**May cross:**

- operating posture, judgment, and hard boundaries;
- generalized failure modes and their decision effects;
- service and topology *shape*, as templates;
- container stack structure and public image names;
- watchdog contracts and detection/remediation patterns;
- scheduled-maintenance structure and cadence patterns;
- agent runtime configuration *shape* and skill structure;
- adoption, customization, and integrity tooling.

**May not cross:**

- credentials, tokens, keys, or anything that authenticates;
- internal or external addressing, hostnames, MACs, or port maps;
- personal names, relationships, emails, or accounts;
- device serials, vendor account identifiers, or geographic coordinates;
- ticket numbers, document identifiers, or private record references;
- machine paths, private remotes, or private provenance;
- capability state — what is currently enabled, reachable, or authorized here;
- incident history tied to identifiable devices;
- any language that causes an adopting agent to assume this lab's topology exists in its own.

## The generalization step

This is where the value is created and where leaks are prevented. For each candidate change, extract the **decision effect** and discard the instance.

Working example, with the instance removed:

> **Private:** a specific camera intermittently dropped its stream; the health watchdog escalated to a full-stack restart; recordings for every camera gapped during each restart; the restarts masked the single failing device for weeks.
>
> **Public doctrine:** a watchdog whose remediation scope exceeds its detection scope converts a single-component fault into a service-wide outage, and resolves the symptom that would have identified the component. Bound remediation to the smallest unit that can carry the fault, and cap escalation frequency so that repeated escalation surfaces as a signal rather than as recovery.

The public form is more useful than the private one, and carries nothing identifying. If a generalization cannot be written without naming a device, an address, or a record, it is not yet generalized.

## Release checks

Before every public update:

1. inspect the private change semantically;
2. extract the class-level decision effect;
3. generalize by meaning, not by find-and-replace;
4. regenerate derived files (`scripts/generate_index.py`);
5. run `python3 scripts/check_template.py`;
6. run `python3 scripts/check_sanitization.py --strict`;
7. read the staged diff by eye for addressing, names, and credentials;
8. push only to the intended remote;
9. clone the published HTTPS URL into a fresh directory and re-run both checkers there;
10. verify local and remote heads and the intended visibility.

Static checks establish packaging integrity. They do not prove that an adopted architecture is well designed, and they do not prove that a generalization was complete. Step 3 is human judgment and cannot be delegated to step 6.

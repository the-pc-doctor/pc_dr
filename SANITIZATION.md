# Sanitization

Publishing infrastructure is a different risk class from publishing prose. Prose leaks a name. Configuration leaks a way in.

This file defines the threat model, the deny classes, and the enforcement. `scripts/check_sanitization.py` implements it. `SYNC.md` defines the workflow around it.

## Threat model

What an attacker gains from a careless publication, in rough order of severity:

| Leaked | Consequence |
|---|---|
| A live credential, token, or private key | Direct access. Public-repo secrets are scraped within minutes of the push. |
| An external hostname or DDNS name plus a service inventory | A target list with known software and known versions. |
| Internal addressing and port map | Lateral-movement map, useful the moment anything else is breached. |
| Hardware addresses | Device fingerprinting; in some setups, a bypass for MAC-based access control. |
| Personal names, emails, family names | Correlates the lab to a person; enables social engineering and account recovery attacks. |
| Device serials, account identifiers | Vendor-side impersonation and support-channel social engineering. |
| Ticket and document identifiers | Correlates the public repo to a private record system. |
| Geographic coordinates | Physical location. |

Note that severity is not the same as detectability. A private key is catastrophic and trivially greppable. An internal subnet is moderate and appears in hundreds of files. The second is the one that actually gets published.

## The two rules that matter most

**1. Generate, never scrub.**

Public artifacts are hand-authored parameterized templates. Live files are read as *reference* while authoring, and are never transformed into published artifacts.

Copy-then-scrub fails for structural reasons, not from carelessness:

- Detection is a denylist problem, and denylists are never complete.
- One miss is permanent. Git history retains it after the file is fixed.
- Scrubbing preserves structure. Even with every literal replaced, a scrubbed config still discloses your exact topology, port map, and service inventory — because that is what a config *is*.
- It scales wrongly. A live tree has hundreds of candidate files; a template tree has the ones you deliberately wrote.

Authoring from scratch is slower per file and correct by construction.

**2. The denylist is itself private.**

A committed file listing the real names, hostnames, addresses, and serials to exclude is a disclosure of exactly those values, published in the most convenient possible format.

The identity denylist therefore lives **outside** the repository and is loaded at check time from `$PC_DR_DENYLIST`, or from `.denylist.local` (which is gitignored). `scripts/denylist.example.txt` documents the format using placeholder values only.

A checker that runs without a denylist is running in degraded mode. It says so, loudly, and exits non-zero when `--strict` is set.

## Placeholder conventions

Placeholders use reserved ranges so that **any real value is a hard failure** rather than a judgment call.

| Class | Use | Reserved by |
|---|---|---|
| IPv4 | `192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24` | RFC 5737 |
| Domain | `example.com`, `example.org`, `lab.example` | RFC 2606 |
| MAC | `de:ad:be:ef:00:xx` | Convention |
| Template variable | `{{ host.core.ip }}` | This project |

Consequence: a literal RFC 1918 address (`10/8`, `172.16/12`, `192.168/16`) anywhere in this repository is an error, even in an example. There is a documentation range for that, and it is not the one your lab uses.

Carrier-grade NAT space (`100.64.0.0/10`) is also denied — overlay-network addresses live there and are as identifying as a public IP.

## Deny classes

The checker fails on any of these outside an explicit allowance.

**Network**
- RFC 1918 literals; `100.64.0.0/10`; loopback with a nonstandard port map
- MAC addresses not matching the reserved placeholder prefix
- Dynamic-DNS and overlay-network domains
- Any hostname resolving to a real host you operate

**Secrets**
- PEM private-key headers
- Provider key prefixes and personal-access-token shapes
- JWT structure
- Bot-token shapes (`<digits>:<35-char token>`)
- `Authorization:` headers with a literal value
- `password|passwd|token|api_key|apikey|secret|bearer` followed by an assignment and a non-placeholder value
- High-entropy base64 or hex runs of 20+ characters

**Identity** (from the private denylist)
- Personal and family names, usernames, email addresses
- Employer, ISP account, or provider account identifiers

**Records**
- Ticket numbers and internal document identifiers
- Device serial numbers and hardware identifiers
- Geographic coordinates
- Automation identifiers derived from epoch timestamps, where they would correlate to a private record

**Paths**
- Absolute home directories containing a real username
- Private repository or remote URLs

## What is explicitly allowed

These are safe and are the reason the template is useful at all:

- **Public container image names and tags.** `home-assistant`, `frigate`, `nginx-proxy-manager`, `authelia`, `uptime-kuma`, `mosquitto`, `influxdb`, and the rest are public software. Naming them is not disclosure; it is documentation.
- **Public GitHub projects and upstream repositories**, including ones this lab depends on.
- **Public port defaults** documented by the upstream project.
- **Generalized failure modes.** "A watchdog with remediation scope wider than its detection scope amplifies single-component faults" carries no identifying information. The incident that taught it does.

The boundary: **software is public, deployment is private.** Which images you run is documentation. Where they run, on what addresses, behind what hostname, with what credentials, is not.

## Allowance pragma

Reviewed exceptions are marked inline and are auditable:

```
# sanitize:allow reserved-doc-range  — RFC 5737 example, intentional
```

An allowance names the reason. `grep -rn 'sanitize:allow'` is the audit surface, and a review that finds an unexplained allowance treats it as a defect.

## Enforcement

```bash
python3 scripts/check_sanitization.py --strict          # working tree
python3 scripts/check_sanitization.py --strict --history # every blob in git history
```

The history mode matters. A secret removed in a later commit is still published; the working tree being clean proves nothing about what is reachable.

## Publication sequence

Never push a new repository straight to public.

1. Working tree clean; `check_template.py` and `check_sanitization.py --strict` pass.
2. Fresh repository, **no imported history**. Do not filter a private repo into a public one — start empty.
3. Push to a **private** remote.
4. `git clone` the remote HTTPS URL into a clean directory.
5. Re-run both checkers **on the clone**, not on your working tree.
6. Read the rendered file list by eye. Confirm nothing rendered from real `vars.yml` was committed.
7. Only then change visibility to public.

Private-to-public is a reversible decision. Public-to-private after a secret has been indexed is not.

## If something leaks anyway

Assume disclosure the moment it is pushed, not the moment someone notices.

1. Rotate the credential first. Do not start with deleting the commit — rotation is what actually closes the exposure.
2. Then remove the artifact and, if the repository was public, treat the history as compromised and republish from a fresh repository.
3. Record it in `log.md` as a material failure, and add the missed pattern to the deny classes.

Deleting a public commit does not un-publish it. Rotation does.

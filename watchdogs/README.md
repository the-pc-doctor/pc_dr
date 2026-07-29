# Watchdogs

Self-healing units. The shared contract is in `lib/watchdog_common.sh`, which
implements `doctrine/reliability/watchdog-blast-radius.md` and
`doctrine/reliability/verification-before-claiming-done.md`.

Read the doctrine before adding a healer. Automated healing is the most
dangerous code in a lab, because it is the only code with standing authority to
take services down.

`systemd/` unit templates are Phase 3.

#!/usr/bin/env bash
# Shared watchdog contract.
#
# Implements two doctrine pages:
#   doctrine/reliability/watchdog-blast-radius.md
#   doctrine/reliability/verification-before-claiming-done.md
#
# The contract, in one line: remediate the smallest unit that can carry the
# fault, cap escalation so that hitting the cap is a SIGNAL, preserve the
# trigger evidence before acting, and verify the effect before recording
# success.
#
# Source this from a per-service watchdog:
#
#   source "${LAB_HOME}/watchdogs/lib/watchdog_common.sh"
#   wd_init nvr
#   wd_probe_http "http://127.0.0.1:5000/api/version" || wd_remediate frigate
#
# shellcheck shell=bash

set -uo pipefail

WD_STATE_DIR="${WD_STATE_DIR:-/var/lib/lab-watchdog}"
WD_EVIDENCE_DIR="${WD_EVIDENCE_DIR:-${WD_STATE_DIR}/evidence}"

# Escalation caps per hour. Tier 3 defaults to 0 — whole-service restarts are
# OFF unless a specific service opts in. This is deliberate: a service-wide
# restart triggered by one component's fault interrupts every other component
# and erases the evidence identifying the culprit. Set it above zero only when
# you have evidence that the fault's true scope is the whole service.
WD_TIER1_MAX_PER_HOUR="${WD_TIER1_MAX_PER_HOUR:-6}"
WD_TIER2_MAX_PER_HOUR="${WD_TIER2_MAX_PER_HOUR:-2}"
WD_TIER3_MAX_PER_HOUR="${WD_TIER3_MAX_PER_HOUR:-0}"

WD_SERVICE=""

wd_log() {
  printf '%s %s[%s] %s\n' "$(date -Is)" "watchdog" "${WD_SERVICE:-init}" "$*"
}

wd_init() {
  WD_SERVICE="$1"
  mkdir -p "${WD_STATE_DIR}" "${WD_EVIDENCE_DIR}" 2>/dev/null || true
}

# --- Detection -------------------------------------------------------------
#
# Probe from the vantage point that actually matters. A service can be healthy
# on loopback while every route to it is broken — reachability is not health,
# and health from the wrong place is not evidence. If users reach a service
# through a reverse proxy, probe through the proxy too.

wd_probe_http() {
  local url="$1" timeout="${2:-10}"
  curl -fsS --max-time "${timeout}" -o /dev/null "${url}"
}

# Probe the same service by two paths. Divergence localizes the fault: direct
# ok + proxied fail means the proxy is the problem, not the service. This is
# the single most common misdiagnosis in a proxied lab.
wd_probe_both_paths() {
  local direct="$1" proxied="$2"
  local d=0 p=0
  wd_probe_http "${direct}" || d=1
  wd_probe_http "${proxied}" || p=1
  if [[ ${d} -eq 0 && ${p} -ne 0 ]]; then
    wd_log "service healthy directly but unreachable via proxy — fault is the path, not the service"
    return 2
  fi
  [[ ${d} -eq 0 ]]
}

wd_container_running() {
  [[ "$(docker inspect -f '{{.State.Running}}' "$1" 2>/dev/null)" == "true" ]]
}

# --- Evidence --------------------------------------------------------------
#
# Capture WHY before remediating. A healer that restarts a service and thereby
# clears the log, metric, or error counter that triggered it has destroyed the
# only record of its own reason to act.

wd_capture_evidence() {
  local unit="$1" reason="$2"
  local stamp file
  stamp="$(date +%Y%m%d-%H%M%S)"
  file="${WD_EVIDENCE_DIR}/${WD_SERVICE}-${unit}-${stamp}.log"
  {
    printf '=== reason: %s\n=== unit: %s\n=== at: %s\n\n' "${reason}" "${unit}" "$(date -Is)"
    docker logs --tail 200 "${unit}" 2>&1 || true
  } >"${file}"
  wd_log "evidence captured: ${file}"
}

# --- Escalation accounting -------------------------------------------------
#
# The cap exists so that reaching it produces a signal, not so the healer stops
# quietly. A tier that can fire without limit is a mechanism for turning an
# intermittent component fault into a chronic service outage.

_wd_counter_file() { printf '%s/%s.tier%s.count' "${WD_STATE_DIR}" "${WD_SERVICE}" "$1"; }

_wd_recent_count() {
  local tier="$1" file cutoff count=0 line
  file="$(_wd_counter_file "${tier}")"
  [[ -f "${file}" ]] || { printf '0'; return; }
  cutoff=$(( $(date +%s) - 3600 ))
  while read -r line; do
    [[ -n "${line}" && "${line}" -gt "${cutoff}" ]] && count=$(( count + 1 ))
  done <"${file}"
  printf '%s' "${count}"
}

_wd_record() {
  local tier="$1" file cutoff tmp
  file="$(_wd_counter_file "${tier}")"
  cutoff=$(( $(date +%s) - 3600 ))
  tmp="$(mktemp)"
  [[ -f "${file}" ]] && awk -v c="${cutoff}" '$1>c' "${file}" >"${tmp}"
  date +%s >>"${tmp}"
  mv "${tmp}" "${file}"
}

wd_tier_allowed() {
  local tier="$1" max used
  case "${tier}" in
    1) max="${WD_TIER1_MAX_PER_HOUR}" ;;
    2) max="${WD_TIER2_MAX_PER_HOUR}" ;;
    3) max="${WD_TIER3_MAX_PER_HOUR}" ;;
    *) return 1 ;;
  esac
  used="$(_wd_recent_count "${tier}")"
  if [[ "${max}" -eq 0 ]]; then
    wd_log "tier ${tier} is disabled (cap 0) — not escalating"
    return 1
  fi
  if [[ "${used}" -ge "${max}" ]]; then
    # Reaching the cap is the finding. Surface it; do not silently continue.
    wd_log "SIGNAL: tier ${tier} cap reached (${used}/${max} in the last hour) — unresolved fault, escalation suppressed"
    return 1
  fi
  return 0
}

# --- Remediation -----------------------------------------------------------
#
# Tier 1 acts on the component detection identified. Nothing here restarts a
# parent on the strength of a child's failure.

wd_remediate() {
  local unit="$1" tier="${2:-1}" reason="${3:-health probe failed}"
  wd_tier_allowed "${tier}" || return 1
  wd_capture_evidence "${unit}" "${reason}"
  wd_log "tier ${tier} remediation: restarting ${unit} (${reason})"
  _wd_record "${tier}"
  docker restart "${unit}" >/dev/null 2>&1
}

# --- Verification ----------------------------------------------------------
#
# An issued restart is not a restored service. Confirm the effect, with a
# freshness check, before recording success. A state source that has stopped
# updating will happily confirm whatever it last saw.

wd_verify() {
  local probe_url="$1" attempts="${2:-6}" delay="${3:-10}" i
  for (( i = 1; i <= attempts; i++ )); do
    sleep "${delay}"
    if wd_probe_http "${probe_url}"; then
      wd_log "verified healthy after remediation (attempt ${i}/${attempts})"
      return 0
    fi
  done
  wd_log "NOT VERIFIED: still failing after ${attempts} attempt(s) — do not report this as fixed"
  return 1
}

# Confirm a container actually restarted rather than merely being asked to.
# Compares start time before and after; an unchanged start time means the
# restart did not happen, whatever the exit code said.
wd_verify_restarted() {
  local unit="$1" before="$2" after
  after="$(docker inspect -f '{{.State.StartedAt}}' "${unit}" 2>/dev/null)"
  if [[ -z "${after}" || "${after}" == "${before}" ]]; then
    wd_log "NOT VERIFIED: ${unit} start time unchanged — restart did not take effect"
    return 1
  fi
  return 0
}

# --- Critical-service guard ------------------------------------------------
#
# Named critical services are protected explicitly, not inferred from the
# architecture. Under memory pressure a reclaim daemon and a watchdog can fight
# — the daemon kills, the watchdog restarts, the restart allocates. Resolve by
# precedence, not by tuning both independently.

wd_is_critical() {
  local name="$1" entry
  for entry in ${WD_CRITICAL_SERVICES:-}; do
    [[ "${entry}" == "${name}" ]] && return 0
  done
  return 1
}

wd_guard_critical() {
  local name="$1"
  if wd_is_critical "${name}" && [[ "${WD_MAINTENANCE_WINDOW:-0}" != "1" ]]; then
    wd_log "REFUSING: ${name} is a named critical service and this is not a maintenance window"
    return 1
  fi
  return 0
}

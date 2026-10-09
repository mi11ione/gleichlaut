#!/bin/sh
# Map the exit code of a failed Gleichlaut unit (systemd OnFailure=, argument: the unit name) or of a finished job
# (argument: --code N --name NAME) to a severity and a message, write it to the journal, and mail it if ALERT_MAIL is set.
# The table is the same as docs/deploy/README.md and docs/operations.md §6.
set -u
if [ "${1:-}" = "--code" ]; then code="$2"; unit="${4:-gleichlaut}"
else unit="$1"; code=$(systemctl show -p ExecMainStatus --value "$unit" 2>/dev/null || echo "?"); fi
case "$code" in
  1) sev=developer; msg="reproduction or validation failed: do not use this build" ;;
  2) sev=operator;  msg="usage error, bad item file or missing configuration (LLM_BASE_URL, CA file, key file, llama-cpp-python missing: use the offline image)" ;;
  3) sev=operator;  msg="70B canary outside tolerance, or drafting refused (latest canary failed or older than 31 days): run make canary; on a failure re-certify, or draft with the local 8B (make month)" ;;
  4) sev=operator;  msg="70B endpoint not certified (missing, expired, FAIL, or does not verify): make certify-endpoint" ;;
  5) sev=operator;  msg="certificate FAIL: do not use this endpoint for the SL lane" ;;
  6) sev=retry;     msg="endpoint or feed failed (unreachable, timeout, not yet published): records kept; the next run resumes. Page if it repeats" ;;
  7) sev=operator;  msg="certificate PENDING_REVIEW: label needs_review, then certify --resolve" ;;
  8) sev=reviewer;  msg="audit --fail-on-findings: the register has DE<->FR/IT divergences; read out/audit/audit_<date>_summary.json" ;;
  130) sev=retry;   msg="interrupted: the next run resumes" ;;
  *) sev=developer; msg="unexpected exit code $code" ;;
esac
line="gleichlaut ALERT [$sev] $unit exited $code: $msg"
logger -t gleichlaut -p user.err "$line" 2>/dev/null || echo "$line" >&2
if [ -n "${ALERT_MAIL:-}" ] && command -v mail >/dev/null 2>&1; then
  printf '%s\n\njournalctl -u %s -n 50\n' "$line" "$unit" | mail -s "gleichlaut: $unit exit $code ($sev)" "$ALERT_MAIL"
fi

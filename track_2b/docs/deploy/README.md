# Scheduling and alerting

Two ways to run Gleichlaut unattended. Both run the same three jobs:

| Job | When | Needs | Command |
|---|---|---|---|
| audit | quarterly, or monthly after the publication | the public feed only (no model, no endpoint, no secret) | `gleichlaut feeds --latest`, then `gleichlaut.sl.ingest <date>`, then `gleichlaut audit --date <date>` |
| canary | monthly, before the month run | the certified endpoint and its key | `gleichlaut certify --backend openai --canary 40` |
| month | the 2nd of each month (BAG publishes on the 1st) | the certified endpoint, a passing canary that is at most 31 days old | `gleichlaut month --from previous --to latest --fetch` (shadow mode), or `--items FILE` (pre-publication) |

Certification (`gleichlaut certify --backend openai`) is a manual step. Run it once per endpoint and model, again every
90 days, and after a failed canary.

## systemd (a VM or a server, without Docker)

```bash
sudo useradd --system --home /var/lib/gleichlaut gleichlaut
sudo git clone <repo> /opt/gleichlaut && sudo python3 -m venv /opt/gleichlaut/venv
sudo /opt/gleichlaut/venv/bin/pip install -r /opt/gleichlaut/track_2b/requirements.txt
sudo install -d -m 0750 /etc/gleichlaut
sudo install -m 0600 /dev/null /etc/gleichlaut/gleichlaut.env      # LLM_BASE_URL=..., LLM_API_KEY=..., LLM_NAME=..., proxy/CA variables
sudo sh -c 'head -c 32 /dev/urandom > /etc/gleichlaut/cert.key && chmod 0400 /etc/gleichlaut/cert.key'   # optional HMAC key
sudo cp /opt/gleichlaut/track_2b/docs/deploy/systemd/* /etc/systemd/system/
sudo systemctl daemon-reload
sudo -u gleichlaut env $(cat /etc/gleichlaut/gleichlaut.env) GLEICHLAUT_STATE=/var/lib/gleichlaut/state \
  PYTHONPATH=/opt/gleichlaut/track_2b/src /opt/gleichlaut/venv/bin/python -m gleichlaut certify --backend openai   # once
sudo systemctl enable --now gleichlaut-canary.timer gleichlaut-month.timer gleichlaut-audit.timer
systemctl list-timers 'gleichlaut*'
```

The units are `oneshot` services. Each has `OnFailure=gleichlaut-alert@%n.service`, which runs
[`alert.sh`](alert.sh) with the failed unit's name. The script reads the unit's exit code (`ExecMainStatus`), writes
one line to the journal (`journalctl -t gleichlaut`), and mails it if `ALERT_MAIL` is set in `/etc/gleichlaut/alert.env`.
The units run with `ProtectSystem=strict` and write only under `/var/lib/gleichlaut`. The HMAC key reaches the process
through `LoadCredential=`, readable only by the unit. Without a key, delete the two `LoadCredential`/`GLEICHLAUT_CERT_KEY`
lines.

## Kubernetes

[`kubernetes/gleichlaut.yaml`](kubernetes/gleichlaut.yaml) defines:

- a PVC (10 GiB) for `state/` and `out/`;
- a ConfigMap with the endpoint, paths and timeouts;
- a CronJob `gleichlaut-month` that runs on the 2nd at 06:00 Zurich. Its init container runs the canary and its main
  container runs the month;
- a CronJob `gleichlaut-audit` that runs quarterly.

The pods run as uid 10001, non-root, with no privilege escalation and all capabilities dropped. The root filesystem is
read-only: writes go only to the PVC and an emptyDir `/tmp`. Resources: 250m CPU and 512 MiB requested, 2 CPU and 2 GiB
limit. The run makes about 100 requests to the endpoint and needs no GPU on its own side. The endpoint key and the HMAC
key come from a Secret you create (`kubectl create secret generic gleichlaut-endpoint ...`; see the file header).
`backoffLimit: 0` because a blind retry is wrong for exit 3, 4 and 5. A manual re-run resumes from `records.jsonl`.

## Exit codes and alerts

| Exit | Meaning | Who acts | Alert |
|---|---|---|---|
| 0 | success | | none (optionally a "ran" heartbeat: alert if no success in 35 days) |
| 1 | reproduction or validation failed | developer | ticket: do not use this build |
| 2 | usage error, bad item file, missing configuration (`LLM_BASE_URL`, CA file, key file) | operator | ticket |
| 3 | canary outside tolerance, or drafting refused (latest canary failed or older than 31 days) | operator | **page during office hours**: stop drafting, re-certify (or `--air-gapped`) |
| 4 | endpoint not certified (missing, expired, FAIL, does not verify) | operator | ticket: `make certify` |
| 5 | certificate FAIL | operator | ticket: this endpoint/model must not draft the SL lane |
| 6 | endpoint or feed failed after retries (timeout ≤ about 5 min per request), or feed not yet published | none at first | the next run resumes. Page if two runs in a row exit 6 |
| 7 | certificate PENDING_REVIEW | reviewer | ticket: label `needs_review`, then `certify --resolve` |
| 130 | interrupted | none | re-run |

The same table is in [`alert.sh`](alert.sh) (`alert.sh --code N --name JOB` works outside systemd too) and in
[docs/operations.md](../operations.md) §6. For Kubernetes, alert on `kube_job_status_failed{namespace="gleichlaut"} > 0`
(kube-state-metrics). The exit code is in the pod's `state.terminated.exitCode`. The audit exits 0 even when it finds
divergences, because finding them is its purpose: read `out/audit/audit_<date>_summary.json`, or forward the findings
count to your dashboard.

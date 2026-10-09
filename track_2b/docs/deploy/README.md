# Scheduling and alerting

Two ways to run Gleichlaut unattended: systemd on a server, or Kubernetes. Both run the default lane, the local Apertus
8B GGUF on CPU (a certified build, `eval/certificates/8b-q4_k_m-fresh166.json`), and offer the 70B on a certified
endpoint as an optional variant.

| Job | When | Needs | Command |
|---|---|---|---|
| audit | quarterly, or monthly after the publication | the public feed only (no model, no endpoint, no secret) | `gleichlaut feeds --latest`, then `gleichlaut.sl.ingest <date>`, then `gleichlaut audit --date <date> --fail-on-findings` (exit 8 on findings not marked likely equivalent) |
| month (default: 8B) | the 2nd of each month (BAG publishes on the 1st) | the offline image or a venv with `requirements-offline.txt`, the GGUF on a read-only path, **4 CPU cores and 8 GiB RAM** | `gleichlaut month --backend llamacpp --gguf /models/apertus-v1.5-8b-text-q4_k_m.gguf --from previous --to latest --fetch --emit` |
| certify (8B, once) | only with an HMAC key; again after a GGUF / llama-cpp-python / frozen-code change | nothing (seconds, no network) | `gleichlaut certify --import-run data/runs/8b_q4_k_m_fresh166_g3_final.jsonl --gguf-sha256 a037df8d… --labels eval/labels/m1_q4_k_m_fresh166.tsv` |
| canary (70B variant) | monthly, before the 70B month run | the certified endpoint and its key | `gleichlaut certify --backend openai --canary 40` |
| month-70b (variant) | the 2nd of each month, after the canary | the certified endpoint, a passing canary at most 31 days old | `gleichlaut month --backend openai --from previous --to latest --fetch --emit` |

Without a key the gate accepts the build certificate shipped in the image, so the 8B lane needs no certification step.
The 70B endpoint is certified by hand (`gleichlaut certify --backend openai`): once per endpoint and model, every 90
days, and after a failed canary. Timing of the 8B month: about 153 s per item on 4 cores, about 2.4 h at today's volume
of ~57 FR/IT items, about 24.5 h at 10× (`docs/operations.md` §1).

## systemd (a VM or a server, without Docker)

```bash
sudo useradd --system --home /var/lib/gleichlaut gleichlaut
sudo git clone <repo> /opt/gleichlaut && sudo python3 -m venv /opt/gleichlaut/venv
sudo apt-get install -y build-essential cmake            # llama-cpp-python is built from source (CPU only)
sudo CMAKE_ARGS="-DGGML_NATIVE=OFF" /opt/gleichlaut/venv/bin/pip install --require-hashes \
  -r /opt/gleichlaut/track_2b/requirements.txt -r /opt/gleichlaut/track_2b/requirements-offline.txt
sudo install -d -o gleichlaut -g gleichlaut /var/lib/gleichlaut/models
sudo -u gleichlaut env GLEICHLAUT_MODELS=/var/lib/gleichlaut/models PYTHONPATH=/opt/gleichlaut/track_2b/src \
  /opt/gleichlaut/venv/bin/python -m gleichlaut fetch-gguf                       # or copy the GGUF in (air-gapped host)
sudo chmod -R a-w /var/lib/gleichlaut/models                                     # the units mount it read-only anyway
sudo install -d -m 0750 /etc/gleichlaut
sudo install -m 0600 /dev/null /etc/gleichlaut/gleichlaut.env      # proxy/CA variables; for the 70B variant LLM_BASE_URL=..., LLM_API_KEY=..., LLM_NAME=...
sudo sh -c 'head -c 32 /dev/urandom > /etc/gleichlaut/cert.key && chmod 0400 /etc/gleichlaut/cert.key'   # optional HMAC key
sudo cp /opt/gleichlaut/track_2b/docs/deploy/systemd/* /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start gleichlaut-certify                  # with the HMAC key only: a signed build certificate in state/
sudo systemctl enable --now gleichlaut-month.timer gleichlaut-audit.timer
# the 70B variant instead of (or next to) the 8B month: certify the endpoint once, then the canary + month-70b timers
#   sudo -u gleichlaut env $(cat /etc/gleichlaut/gleichlaut.env) GLEICHLAUT_STATE=/var/lib/gleichlaut/state \
#     PYTHONPATH=/opt/gleichlaut/track_2b/src /opt/gleichlaut/venv/bin/python -m gleichlaut certify --backend openai
#   sudo systemctl enable --now gleichlaut-canary.timer gleichlaut-month-70b.timer
systemctl list-timers 'gleichlaut*'
```

The units are `oneshot` services. Each has `OnFailure=gleichlaut-alert@%n.service`, which runs
[`alert.sh`](alert.sh) with the failed unit's name. The script reads the unit's exit code (`ExecMainStatus`), writes
one line to the journal (`journalctl -t gleichlaut`), and mails it if `ALERT_MAIL` is set in `/etc/gleichlaut/alert.env`.
The units run with `ProtectSystem=strict` and write only under `/var/lib/gleichlaut`; the 8B month unit sees the models
directory read-only (`ReadOnlyPaths=`) and is limited to `MemoryMax=10G` and `CPUQuota=400%`. The HMAC key reaches the
process through `LoadCredential=`, readable only by the unit. Without a key, delete the two
`LoadCredential`/`GLEICHLAUT_CERT_KEY` lines. The 70B month writes to `/var/lib/gleichlaut/out-70b`, so both lanes can
run side by side without mixing their `--from previous`.

Prometheus: uncomment `GLEICHLAUT_METRICS_DIR=/var/lib/node_exporter/textfile_collector` in a unit (and add the directory
to `ReadWritePaths=`); node_exporter's textfile collector then exposes `gleichlaut_last_run_exit_code`,
`gleichlaut_items{status=...}`, `gleichlaut_shadow_rate_percent`, `gleichlaut_audit_findings{kind=...}` and the rest
(`docs/operations.md` §6).

## Kubernetes

| File | Contents |
|---|---|
| [`kubernetes/gleichlaut.yaml`](kubernetes/gleichlaut.yaml) | the default 8B lane: data PVC (state/ and out/), **models PVC (ReadOnlyMany, mounted read-only)**, ConfigMap, CronJob `gleichlaut-month` (offline image; requests and limits 4 CPU, 8 GiB / 10 GiB; 2nd of the month 06:00 Zurich), CronJob `gleichlaut-audit` (quarterly, `--fail-on-findings`) |
| [`kubernetes/certify-job.yaml`](kubernetes/certify-job.yaml) | one-off Jobs: `gleichlaut-fetch-gguf` (fills the models PVC), `gleichlaut-certify-build` (signed build certificate from the M1 run; seconds), `gleichlaut-certify-build-local` (the suite on the cluster's CPU; hours), `gleichlaut-certify-endpoint` (the 70B) |
| [`kubernetes/gleichlaut-70b.yaml`](kubernetes/gleichlaut-70b.yaml) | the 70B variant: ConfigMap with the endpoint, CronJob `gleichlaut-month-70b` with the canary as an init container |
| [`kubernetes/networkpolicy.yaml`](kubernetes/networkpolicy.yaml) | default deny (DNS only); egress to `epl.bag.admin.ch` for month and audit; for the 70B variant to the endpoint; for the one-off GGUF fetch to Hugging Face. Plain NetworkPolicy matches IP blocks (fill in the CIDRs, or allow only your egress proxy); a CiliumNetworkPolicy variant with `toFQDNs` is included |

The pods run as uid 10001, non-root, with no privilege escalation and all capabilities dropped. The root filesystem is
read-only: writes go only to the data PVC and an emptyDir `/tmp`. The GGUF PVC is mounted read-only in every pod except
the one-off fetch Job. `backoffLimit: 0` because a blind retry is wrong for exit 3, 4, 5 and 8; a manual re-run resumes
from `records.jsonl`. Metrics: `GLEICHLAUT_METRICS_DIR=/app/out/metrics` writes the textfiles to the data PVC; point a
textfile-collector sidecar (or a node_exporter on a node that mounts the PVC) at it.

## Exit codes and alerts

| Exit | Meaning | Who acts | Alert |
|---|---|---|---|
| 0 | success | | none (optionally a "ran" heartbeat: alert if no success in 35 days; `gleichlaut_last_run_timestamp_seconds`) |
| 1 | reproduction or validation failed | developer | ticket: do not use this build |
| 2 | usage error, bad item file, missing configuration (no certified GGUF and no `LLM_BASE_URL`, llama-cpp-python missing: use the offline image, CA file, key file, GGUF sha256 mismatch) | operator | ticket |
| 3 | 70B canary outside tolerance, or 70B drafting refused (latest canary failed or older than 31 days) | operator | **page during office hours**: stop drafting on the endpoint, re-certify, or draft with the local 8B |
| 4 | 70B endpoint not certified (missing, expired, FAIL, does not verify) | operator | ticket: `make certify-endpoint` |
| 5 | certificate FAIL | operator | ticket: this model must not draft the SL lane |
| 6 | endpoint or feed failed after retries (timeout ≤ about 5 min per request), or feed not yet published, or the GGUF download failed | none at first | the next run resumes. Page if two runs in a row exit 6 |
| 7 | certificate PENDING_REVIEW | reviewer | ticket: label `needs_review`, then `certify --resolve` |
| 8 | `audit --fail-on-findings`: divergences in the register | reviewer | ticket: read `out/audit/audit_<date>_summary.json` (a result, not a fault) |
| 130 | interrupted | none | re-run |

An uncertified 8B build is not an exit code: the month runs and every item is marked for review (`review_reason`; the
summary's `gate` is empty). Alert on it from the metrics if needed (`gleichlaut_items{status="ready"} == 0` over a run with
drafts). The same table is in [`alert.sh`](alert.sh) (`alert.sh --code N --name JOB` works outside systemd too) and in
[docs/operations.md](../operations.md) §6. For Kubernetes, alert on `kube_job_status_failed{namespace="gleichlaut"} > 0`
(kube-state-metrics). The exit code is in the pod's `state.terminated.exitCode`.

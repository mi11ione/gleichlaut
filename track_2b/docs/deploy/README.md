# Scheduling and alerting

Two ways to run Gleichlaut unattended: systemd on a server, or Kubernetes. Both run the default lane, the local Apertus
8B GGUF on CPU (a certified build: Q8_0 by default, `eval/certificates/8b-q8_0-fresh166.json`; Q4_K_M for an 8 GiB
box, `eval/certificates/8b-q4_k_m-fresh166.json`), and offer the 70B on a certified
endpoint as an optional variant.

| Job | When | Needs | Command |
|---|---|---|---|
| audit | quarterly, or monthly after the publication | the public feed only (no model, no endpoint, no secret) | `gleichlaut feeds --latest`, then `gleichlaut.sl.ingest <date>`, then `gleichlaut audit --date <date> --fail-on-findings` (exit 8 on findings not marked likely equivalent) |
| month (default: 8B) | the 2nd of each month (BAG publishes on the 1st) | the offline image or a venv with `requirements-offline.txt`, the GGUF on a read-only path, **4 CPU cores and 16 GiB RAM** (Q8_0; 8 GiB with Q4_K_M) | `gleichlaut month --backend llamacpp --gguf /models/apertus-v1.5-8b-text-q8_0.gguf --from previous --to latest --fetch --emit` |
| certify (8B, once) | only with an HMAC key; again after a GGUF / llama-cpp-python / frozen-code change | nothing (seconds, no network) | `gleichlaut certify --import-run data/runs/8b_q8_0_fresh166_g3_final.jsonl --gguf-sha256 dea904ad… --labels eval/labels/m1_q8_0_fresh166.tsv` (Q4_K_M: `8b_q4_k_m_…`, `a037df8d…`, `m1_q4_k_m_…`) |
| canary (70B variant) | monthly, before the 70B month run (the 2nd, 19:00 on systemd; an init container on Kubernetes) | the certified endpoint and its key | `gleichlaut certify --backend openai --canary 40` |
| month-70b (variant) | the 2nd of each month at 20:00, after the canary and after the 8B month (never at the same time: both use the same feed snapshots) | the certified endpoint, a passing canary at most 31 days old | `gleichlaut month --backend openai --from previous --to latest --fetch --emit` |

Without a key the gate accepts the build certificate shipped in the image, so the 8B lane needs no certification step.
The 70B endpoint is certified by hand (`gleichlaut certify --backend openai`): once per endpoint and model, every 90
days, and after a failed canary. Timing of the 8B month (Q8_0): 200.5 s per item on 4 cores, about 3.2 h at today's
volume of ~57 FR/IT items, about 32.0 h at 10× (Q4_K_M: 153.4 s, 2.4 h, 24.5 h; `docs/operations.md` §1).

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
directory read-only (`ReadOnlyPaths=`) and is limited to `MemoryMax=18G` (Q8_0; `10G` for Q4_K_M) and `CPUQuota=400%`. The HMAC key reaches the
process through `LoadCredential=`, readable only by the unit. Without a key, delete the two
`LoadCredential`/`GLEICHLAUT_CERT_KEY` lines. The 70B month writes to `/var/lib/gleichlaut/out-70b`, so both lanes can
be enabled without mixing their `--from previous`. They share the feed snapshots, so they do not run at the same time:
the 8B month starts the 2nd at 06:00, the 70B canary at 19:00 and the 70B month at 20:00, and
`gleichlaut-month-70b.service` is ordered `After=gleichlaut-month.service`, so it waits for an 8B month that is still
running.

Prometheus: uncomment `GLEICHLAUT_METRICS_DIR=/var/lib/node_exporter/textfile_collector` in a unit (and add the directory
to `ReadWritePaths=`); node_exporter's textfile collector then exposes `gleichlaut_last_run_exit_code`,
`gleichlaut_items{status=...}`, `gleichlaut_shadow_rate_percent`, `gleichlaut_audit_findings{kind=...}` and the rest
(`docs/operations.md` §6).

## Kubernetes

| File | Contents |
|---|---|
| [`kubernetes/gleichlaut.yaml`](kubernetes/gleichlaut.yaml) | the default 8B lane: data PVC (state/ and out/), **models PVC (ReadWriteOnce: written once, then mounted read-only)**, ConfigMap, CronJob `gleichlaut-month` (offline image; requests and limits 4 CPU, 16 GiB / 18 GiB for Q8_0, 8 GiB / 10 GiB for Q4_K_M; 2nd of the month 06:00 Zurich, 12 h deadline), CronJob `gleichlaut-audit` (quarterly, the 3rd 07:00, `--fail-on-findings`) |
| [`kubernetes/certify-job.yaml`](kubernetes/certify-job.yaml) | one-off Jobs, applied one at a time with `-l`: `gleichlaut-fetch-gguf` (fills the models PVC from Hugging Face or your mirror; proxy, CA and `GLEICHLAUT_MODEL_URL` from the ConfigMap; resumes an interrupted download), `gleichlaut-certify-build` (signed build certificate from the M2 run of Q8_0, or the M1 run of Q4_K_M; seconds), `gleichlaut-certify-build-local` (the suite on the cluster's CPU; hours), `gleichlaut-certify-endpoint` (the 70B) |
| [`kubernetes/models-loader.yaml`](kubernetes/models-loader.yaml) | the no-egress alternative to the fetch Job: a loader pod for `kubectl cp` and a sha256 check |
| [`kubernetes/gleichlaut-70b.yaml`](kubernetes/gleichlaut-70b.yaml) | the 70B variant: ConfigMap with the endpoint, CronJob `gleichlaut-month-70b` (the 2nd 20:00, after the 8B month's deadline) with the canary as an init container |
| [`kubernetes/networkpolicy.yaml`](kubernetes/networkpolicy.yaml) | direct egress: default deny (DNS only); egress to `epl.bag.admin.ch` for month and audit; for the 70B variant to the endpoint; for the one-off GGUF fetch to your mirror. Plain NetworkPolicy matches IP blocks (fill in the CIDRs); a CiliumNetworkPolicy variant with `toFQDNs` is included |
| [`kubernetes/networkpolicy-proxy.yaml`](kubernetes/networkpolicy-proxy.yaml) | behind an egress proxy, instead of the file above: default deny, and egress only to the proxy's address and port for the pods that need the network; the proxy enforces the host names |

Secrets and ConfigMaps you create yourself: `gleichlaut-cert-key` (the certificate HMAC key, **one Secret for both lanes
and every Job**; optional for the 8B lane, required for the 70B lane), `gleichlaut-endpoint` (`LLM_API_KEY` of the 70B
endpoint only), and optionally `gleichlaut-ca` (your internal CA bundle as `ca.pem`, mounted at `/etc/gleichlaut/ca` in
every pod that talks to the network; set `SSL_CERT_FILE: /etc/gleichlaut/ca/ca.pem` in the ConfigMap). The key Secret is
mounted with `optional: true` in the 8B pods, so it is in place when you add it later: create the Secret, uncomment
`GLEICHLAUT_CERT_KEY` in `gleichlaut-config`, and run `gleichlaut-certify-build` once (with a key, the unsigned shipped
build certificate is refused and every 8B draft goes to review until a signed copy is in `state/`).

The images are referenced by digest (`registry.example.ch/gleichlaut@sha256:CHANGE-ME`): fill them in from your CI (the
manifest header shows three ways to get the digest). Signing the pushed digests with cosign and admitting only verified
images is the next step ([docs/operations.md](../operations.md) §10).

Schedules: the CronJobs share the ReadWriteOnce data PVC and the feed snapshots under `out/hist`, so their windows never
overlap. `gleichlaut-month` runs the 2nd 06:00 with a 12 h deadline (done by 18:00), `gleichlaut-month-70b` the 2nd 20:00
with a 6 h deadline, `gleichlaut-audit` the 3rd 07:00 with a 1 h deadline. `concurrencyPolicy: Forbid` keeps each CronJob
from overlapping itself; Kubernetes has no lock between two CronJobs, so the stagger is what separates them (a test checks
it from the schedules and deadlines). If you change a schedule or a deadline, keep the windows apart.

The pods run as uid 10001, non-root, with no privilege escalation and all capabilities dropped
(`fsGroupChangePolicy: OnRootMismatch`, so a large volume is not re-chowned at every start). The root filesystem is
read-only: writes go only to the data PVC and an emptyDir `/tmp`. The GGUF PVC is mounted read-only in every pod except
the one-off fetch Job and the loader pod. `backoffLimit: 0` because a blind retry is wrong for exit 3, 4, 5 and 8; a manual
re-run (`kubectl -n gleichlaut create job --from=cronjob/gleichlaut-month gleichlaut-month-rerun-1`) resumes from
`records.jsonl`. Metrics: `GLEICHLAUT_METRICS_DIR=/app/out/metrics` writes the textfiles to the data PVC; point a
textfile-collector sidecar (or a node_exporter on a node that mounts the PVC) at it.

### Filling the models volume

The PVC `gleichlaut-models` is ReadWriteOnce: it is written once and then mounted read-only by the drafting pods
(`persistentVolumeClaim.readOnly` and `volumeMounts.readOnly`). Pick one way to fill it:

1. **From Hugging Face** (egress to `huggingface.co` and its CDN, directly or through the proxy):
   `kubectl apply -n gleichlaut -f kubernetes/certify-job.yaml -l job=fetch-gguf`. The Job reads `gleichlaut-config`, so
   `HTTPS_PROXY` and `SSL_CERT_FILE` apply to it. An interrupted download resumes from the `.part` file (HTTP Range) on
   the Job's next attempt (`backoffLimit: 3`).
2. **From an internal mirror** (a Nexus/Artifactory raw repository, an HTTPS file server): put the file there unchanged,
   set `GLEICHLAUT_MODEL_URL` in `gleichlaut-config` to its URL (same file name), and run the same Job. The sha256 check
   is still the pinned one, so the mirror can only serve the certified file. Narrow the `gleichlaut-fetch-gguf` policy in
   `networkpolicy.yaml` to the mirror's address.
3. **No egress at all:** download the file on a connected machine, check it there
   (`sha256sum apertus-v1.5-8b-text-q8_0.gguf` must print `dea904ad80cd725ec89962abae464477f5d8114d1f4377514f381f7dc2ed202d`),
   carry it in by your transfer process, then follow [`kubernetes/models-loader.yaml`](kubernetes/models-loader.yaml):
   apply the loader pod, `kubectl cp` the file to `/models/`, run `sha256sum` (and `python -m gleichlaut fetch-gguf`, which
   prints "GGUF verified" and downloads nothing when the file is right) in the pod, delete the pod. If your storage team
   can put the file on a volume directly (an NFS export, a pre-populated PV bound to the claim), that works as well: the
   pods only need the file at `/models/apertus-v1.5-8b-text-q8_0.gguf`.

The default build is Q8_0: file `apertus-v1.5-8b-text-q8_0.gguf`, sha256
`dea904ad80cd725ec89962abae464477f5d8114d1f4377514f381f7dc2ed202d`, 8,567,121,856 bytes, 16 GiB RAM. **The Q4_K_M build**
(`GLEICHLAUT_BUILD=q4_k_m`, for a node with 8 GiB RAM, also certified): file `apertus-v1.5-8b-text-q4_k_m.gguf`, sha256
`a037df8d87ff6caacee794ee85f55342f2152e0d359b7389033300c3bee5f299`, 5,059,027,136 bytes. Set `GLEICHLAUT_BUILD: q4_k_m`
in `gleichlaut-config` (the fetch Job then fetches and checks that file), change `--gguf` of `gleichlaut-month` to
`/models/apertus-v1.5-8b-text-q4_k_m.gguf`, and lower its memory request and limit to 8Gi / 10Gi
([docs/dependencies.md](../dependencies.md)). The PVC's 12Gi holds either file.

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

## Building inside a closed network

The Dockerfile reaches three places at build time; each has a build argument whose default is today's behaviour:

| Source | Default | Build argument |
|---|---|---|
| base image | `mirror.gcr.io/library/python:3.12-slim@sha256:a6e34c59…` | `BASE=registry.internal.example.ch/library/python:3.12-slim@sha256:a6e34c59…` (mirror the same digest) |
| Python packages | pypi.org | `PIP_INDEX_URL=https://pypi.internal.example.ch/simple`, and `PIP_TRUSTED_HOST=` only for a plain-HTTP mirror |
| Debian packages (offline image) | `http://deb.debian.org` | `APT_MIRROR=http://apt.internal.example.ch` (serving `/debian` and `/debian-security`) |

```bash
docker build --target offline \
  --build-arg BASE=registry.internal.example.ch/library/python:3.12-slim@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1 \
  --build-arg PIP_INDEX_URL=https://pypi.internal.example.ch/simple \
  --build-arg APT_MIRROR=http://apt.internal.example.ch \
  -t registry.internal.example.ch/gleichlaut-offline:<tag> track_2b
```

`pip install --require-hashes` checks every file against the lock, whichever index serves it, so a mirror can only serve
the pinned bytes. The index setting also reaches pip's build isolation, which fetches llama-cpp-python's build backend
(scikit-build-core) for the source build. **Known gap:** that build backend is neither version-pinned nor hash-checked
(pip's `--require-hashes` does not cover build isolation), and the apt packages are not version-pinned either. The SBOM
lists them as unpinned (`docs/sbom.json`; scope `excluded` for the build-only ones).

**Prebuilt wheel (closes the scikit-build-core gap and needs no compiler in the build):**

1. On one build host, build the wheel once with the image's flags:
   `CMAKE_ARGS="-DGGML_NATIVE=OFF -DLLAMA_CURL=OFF -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=OFF" pip wheel --no-deps llama-cpp-python==0.3.35 -w wheels/`
   (inside the same base image, so the wheel matches its Python and glibc), and record `sha256sum wheels/*.whl`.
2. Publish the wheel on your internal index, and add its hash to the `llama-cpp-python==0.3.35` entry of
   `requirements-offline.txt` (one more `--hash=sha256:…` line). pip prefers the wheel and builds nothing.
   `make lock` rewrites that file from PyPI's hashes, so add the line again after a re-lock.
3. Build with `--build-arg APT_BUILD=` (no `build-essential`/`cmake`; `libgomp1` stays).

The version stays 0.3.35, so the build certificates still apply (Operator FAQ, first question).

## Operator FAQ

Facts are what the code does today; **Recommendation** marks advice.

**1. How do I get the GGUF into a cluster with no egress, and does the build certificate hold for a llama-cpp-python I
built myself?**

Mirror or copy the file (see "Filling the models volume": internal mirror with `GLEICHLAUT_MODEL_URL`, or the loader
pod and `kubectl cp`). Gleichlaut checks the file's sha256 after every download, and the gate hashes the loaded file
before every SL run.

What a build certificate binds (`certify.write_build_certificate`, checked by `certify.build_lookup` and
`verify_build`):

- the GGUF's **sha256** (the loaded file is hashed each run);
- the **llama-cpp-python version string** as installed (`importlib.metadata.version("llama-cpp-python")`, e.g. `0.3.35`);
- the **frozen code**: the sha256 of `eval/prereg/freeze.json`, and the sha256 of the suite file;
- its stored **records and labels** (sha256 of each), which are re-scored with the frozen checks to the same PASS and
  metrics at each use;
- with `GLEICHLAUT_CERT_KEY`, an **HMAC** over all of the above.

It does not bind how llama-cpp-python was compiled (compiler, CMake flags, CPU, BLAS), the Python or numpy version, or
the base image. So a wheel you build yourself from the 0.3.35 source reports version 0.3.35 and the certificate holds.
That is already the case for the image: the shipped certificates come from the M1 and M2 runs on GitHub's CPU runners
(`CMAKE_ARGS="-DGGML_NATIVE=OFF"`, source build), and the Dockerfile compiles the same version again.

Re-certification is needed after: another GGUF file (any other sha256, including a re-quantisation), another
llama-cpp-python version, a change to `eval/prereg/freeze.json` or the suite, or a new HMAC key (question 2). Without a
valid certificate the month still runs, but every 8B item goes to review (`review_reason`), no exit code. Custom check
resources (`GLEICHLAUT_RESOURCES`) void every certificate.

**Recommendation:** because compile flags are not bound, run `gleichlaut-certify-build-local` once on your own build
and hardware (~9.2 h on 4 cores for Q8_0, ~7.1 h for Q4_K_M). It writes a certificate from your own run and lists any
ready output that differs from the labelled M1 / M2 outputs in `needs_review`.

**2. Who owns the HMAC key and `state/`: generation, rotation, backup?**

What the code does:

- The key is a file named by `GLEICHLAUT_CERT_KEY`, at least 16 bytes (`certify.cert_key`; shorter or unreadable is
  exit 2). On Kubernetes it is the Secret `gleichlaut-cert-key`, one for both lanes; on systemd `/etc/gleichlaut/cert.key`
  passed by `LoadCredential=`. Gleichlaut never writes it anywhere.
- With a key set, every certificate and canary report is HMAC-SHA256-signed when written, and every one that is unsigned
  or signed with another key is refused when read ("HMAC does not match (edited, or signed with another key)"). Without
  a key, signatures are not checked.
- **Rotation:** with a new key, everything signed with the old one is refused: the 8B build certificate (every 8B item
  goes to review until you run `gleichlaut-certify-build` again: seconds), the 70B endpoint certificate (exit 4 until
  `gleichlaut-certify-endpoint`: about 285 requests, under an hour) and the canary reports (ignored, so the next canary
  runs against the new certificate). There is no re-sign command; old files stay in `state/` untouched, and the newest
  certificate for a GGUF or an endpoint decides.
- `state/` holds the certificates, their suite records and call logs, the canary reports, the recorded responses and
  `gate-overrides.jsonl`. Losing it: the 8B lane without a key falls back to the certificate shipped in the image; with
  a key, every 8B item goes to review until `gleichlaut-certify-build` runs again; the 70B lane exits 4 until
  re-certified.

**Recommendation:** the platform team owns the key like any other service secret: generate it once
(`head -c 32 /dev/urandom`), keep the master copy in the organisation's secret store (Vault, KMS), and create the
Kubernetes Secret from there. Rotate on staff change or suspected exposure, and then run `gleichlaut-certify-build` and,
for the 70B lane, `gleichlaut-certify-endpoint` and a canary in the same change window. Keep retired keys in the secret store:
certificates signed with them can still be checked later (`GLEICHLAUT_CERT_KEY=/path/to/old.key gleichlaut certify --list`
with `GLEICHLAUT_STATE` on a copy of `state/`). Back up `state/` with the month outputs. It is the evidence that the model was fit when a draft was
made ([docs/operations.md](../operations.md) §8 retention).

**3. Rollback when `freeze.json` changes, two versions side by side, and the XLIFF hand-off while a month is half done?**

What the code does:

- Every certificate records the sha256 of `eval/prereg/freeze.json`. When it changes, all certificates stop counting:
  8B items go to review, the 70B lane exits 4. The release notes say whether it changed ([docs/operations.md](../operations.md) §10).
- **Rollback:** the previous image carries its own `freeze.json` and its own shipped build certificate, and certificates
  in `state/` are never modified. But the **newest** certificate for a GGUF (with that llama-cpp-python version) or for an
  endpoint and model decides, without falling back to an older one (`build_lookup`, `lookup`). If you certified under the
  new version, the old version refuses that newest certificate. Then move the new version's certificates out of
  `state/certificates/`, or certify again under the old version (the 8B import takes seconds).
- **Two versions side by side** with different `freeze.json` must not share `state/`, because each would refuse the
  other's newest certificate. `GLEICHLAUT_STATE`, `GLEICHLAUT_OUT` and `GLEICHLAUT_HIST` set the three directories.
  **Recommendation:** give the second version its own (a second PVC, or `subPath: state-v2` / `out-v2`), run it in shadow
  mode, and compare `summary.json` of the same feed pair. Versions with the same `freeze.json` can share `state/`.
- **A half-done month:** `records.jsonl` gets one line per item, flushed and fsynced. A re-run of the same command skips
  finished keys and cuts a torn last line. `summary.json` is written only when every item is drafted, and `--from
  previous` counts only runs that have one. So the next run (the next schedule, or a manual `kubectl create job
  --from=cronjob/...`) resumes the same `out/month/<from>-<to>/`, unless BAG has published a newer feed in the meantime.
  In that case the new run spans from the last completed run to the newer feed in a new directory, and the half-done
  directory stays as it is. `--emit` runs only after the last item, and `gleichlaut emit --records … --items …` refuses
  an items file that has items without a record ("emit: no record for N item(s)"), so there is no partial XLIFF by default.
  **Recommendation:** to hand the translators the finished part early, emit for the drafted keys only. Write an items
  file with just the keys already in `records.jsonl` (e.g. `python3 -c` with `json`), run `gleichlaut emit --records
  out/month/<run>/records.jsonl --items done.json --n 0 --out out/month/<run>/emit-partial`, and at the end hand over only
  the units that were not in the partial file.

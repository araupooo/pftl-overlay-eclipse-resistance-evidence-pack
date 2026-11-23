# Methodology

## Pinned source

- Repository: postfiatorg/postfiatd, commit
  `0085a1ff885d6a446369cf73a4430f75af22be55` (2026-10-10, PR #50 merge,
  v1.0.9).
- A local checkout at `/tmp/postfiatd-pin` was verified with
  `git rev-parse HEAD` to equal that commit before any excerpt was
  taken.
- Every excerpt in `fixtures/source-excerpts/` was pulled by
  `scripts/extract_excerpts.py` with an explicit 1-based line range and
  an anchor string that must appear in the extracted text; a wrong range
  fails loudly. Blob SHAs and sizes are in
  `fixtures/source-hashes.json`.
- Line numbers in this pack come from `grep -n` on that checkout, never
  from a browser fetch of a raw file.

## Live probes

- Endpoint: https://rpc.testnet.postfiat.org/ (public JSON-RPC),
  network ID 2025.
- 14 HTTP calls total: 8 RPC methods (`server_info`, `ledger_current`,
  `ledger_closed`, `fee`, `feature`, `validators`, `peers`,
  `ledger_request`), 1 validator-list GET, 3 explorer GETs, 2
  `ledger_current` reads for the cadence window.
- The cadence measurement is two `ledger_current` reads 60 s apart:
  8286469 -> 8286489, 20 ledgers in 61.0 s, 3.049 s/ledger.
- The validator-list document (https://postfiat.org/testnet_vl.json) is
  v2 format: the `blobs_v2` entry is base64 JSON; the blob was decoded
  locally (sequence 30, 25 validators). The blob signature was NOT
  verified: that needs Ed25519, which is not in the Python standard
  library (gap G-05).
- Unedited probe outputs are in `outputs/rpc-*.json` and
  `outputs/testnet_vl.json`; `outputs/probe-run.log` records the probe
  timestamps and the full SHA-256 of each output file.

## Lab drills

- All three drills run in `scripts/drill.py` against the pure-stdlib
  model in `src/overlay_model.py`. No network access happens in the
  drills: no peer connection, no traffic to the live network, no
  transaction.
- The model mirrors pinned rules, not live behaviour: the slot
  arithmetic mirrors `PeerfinderConfig`, the peer score mirrors
  `PeerImp::getScore`, the manifest caps mirror `ManifestMessages.h`,
  the backoff mirrors `peerfinder/detail/Tuning.h`.
- The manifest-cap drill is a mirror of the C++ rule, not the C++ code
  itself: it checks the same inequalities (`size <= 512`,
  `count <= 500`, `bytes <= 512 KiB`) that the pinned code enforces,
  and the 513-byte rejection case is the same input the pinned test
  asserts on (`manifest_flood_test.cpp:238`).
- The peer-score simulation uses a fixed seed (7) and 20000 trials, so
  it is deterministic across runs.
- Every drill case is timed individually with `time.monotonic()`. The
  elapsed time is printed on the case's PASS/FAIL line and stored as
  `elapsed_ms` in `outputs/derived/drill-results.json`. Per-drill and
  total wall times are also recorded.
- Drill result: 24/24 PASS (A 8, B 6, C 10), total wall 322.81 ms.

## Boundaries

- Eclipse, churn, and flood traffic are lab-only. No attempt was made
  to eclipse, flood, or churn the live network, and no peer connection
  was opened to it.
- No transaction was submitted and no vote was cast.
- The public RPC proxy refuses admin methods with HTTP 403. Those
  refusals are recorded as measurements; no admin access was sought.
- Lab keys: none were needed. No key material of any kind appears in
  this pack.

## Counting discipline

Every count in this pack was recomputed from the table it summarizes
before being written into any summary:

- Findings: 12 (3 HIGH, 6 MEDIUM, 2 LOW, 1 INFO; 7 MEASURED,
  5 SPECIFIED) — counted from `findings.json`.
- Claims: 30 (19 VERIFIED, 9 SPECIFIED, 1 UNVERIFIED, 1 UNTESTABLE) —
  counted from `docs/claim-index.md`, where status is column 2.
- Risks: 14 (3 HIGH, 6 MEDIUM, 4 LOW, 1 INFO) — counted from
  `docs/risk-register.md`.
- Gaps: 7 — counted from `docs/gap-register.md`.
- Drills: 24 cases (A 8, B 6, C 10), all PASS — counted from
  `outputs/derived/drill-results.json`.

If a summary and its table ever disagree, the table wins.

## Reproduction

`scripts/clean_reproduce.sh` re-runs everything fresh from a clean
checkout of this pack: it re-verifies the pinned commit, re-extracts
the excerpts, re-probes the live testnet (including a fresh 60 s
cadence window), re-runs the drills, re-runs the analysis, and compares
the fresh results with the shipped ones
(`scripts/compare_reproduce.py`). It exits 0 only if every check
passes. The fresh-clone reproduction outputs are kept under
`outputs/fresh-clone/` and their comparison log at
`outputs/fresh-clone-compare.log`.

# PFTL Peer-to-Peer Overlay and Eclipse-Resistance Evidence Pack

## Verdict: BOUNDED BUT UNAUDITABLE FROM OUTSIDE

The overlay mechanisms in the pinned postfiatd revision are well bounded:
manifest floods are capped at 512 bytes per manifest, 500 manifests and
512 KiB per batch; a full eclipse needs all 21 peer slots from at least
6 distinct IPs; and an eclipse of one node cannot forge consensus, since
17 of 25 validator validations are still required. All 24 lab drill cases
pass. But the live peer surface cannot be audited from outside: the
`peers` and `validators` RPC methods are admin-only (HTTP 403 from the
public proxy), so nobody outside the operator can see who the 21 peers
are, whether the node has fixed peers, or whether its address cache is
diverse. And the live node sits exactly at the default 21-peer cap, with
zero spare slots.

- Pinned source: postfiatorg/postfiatd commit
  `0085a1ff885d6a446369cf73a4430f75af22be55` (2026-10-10, PR #50 merge,
  v1.0.9)
- Live network: PFTL testnet, network ID 2025 (not XRPL mainnet)
- Probed: 2026-11-23 02:25-02:26 UTC (09:25-09:26 WIB) via
  https://rpc.testnet.postfiat.org/ — 14 HTTP calls total, all read-only
- Live at probe time: build 1.0.9, validated ledger 8286463, complete
  ledgers 8200054-8286463, 21 peers, quorum 17, cadence 3.049 s/ledger,
  validator list sequence 30 with 25 validators

## Counts (recomputed from their tables)

| Table | Count |
| --- | --- |
| Findings | 12 — 3 HIGH, 6 MEDIUM, 2 LOW, 1 INFO; 7 MEASURED, 5 SPECIFIED |
| Claims | 30 — 19 VERIFIED, 9 SPECIFIED, 1 UNVERIFIED, 1 UNTESTABLE |
| Risks | 14 — 3 HIGH, 6 MEDIUM, 4 LOW, 1 INFO |
| Gaps | 7 |
| Drill cases | 24/24 PASS (A 8, B 6, C 10), every case with its own elapsed time |
| Source excerpts | 24 files, line numbers verified with grep -n on the pinned checkout |

## How to reproduce

```sh
bash scripts/clean_reproduce.sh
# exit 0 only if every check passes; prints one PASS line per check.
# Re-probes the live testnet (includes a 60 s cadence window) and
# re-runs the drills from the pinned checkout.
bash scripts/verify_digests.sh   # verifies SHA256SUMS, exit 0
python3 scripts/drill.py         # lab drills only, no network access
python3 scripts/probe_all.py     # read-only live probes only
```

## File map

| Path | Contents |
| --- | --- |
| `README.md` | This file: verdict, counts, reproduce steps, file map |
| `docs/decision-memo.md` | Verdict and reasoning |
| `docs/overlay-inventory.md` | Source-cited inventory of every overlay mechanism |
| `docs/peer-surface.md` | Live peer-surface measurements |
| `docs/methodology.md` | How each measurement was made; boundaries |
| `docs/runbook-a.md` | Drill A: eclipse-attempt simulation (lab peer-set model) |
| `docs/runbook-b.md` | Drill B: peer-churn and re-connection timing (lab model) |
| `docs/runbook-c.md` | Drill C: manifest-flood handling (lab cap mirror) |
| `docs/risk-register.md` | 14 risks |
| `docs/gap-register.md` | 7 gaps |
| `docs/claim-index.md` | 30 claims with status and evidence pointer |
| `docs/citations.md` | Every pinned-source citation with file and line |
| `docs/evidence-index.md` | Every output file and what it proves |
| `docs/index.html` | Rendered results page |
| `findings.json` | 12 findings, machine-readable |
| `run-manifest.json` | Run record: versions, counts, digests |
| `configs/overlay-thresholds.json` | Every pinned constant in one place |
| `src/overlay_model.py` | Pure-stdlib model of the overlay rules |
| `scripts/` | probe_all.py, analyze.py, drill.py, extract_excerpts.py, clean_reproduce.sh, compare_reproduce.py, verify_digests.sh, make_sha256sums.sh |
| `fixtures/source-excerpts/` | 24 verbatim pinned-source excerpts |
| `fixtures/source-hashes.json` | Git blob SHA and size per excerpted file |
| `outputs/` | Unedited probe outputs, derived tables, drill-run.log, fresh-clone reproduction |

## Boundaries (read before re-running)

- Read-only probes only: no transaction submitted, no vote cast.
- No peer connection is ever opened to the live network. Eclipse,
  churn, and flood traffic exist only as lab models in `scripts/drill.py`
  and `src/overlay_model.py`.
- The `peers`, `validators`, and `ledger_request` RPC methods are
  admin-only; the public proxy returns HTTP 403 for them. That refusal is
  a recorded measurement, not a failure to probe.
- Claims that cannot be tested without attacking the live network are
  marked UNTESTABLE (see claim C-30), not silently assumed.

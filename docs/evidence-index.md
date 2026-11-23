# Evidence Index

## Unedited live probe outputs (`outputs/`)

| File | Proves |
| --- | --- |
| `outputs/rpc-server_info.json` | Build 1.0.9, network 2025, 21 peers, quorum 17, complete 8200054-8286463, validated 8286463, load factor 1, io latency 1 ms, 103 peer disconnects |
| `outputs/rpc-ledger_current.json` | Ledger current index 8286464 |
| `outputs/rpc-ledger_closed.json` | Ledger closed index 8286464 |
| `outputs/rpc-fee.json` | Base fee 10 drops, median 5000, queue 0/2000 |
| `outputs/rpc-feature.json` | 101 amendments, 64 enabled |
| `outputs/rpc-validators.json` | HTTP 403 (admin-only method) |
| `outputs/rpc-peers.json` | HTTP 403 (admin-only method) |
| `outputs/rpc-ledger_request.json` | HTTP 403 (admin-only method) |
| `outputs/testnet_vl.json` | Validator-list document v2 (14781 bytes; blob sequence 30, 25 validators) |
| `outputs/probe-run.log` | Probe timestamps, per-call results, full SHA-256 of each probe output |

## Derived tables (`outputs/derived/`)

| File | Proves |
| --- | --- |
| `outputs/derived/probe-summary.json` | All live numbers in one table, incl. cadence 3.049 s/ledger and explorer results |
| `outputs/derived/peer-surface.json` | Peer-surface table: 21 peers = default cap, 0 spare slots, admin refusals |
| `outputs/derived/eclipse-inputs.json` | Slot split, IP count, eclipse probabilities, quorum thresholds |
| `outputs/derived/manifest-limits.json` | Manifest and batch limits, greeting bound, legacy dump limit |
| `outputs/derived/drill-results.json` | All 24 drill cases with status, detail, and per-case `elapsed_ms` |
| `outputs/derived/run-checks.json` | 8/8 analysis checks PASS |

## Drill log

| File | Proves |
| --- | --- |
| `outputs/drill-run.log` | Unedited drill output: every case PASS/FAIL line with its measured elapsed time, per-drill and total wall times |

## Fresh-clone reproduction (`outputs/fresh-clone/`)

| File | Proves |
| --- | --- |
| `outputs/fresh-clone-compare.log` | 11/11 compare checks PASS; fresh validated ledger advanced past the shipped one |
| `outputs/fresh-clone/derived/probe-summary.json` | Fresh live probe (re-run at reproduction time) |
| `outputs/fresh-clone/derived/drill-results.json` | Fresh drill run: 24/24 PASS |
| `outputs/fresh-clone/derived/run-checks.json` | Fresh analysis checks |

## Pinned-source evidence (`fixtures/`)

| File | Proves |
| --- | --- |
| `fixtures/source-excerpts/*.txt` (24 files) | Verbatim pinned-source excerpts with file path and line ranges |
| `fixtures/source-hashes.json` | Git blob SHA and size for each of the 18 excerpted source files |

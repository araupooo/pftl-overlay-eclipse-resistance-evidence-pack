# Live Peer-Surface Measurement — 2026-11-23 02:25-02:26 UTC

Method: read-only JSON-RPC POSTs to https://rpc.testnet.postfiat.org/
plus HTTP GETs of the public validator-list document and the explorer
homepage. 14 HTTP calls total. No transaction submitted, no vote cast,
no peer connection opened. Unedited outputs in `outputs/rpc-*.json`,
`outputs/testnet_vl.json`, and `outputs/probe-run.log`; derived tables
in `outputs/derived/peer-surface.json`.

## Node identity and liveness

| Field | Value | Source |
| --- | --- | --- |
| Build version | 1.0.9 | `outputs/rpc-server_info.json` |
| Network ID | 2025 (PFTL testnet) | same |
| Host ID | MUFF | same |
| Server state | full | same |
| Validated ledger | 8286463 (age 2 s) | same |
| Complete ledgers | 8200054-8286463 | same |
| Ledger current / closed | 8286464 / 8286464 | `outputs/rpc-ledger_current.json`, `outputs/rpc-ledger_closed.json` |
| Cadence | 3.049 s/ledger (20 ledgers in 61.0 s) | `outputs/derived/probe-summary.json` |
| Load factor | 1 | server_info |
| I/O latency | 1 ms | server_info |

## Peer surface

| Field | Value | Source |
| --- | --- | --- |
| Peers | 21 | server_info `peers` |
| Default peer cap | 21 (`defaultMaxPeers`) | peerfinder Tuning.h line 63 |
| Spare slots | 0 — the node is exactly at its default cap | F-01 |
| Outbound slots at default | 10 | PeerfinderConfig.cpp lines 38-44 |
| Inbound slots at default | 11 | PeerfinderConfig.cpp lines 94-112 |
| Peer disconnects (lifetime counter) | 103 | server_info `peer_disconnects` |
| Peer identities | NOT observable — `peers` RPC is admin-only | `outputs/rpc-peers.json` (HTTP 403) |

The 21-peer reading is the single most informative live number in this
pack: it equals the default cap exactly, so the node accepts no new peer
until one disconnects. Whether any of the 21 are fixed peers, cluster
members, or reservations cannot be seen from the public surface.

## Validator surface

| Field | Value | Source |
| --- | --- | --- |
| Validation quorum | 17 | server_info `validation_quorum` |
| Validator list format | v2 (`blobs_v2`) | `outputs/testnet_vl.json` |
| List sequence | 30 | decoded blob |
| Validators in list | 25 | decoded blob |
| Effective / expiration | 848261408 / 891447293 (Ripple epochs) | decoded blob |
| Publisher key | ED3F1E0DA736FCF99BE2880A60DBD470715C0E04DD793FB862236B070571FC09E2 | testnet_vl.json `public_key` |
| Publisher manifest | 288 characters | same |
| Blob signature | 140 characters (DER) | same |
| Blob size | 10652 bytes decoded; document 14781 bytes | same |
| Validator-set RPC view | NOT observable — `validators` RPC is admin-only | `outputs/rpc-validators.json` (HTTP 403) |

## Amendment surface (context, not overlay)

The `feature` RPC returns 101 amendments, 64 enabled
(`outputs/rpc-feature.json`). This is background context only; the
amendment inventory itself belongs to the amendment-monitoring pack.

## Explorer

| URL | Result |
| --- | --- |
| https://explorer.testnet.postfiat.org/ | HTTP 200, single-page-app shell |
| https://explorer.testnet.postfiat.org/health | HTTP 200, same single-page-app shell (no JSON health status exposed at this path) |
| https://explorer.postfiat.org/ | Connection closed without response |

## Admin-only methods (measured refusals)

| Method | HTTP status | Pinned role |
| --- | --- | --- |
| `peers` | 403 | `Role::ADMIN`, Handler.cpp line 144 |
| `validators` | 403 | `Role::ADMIN`, Handler.cpp line 188 |
| `ledger_request` | 403 | `Role::ADMIN`, Handler.cpp line 136 |

These refusals are measurements, not probe failures: they establish
that peer identities and the validator-set RPC view are not publicly
observable, which is the audit gap behind finding F-03.

## Fee surface (context)

`fee` RPC returns base fee 10 drops, median fee 5000 drops, open-ledger
fee 10 drops, queue 0/2000 (`outputs/rpc-fee.json`). Included because
load factor and fee state describe the same node's load posture; the
fee-market analysis itself belongs to the fee-market pack.

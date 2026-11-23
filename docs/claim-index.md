# Claim-to-Evidence Index

Status is column 2. VERIFIED means measured live or in a lab drill;
SPECIFIED means stated in the pinned code; UNVERIFIED means the claim
cannot be checked from the public surface; UNTESTABLE means testing it
would require attacking the live network.

| ID | Status | Claim | Evidence |
| --- | --- | --- | --- |
| C-01 | VERIFIED | The live testnet node runs postfiatd 1.0.9 | outputs/rpc-server_info.json (`build_version`) |
| C-02 | VERIFIED | The live network ID is 2025 (PFTL testnet, not XRPL) | outputs/rpc-server_info.json (`network_id`) |
| C-03 | VERIFIED | Validated ledger 8286463 at probe time (2026-11-23 02:26 UTC); complete ledgers 8200054-8286463 | outputs/rpc-server_info.json; outputs/derived/probe-summary.json |
| C-04 | VERIFIED | Ledger cadence is 3.049 s/ledger (20 ledgers in 61.0 s) | outputs/derived/probe-summary.json (`cadence`) |
| C-05 | VERIFIED | The live node reports 21 peers — exactly the default cap | outputs/rpc-server_info.json (`peers`); peerfinder Tuning.h line 63 |
| C-06 | VERIFIED | Validation quorum is 17 | outputs/rpc-server_info.json (`validation_quorum`) |
| C-07 | VERIFIED | The validator list is sequence 30 with 25 validators, publisher ED3F1E0DA736FCF99BE2880A60DBD470715C0E04DD793FB862236B070571FC09E2 | outputs/testnet_vl.json (decoded blob) |
| C-08 | VERIFIED | The `peers`, `validators`, and `ledger_request` RPC methods return HTTP 403 from the public proxy | outputs/rpc-peers.json; outputs/rpc-validators.json; outputs/rpc-ledger_request.json |
| C-09 | VERIFIED | The live `feature` list has 101 entries, 64 enabled | outputs/rpc-feature.json |
| C-10 | VERIFIED | The explorer homepage and /health both return HTTP 200 (single-page-app shell); explorer.postfiat.org closes the connection without responding | outputs/derived/probe-summary.json (`explorer`) |
| C-11 | SPECIFIED | At default settings a node holds 10 outbound and 11 inbound peer slots (21 total) | fixtures/source-excerpts/peerfinder-outpeers.txt (PeerfinderConfig.cpp lines 38-44, 94-112) |
| C-12 | SPECIFIED | Outbound slots follow `max((maxPeers * 15 + 50) // 100, 10)` | fixtures/source-excerpts/peerfinder-outpeers.txt |
| C-13 | SPECIFIED | At most 2 inbound connections per public IP by default, capped at `inPeers / 2` | fixtures/source-excerpts/peerfinder-ip-limit.txt (PeerfinderConfig.cpp lines 46-63) |
| C-14 | SPECIFIED | Fixed peers are tried first and bypass the slot caps | fixtures/source-excerpts/peerfinder-autoconnect.txt; fixtures/source-excerpts/slot-activation.txt |
| C-15 | SPECIFIED | Cluster members and reserved peers get a reserved slot | fixtures/source-excerpts/reserved-slot.txt (OverlayImpl.cpp lines 262-272) |
| C-16 | SPECIFIED | The handshake requires a secp256k1 public key, verifies the session signature, and rejects self-connections | fixtures/source-excerpts/handshake-verify.txt (Handshake.cpp lines 286-322) |
| C-17 | SPECIFIED | Only protocol versions 2.1 and 2.2 are spoken | fixtures/source-excerpts/protocol-versions.txt (ProtocolVersion.cpp lines 40-45) |
| C-18 | SPECIFIED | Peer score is `rand(0..9999) + 10000 if have-item - 30 * latency_ms` (or `- 8000` for unknown latency) | fixtures/source-excerpts/peer-score.txt (PeerImp.cpp lines 3623-3658) |
| C-19 | VERIFIED | The latency term cancels the have-item bonus at 333.33 ms | outputs/derived/drill-results.json (A-07) |
| C-20 | VERIFIED | A 5 ms peer wins the fetch-pack pick in 18.2% of trials against twenty 50 ms peers (fair share 4.76%) | outputs/derived/drill-results.json (A-07) |
| C-21 | VERIFIED | A full eclipse needs all 21 slots from at least 6 IPs, and a pool share above 0.933 for even odds on the outbound side | outputs/derived/drill-results.json (A-02, A-08) |
| C-22 | VERIFIED | Eclipsing 1 validator leaves quorum reachable; 9 must fall at once to halt consensus | outputs/derived/drill-results.json (A-05, A-06) |
| C-23 | VERIFIED | Losing all 10 outbound peers refills in one 10 s batch when candidates exist | outputs/derived/drill-results.json (B-02) |
| C-24 | VERIFIED | The connection-backoff ladder sums to 143 s over 10 failures and caps at 55 s | outputs/derived/drill-results.json (B-04) |
| C-25 | VERIFIED | A 513-byte manifest is rejected and a 512-byte one accepted | outputs/derived/drill-results.json (C-02, C-03) |
| C-26 | VERIFIED | Manifest batches are bounded at 500 manifests and 512 KiB | outputs/derived/drill-results.json (C-05, C-06, C-07) |
| C-27 | VERIFIED | The untrusted-manifest greeting payload is bounded at 512000 bytes (1000 x 512 B) | outputs/derived/drill-results.json (C-08) |
| C-28 | SPECIFIED | A legacy oversized manifest dump is drained once per connection, at most 256 MiB - 1 bytes, with a 300 s deadline | fixtures/source-excerpts/manifest-discard.txt (ManifestMessageDiscard.h lines 72-90) |
| C-29 | UNVERIFIED | The live public node configures fixed peers | Not publicly observable; no evidence either way (gap G-02) |
| C-30 | UNTESTABLE | The live node can be eclipsed in practice | Testing it would require attacking the live network; lab-only boundary (gap G-03) |

Summary: 30 claims — 19 VERIFIED, 9 SPECIFIED, 1 UNVERIFIED, 1 UNTESTABLE.

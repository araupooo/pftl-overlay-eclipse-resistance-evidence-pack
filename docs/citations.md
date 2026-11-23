# Citations — Pinned Source References

Pinned commit: postfiatorg/postfiatd
`0085a1ff885d6a446369cf73a4430f75af22be55` (2026-10-10, PR #50 merge,
v1.0.9). All line numbers verified with `grep -n` on the local
checkout of that commit. Excerpts in `fixtures/source-excerpts/`.

| # | File | Lines | What it proves | Excerpt |
| --- | --- | --- | --- | --- |
| 1 | src/xrpld/peerfinder/detail/Tuning.h | 39-44, 46-52, 54-63, 65-70, 79-80 | secondsPerConnect 10, maxConnectAttempts 20, outPercent 15, minOutCount 10, defaultMaxPeers 21, maxRedirects 30, backoff ladder | peerfinder-tuning.txt |
| 2 | src/xrpld/peerfinder/detail/PeerfinderConfig.cpp | 38-44, 94-112 | calcOutPeers formula; outPeers/inPeers derivation | peerfinder-outpeers.txt |
| 3 | src/xrpld/peerfinder/detail/PeerfinderConfig.cpp | 46-63 | ipLimit default 2, cap at inPeers/2 | peerfinder-ip-limit.txt |
| 4 | src/xrpld/overlay/detail/Tuning.h | 30-65 | converged 24, diverged 128, reply-node caps, send-queue limits, idle check 4 s, maxQueryDepth 3, read buffer 16384 | overlay-tuning.txt |
| 5 | src/xrpld/overlay/detail/PeerImp.cpp | 3623-3658 | PeerImp::getScore formula | peer-score.txt |
| 6 | src/xrpld/app/ledger/detail/LedgerMaster.cpp | 723-760 | getFetchPack: highest-score peer holding the range | fetch-pack-target.txt |
| 7 | src/xrpld/overlay/detail/ManifestMessages.h | 19-40 | Batch caps 500 / 512 KiB; maxManifestBytes 512; deserializeBoundedManifest | manifest-cap.txt |
| 8 | src/xrpld/overlay/detail/ManifestMessages.h | 50-72 | makeManifestMessages greeting; outbound 512-byte gate | manifest-greeting.txt |
| 9 | src/xrpld/overlay/detail/OverlayImpl.cpp | 638-660 | onManifests: batch limit charge, maxUntrusted per message | manifest-onmanifests.txt |
| 10 | src/test/overlay/manifest_flood_test.cpp | 230-240 | 513-byte manifest rejected | manifest-flood-test.txt |
| 11 | src/xrpld/overlay/detail/ManifestMessageDiscard.h | 72-90 | Legacy dump: one per connection, 256 MiB - 1, 300 s | manifest-discard.txt |
| 12 | src/xrpld/app/misc/Manifest.h | 280-290 | defaultMaxUntrustedManifests = 1000 | manifest-default-untrusted.txt |
| 13 | src/xrpld/overlay/detail/ObjectByHashLimits.h | 14-27 | 4096 objects / 8 MiB reply; 10000-hash tx-queue exception | object-by-hash-limits.txt |
| 14 | src/xrpld/overlay/detail/Handshake.cpp | 286-322 | secp256k1 check, digest verification, self-connection rejection | handshake-verify.txt |
| 15 | src/xrpld/overlay/detail/ProtocolVersion.cpp | 33-45 | Supported versions {2,1}, {2,2} | protocol-versions.txt |
| 16 | src/xrpld/peerfinder/detail/Counts.h | 68-86 | can_activate: fixed/reserved bypass slot caps | slot-activation.txt |
| 17 | src/xrpld/overlay/detail/OverlayImpl.cpp | 262-272 | Cluster/reservation reserved slot | reserved-slot.txt |
| 18 | src/xrpld/overlay/detail/OverlayImpl.cpp | 1401-1411 | autoConnect via peerFinder->autoconnect | autoconnect.txt |
| 19 | src/xrpld/peerfinder/detail/Logic.h | 493-505 | autoconnect: fixed first, attempts_needed | peerfinder-autoconnect.txt |
| 20 | src/xrpld/peerfinder/detail/Counts.h | 88-93 | attempts_needed caps at maxConnectAttempts | peerfinder-attempts.txt |
| 21 | src/xrpld/overlay/detail/OverlayImpl.cpp | 100-112 | 1 s timer: once_per_second, sendEndpoints, autoConnect, idle sweep every 4 s | idle-peers.txt |
| 22 | src/xrpld/overlay/ReduceRelayCommon.h | 36-41 | Squelch expiry: 600 s default, 10 s per peer, 3600 s max | squelch.txt |
| 23 | src/xrpld/rpc/detail/Handler.cpp | 134-136, 142-144, 186-188 | ledger_request, peers, validators are Role::ADMIN | rpc-admin-roles.txt |
| 24 | src/xrpld/app/misc/ValidatorList.h | 880-895 | ValidatorList::verify signature | validator-list-verify.txt |

## Live sources

| Source | What it proves |
| --- | --- |
| https://rpc.testnet.postfiat.org/ (JSON-RPC, network 2025) | server_info, ledger_current, ledger_closed, fee, feature; 403 refusals for peers, validators, ledger_request |
| https://postfiat.org/testnet_vl.json | Validator-list document v2: sequence 30, 25 validators |
| https://explorer.testnet.postfiat.org/ and /health | HTTP 200, single-page-app shell |
| https://explorer.postfiat.org/ | Connection closed without response |

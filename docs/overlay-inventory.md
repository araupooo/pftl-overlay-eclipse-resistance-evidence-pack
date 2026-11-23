# Overlay Inventory — PFTL Peer-to-Peer Overlay, Pinned postfiatd 0085a1ff

Every mechanism below is cited to the pinned source file and line
range. Excerpts live in `fixtures/source-excerpts/`; blob SHAs in
`fixtures/source-hashes.json`. Where postfiatd inherits a mechanism
from upstream XRPL (rippled), that is stated; the pinned code is the
authority in every case.

## 1. Peer discovery

| Mechanism | Pinned rule |
| --- | --- |
| Address sources | Fixed peers (config `[ips_fixed]`), fallback strings (`[ips]`), the on-disk peer database (StoreSqdb), and endpoints learned from connected peers via `sendEndpoints` |
| Autoconnect cadence | Once per second: `once_per_second()`, `sendEndpoints()`, `autoConnect()` (OverlayImpl.cpp lines 105-111) |
| Batch interval | One batch of connection attempts every 10 s (`secondsPerConnect = 10`, peerfinder Tuning.h line 40) |
| Simultaneous attempts | At most 20 (`maxConnectAttempts = 20`, Tuning.h line 44; enforced by `Counts::attempts_needed`, Counts.h lines 88-93) |
| Attempt order | Fixed peers first, then other candidates (`Logic::autoconnect`, Logic.h lines 493-505) |
| Failed-endpoint backoff | Fibonacci seconds `[1, 1, 2, 3, 5, 8, 13, 21, 34, 55]`, capped at the last entry (Tuning.h lines 79-80) |
| Redirects | At most 30 per connection (`maxRedirects = 30`, Tuning.h line 70); redirects exist to stop address-cache flooding |
| Per-IP inbound cap | Default 2 connections per public IP, capped at `inPeers / 2` (PeerfinderConfig::applyTuning, lines 46-63) |

## 2. Connection and scoring

### Slot arithmetic (defaults)

- `defaultMaxPeers = 21` (peerfinder Tuning.h line 63)
- `outPeers = max((maxPeers * 15 + 50) // 100, 10)` — at 21 peers that is
  `max(3, 10) = 10` outbound (PeerfinderConfig.cpp lines 38-44)
- `inPeers = maxPeers - outPeers = 11` (PeerfinderConfig.cpp lines 94-112)
- If the node cannot accept incoming connections, `outPeers = maxPeers`
  (all 21 outbound)
- Fixed peers and reserved peers bypass the caps entirely:
  `Counts::can_activate` returns true for fixed/reserved slots regardless
  of the in/out maxima (Counts.h lines 68-86)

### Reserved slots

A connecting node gets a reserved slot if it is in the local cluster or
holds a peer reservation (OverlayImpl.cpp lines 262-272). Cluster
membership is a local configuration decision, not a network property.

### Handshake

- The peer must present a secp256k1 public key; any other key type is
  rejected (Handshake.cpp line 294)
- The session signature is verified against a shared value with
  `verifyDigest` (line 318); failure throws and the connection is refused
- A self-connection (peer's key equals the node's own identity) is
  rejected (line 322)
- The network ID is checked during the handshake (OverlayImpl.cpp line
  258 passes `setup_.networkID` into `verifyHandshake`)
- Protocol versions spoken: `{2, 1}` and `{2, 2}`; the negotiated version
  is the largest in the intersection of the two sides' lists
  (ProtocolVersion.cpp lines 40-45, 128-141)

### Peer score (used for fetch-pack target selection)

`PeerImp::getScore` (PeerImp.cpp lines 3623-3658):

```
score = rand_int(9999)
      + (10000 if the peer has the item else 0)
      - 30 * latency_ms            (if latency is known)
      - 8000                       (if latency is unknown)
```

The random 0..9999 component dominates: the latency term cancels the
10,000-point have-item bonus only at 333.33 ms. Drill A-07 measures the
consequence: a 5 ms peer wins the pick in 18.2% of trials against twenty
50 ms peers (fair share 4.76%) — an edge, not a takeover.

### Idle peers and send queues

- Idle peers are swept every 4 s (`checkIdlePeers = 4`, overlay Tuning.h
  line 58; OverlayImpl.cpp lines 111-112)
- Send-queue targets: 128 messages is the sustained target, 192 is the
  drop threshold, and 4 consecutive over-target intervals trigger a
  disconnect (overlay Tuning.h lines 46-52; PeerImp.cpp lines 728, 2595)
- Misbehaving peers accumulate resource charges (`PeerImp::charge`,
  PeerImp.cpp line 357); a charge that returns `Resource::drop`
  disconnects the peer (line 366). An over-limit manifest batch charges
  `feeInvalidData` (OverlayImpl.cpp line 651).

### Squelch (validation/proposal relay)

Squelch selects a random subset of peers as the relay sources for
validations and proposals, and squelches the rest for a bounded period:
minimum 600 s, 10 s per peer, maximum 3600 s
(ReduceRelayCommon.h lines 36-41; Slot.h lines 208-217). A selection
round restarts if the last selection is older than twice the 600 s
default (Slot.h line 341).

### Convergence thresholds

- `convergedLedgerLimit = 24`: a peer within 24 ledgers still counts as
  converged (overlay Tuning.h line 32)
- `divergedLedgerLimit = 128`: beyond 128 ledgers a peer counts as
  diverged (line 36)

## 3. Manifest propagation

| Rule | Pinned source |
| --- | --- |
| Largest legitimate manifest | 487 bytes (sfVersion 4 + sfSequence 5 + sfPublicKey 35 + sfSigningPubKey 35 + sfSignature 74 + sfMasterSignature 75 + sfDomain 259) — ManifestMessages.h lines 21-23 |
| Per-manifest cap | `maxManifestBytes = 512` (line 24); enforced on decode (`deserializeBoundedManifest`, line 38) and on outbound append (line 66) |
| Per-batch cap | `maxManifestBatchCount = 500`, `maxManifestBatchBytes = 512 * 1024` (lines 19-21); enforced by `manifestBatchWithinLimits` (lines 27-30) |
| Over-limit batch | The peer is charged `feeInvalidData` and the batch is dropped (OverlayImpl.cpp lines 649-653) |
| Untrusted manifests per message | At most `MAX_UNTRUSTED_MANIFESTS` per message; default 1000 (Manifest.h line 283; OverlayImpl.cpp lines 655-656) |
| Untrusted handling | Unlisted manifests are rate-limited (`ManifestRateLimitCapPolicy::capped`) while listed ones are uncapped (OverlayImpl.cpp lines 51-54); only listed manifests are persisted to disk (lines 71-77) |
| Greeting | A new peer receives every listed key's manifest (revocations included), then up to `maxUntrusted` randomly chosen unlisted live manifests, in count- and byte-bounded batches; revocations of unlisted keys are never sent (ManifestMessages.h lines 42-49) |
| Legacy oversized dump | A 1.0.4 peer whose initial cache dump exceeds its 26-bit frame is drained, never parsed: one dump per connection, at most 2^28 - 1 bytes, 300 s deadline; a repeat dump, impossible length, or timeout is a protocol failure (ManifestMessageDiscard.h lines 72-90) |
| Test | A 513-byte input is rejected (`manifest_flood_test.cpp` line 238) |

## 4. Fetch-pack behaviour

- When a ledger is missing, `LedgerMaster::getFetchPack` asks the
  highest-scoring peer that holds the range (LedgerMaster.cpp lines
  723-760). The score is the `getScore` formula above, so selection is
  mostly random among holders, mildly biased to low latency.
- The ledger header can also be recovered from a fetch pack
  (InboundLedger.cpp lines 283-288).
- Object-by-hash requests are bounded: at most 4096 objects per request
  and 8 MiB per reply (ObjectByHashLimits.h lines 14-16), except the
  transaction-queue type, which may request the 10,000-hash queue in one
  message (lines 21-26).
- Reply-node caps: `softMaxReplyNodes = 8192`, `hardMaxReplyNodes = 12288`
  (overlay Tuning.h lines 39-42).
- Query depth is capped at 3 (`maxQueryDepth = 3`, line 61).

## 5. Validator-list verification

- The validator list is verified by `ValidatorList::verify`
  (ValidatorList.h lines 890-895): a list is accepted only if its
  publisher manifest and signature check out. The signature math needs
  Ed25519, which is not in the Python standard library, so this pack
  records the blob as present-but-unverified (gap G-05).
- The live list is v2 format (`blobs_v2`): sequence 30, 25 validators,
  publisher key
  `ED3F1E0DA736FCF99BE2880A60DBD470715C0E04DD793FB862236B070571FC09E2`
  (see `docs/peer-surface.md`).

## 6. What the public RPC surface exposes — and does not

| Method | Role | Public result |
| --- | --- | --- |
| `server_info` | public | 200 — build, peers count, quorum, complete ledgers, validated ledger |
| `ledger_current`, `ledger_closed`, `fee`, `feature` | public | 200 |
| `peers` | `Role::ADMIN` (Handler.cpp line 144) | HTTP 403 from the public proxy |
| `validators` | `Role::ADMIN` (Handler.cpp line 188) | HTTP 403 from the public proxy |
| `ledger_request` | `Role::ADMIN` (Handler.cpp line 136) | HTTP 403 from the public proxy |

The peer count is public; peer identities, latencies, and the
validator-set RPC view are not. That is the audit gap behind finding
F-03.

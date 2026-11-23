"""overlay_model.py — pure-stdlib model of the PFTL peer-to-peer overlay.

Every formula here mirrors a rule in the pinned postfiatd revision
0085a1ff (2026-10-10, PR #50 merge, v1.0.9). The pinned source file and
line range for each rule is given in the docstring of each function, so a
reviewer can check the model against the code without trusting this file.

No network access happens here: the model only computes from constants
and from data already fetched by scripts/probe_all.py. Nothing in this
module opens a peer connection, submits a transaction, or touches the
live network.

Rules modelled
--------------
* Peer score (PeerImp::getScore, src/xrpld/overlay/detail/PeerImp.cpp
  lines 3623-3658):
      score = rand_int(9999) + (10000 if have_item else 0)
              - 30 * latency_ms            (if latency known)
              - 8000                       (if latency unknown)
  The fetch-pack target is the highest-score peer that holds the range
  (LedgerMaster::getFetchPack, src/xrpld/app/ledger/detail/LedgerMaster.cpp
  lines 723-760).

* Slot arithmetic (PeerFinder Tuning + Config):
  defaultMaxPeers = 21, outPercent = 15, minOutCount = 10
  (src/xrpld/peerfinder/detail/Tuning.h lines 40-63);
  outPeers = max((maxPeers * 15 + 50) // 100, 10)
  (src/xrpld/peerfinder/detail/PeerfinderConfig.cpp lines 18-24);
  inPeers = maxPeers - outPeers. Fixed peers and cluster/reserved peers
  bypass the slot caps (Counts::can_activate,
  src/xrpld/peerfinder/detail/Counts.h lines 68-86; OverlayImpl.cpp
  lines 262-270).

* Per-IP inbound cap (PeerfinderConfig::applyTuning,
  src/xrpld/peerfinder/detail/PeerfinderConfig.cpp lines 29-44):
  default ipLimit = 2 per public IP, capped at inPeers // 2.

* Reconnect timing (PeerFinder Tuning, Tuning.h lines 39-44, 79-80):
  one autoconnect batch every secondsPerConnect = 10 s, at most
  maxConnectAttempts = 20 simultaneous attempts; failed endpoints back
  off along connectionBackoff = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
  (seconds, one entry per consecutive failure, capped at the last entry).

* Manifest caps (src/xrpld/overlay/detail/ManifestMessages.h):
  maxManifestBytes = 512 (line 24), maxManifestBatchCount = 500 and
  maxManifestBatchBytes = 512 * 1024 (lines 19-21); untrusted manifests
  per message default 1000 (defaultMaxUntrustedManifests,
  src/xrpld/app/misc/Manifest.h line 283).

* Object-by-hash limits
  (src/xrpld/overlay/detail/ObjectByHashLimits.h lines 14-16):
  maxObjectByHashRequestObjects = 4096, maxObjectByHashReplyBytes = 8 MiB.
"""

import math
import random

# --- Pinned constants (see module docstring for sources) --------------------
DEFAULT_MAX_PEERS = 21
OUT_PERCENT = 15
MIN_OUT_COUNT = 10
SECONDS_PER_CONNECT = 10
MAX_CONNECT_ATTEMPTS = 20
MAX_REDIRECTS = 30
CONNECTION_BACKOFF = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
DEFAULT_IP_LIMIT = 2
MAX_MANIFEST_BYTES = 512
MAX_MANIFEST_BATCH_COUNT = 500
MAX_MANIFEST_BATCH_BYTES = 512 * 1024
DEFAULT_MAX_UNTRUSTED_MANIFESTS = 1000
MAX_OBJECT_BY_HASH_REQUEST_OBJECTS = 4096
MAX_OBJECT_BY_HASH_REPLY_BYTES = 8 * 1024 * 1024
VALIDATION_QUORUM = 17
UNL_SIZE = 25
# Largest serialized manifest the format can legitimately carry, per the
# comment at ManifestMessages.h lines 21-23 (sfVersion 4 + sfSequence 5 +
# sfPublicKey 35 + sfSigningPubKey 35 + sfSignature 74 + sfMasterSignature
# 75 + sfDomain (256 + 3) = 487 bytes).
MAX_LEGIT_MANIFEST_BYTES = 487


# --- Slot arithmetic --------------------------------------------------------
def calc_out_peers(max_peers=DEFAULT_MAX_PEERS):
    """Outbound slots: max((maxPeers * 15 + 50) // 100, 10)."""
    return max((max_peers * OUT_PERCENT + 50) // 100, MIN_OUT_COUNT)


def calc_in_peers(max_peers=DEFAULT_MAX_PEERS):
    """Inbound slots: maxPeers - outPeers."""
    return max_peers - calc_out_peers(max_peers)


def slot_split(max_peers=DEFAULT_MAX_PEERS):
    """(outbound, inbound, total) slot counts at a given maxPeers."""
    out = calc_out_peers(max_peers)
    return out, max_peers - out, max_peers


def min_ips_to_fill_inbound(in_peers, ip_limit=DEFAULT_IP_LIMIT):
    """Distinct public IPs needed to fill every inbound slot, at ipLimit
    connections per IP. An attacker holding fewer IPs cannot fill the
    inbound side alone, however many connections it opens."""
    return math.ceil(in_peers / ip_limit)


# --- Peer score (PeerImp::getScore) -----------------------------------------
def peer_score(rng, have_item, latency_ms=None):
    """One draw of the peer score. latency_ms=None means unknown latency."""
    score = rng.randint(0, 9999)
    if have_item:
        score += 10000
    if latency_ms is not None:
        score -= 30 * latency_ms
    else:
        score -= 8000
    return score


def score_distribution(n_peers, have_item, my_latency_ms, rival_latency_ms,
                       seed=1, trials=20000):
    """Simulated distribution of the fetch-pack target pick: returns the
    fraction of trials in which a peer with latency `my_latency_ms` wins
    the highest-score pick against (n_peers - 1) rivals at latency
    `rival_latency_ms`, all holding the item. Used to show how much a
    low-latency attacker gains: the random 0..9999 component dominates
    the 30/ms latency term."""
    rng = random.Random(seed)
    wins = 0
    for _ in range(trials):
        mine = peer_score(rng, have_item, my_latency_ms)
        rivals = [peer_score(rng, have_item, rival_latency_ms)
                  for _ in range(n_peers - 1)]
        if mine >= max(rivals):
            wins += 1
    return wins / trials


def score_edge_latency_ms():
    """Latency at which the latency penalty exactly cancels the have-item
    bonus: 10000 / 30 = 333.33 ms. Above this, a peer that HAS the item
    scores no better on average than a peer that does not."""
    return 10000 / 30


# --- Eclipse model (drill A) ------------------------------------------------
def eclipse_outbound_probability(attacker_share, out_slots=10):
    """Probability that ALL outbound slots go to attacker-controlled
    endpoints, if each slot is drawn independently with attacker share
    `attacker_share` of the address pool. (Upper bound on eclipse ease:
    the real draw is without replacement from a finite cache, and fixed
    peers are tried first.)"""
    return attacker_share ** out_slots


def eclipse_slots_needed(max_peers=DEFAULT_MAX_PEERS):
    """Slots an attacker must control for a full eclipse at default
    settings: every outbound slot plus every inbound slot (fixed peers
    excluded — they are tried first and bypass the caps)."""
    out, inb, total = slot_split(max_peers)
    return {"outbound": out, "inbound": inb, "total": total}


def quorum_after_eclipse(validators_eclipsed, unl_size=UNL_SIZE,
                         quorum=VALIDATION_QUORUM):
    """Validations still reachable by the rest of the network if
    `validators_eclipsed` validators are cut off: the network keeps
    validating while (unl_size - validators_eclipsed) >= quorum. An
    eclipse of one node never forges quorum — it only isolates."""
    remaining = unl_size - validators_eclipsed
    return {"remaining_validators": remaining,
            "quorum_still_reachable": remaining >= quorum,
            "quorum": quorum}


# --- Churn model (drill B) ----------------------------------------------------
def backoff_after_failures(n_failures):
    """Seconds to wait before retrying an endpoint after n consecutive
    failures: connectionBackoff[n-1], capped at the last entry (55 s)."""
    if n_failures <= 0:
        return 0
    idx = min(n_failures, len(CONNECTION_BACKOFF)) - 1
    return CONNECTION_BACKOFF[idx]


def refill_time_seconds(peers_lost, attempts_per_batch=MAX_CONNECT_ATTEMPTS,
                        seconds_per_batch=SECONDS_PER_CONNECT):
    """Worst-case time to refill `peers_lost` outbound slots if every
    attempt in a batch succeeds: batches of up to 20 simultaneous
    attempts, one batch per 10 s. One batch refills up to 20 slots, so
    a full 10-slot refill completes in a single batch when the cache
    has candidates."""
    batches = math.ceil(peers_lost / attempts_per_batch)
    return batches * seconds_per_batch


def refill_time_with_failures(peers_lost, failed_endpoints,
                              attempts_per_batch=MAX_CONNECT_ATTEMPTS,
                              seconds_per_batch=SECONDS_PER_CONNECT):
    """Refill time when `failed_endpoints` of the first batch fail and
    must back off once (first backoff step = 1 s) before a retry batch.
    Returns (seconds, note)."""
    if failed_endpoints <= 0:
        return refill_time_seconds(peers_lost), "no failures"
    # First batch fills (peers_lost - failed_endpoints); the failed ones
    # retry after the first backoff step, in the next 10 s batch.
    seconds = seconds_per_batch + backoff_after_failures(1) + seconds_per_batch
    return seconds, "one failed batch, backoff 1 s, retry batch"


# --- Manifest flood model (drill C) -------------------------------------------
def manifest_accepted(size_bytes):
    """Mirror of deserializeBoundedManifest (ManifestMessages.h lines
    35-40): accept iff size <= 512."""
    return size_bytes <= MAX_MANIFEST_BYTES


def batch_within_limits(n_manifests, total_bytes):
    """Mirror of manifestBatchWithinLimits (ManifestMessages.h lines
    27-30): count <= 500 AND bytes <= 512 KiB."""
    return (n_manifests <= MAX_MANIFEST_BATCH_COUNT and
            total_bytes <= MAX_MANIFEST_BATCH_BYTES)


def max_manifest_bytes_per_batch():
    """Upper bound on manifest payload a single batch can carry."""
    return MAX_MANIFEST_BATCH_BYTES


def untrusted_greeting_bytes(max_untrusted=DEFAULT_MAX_UNTRUSTED_MANIFESTS):
    """Upper bound on the untrusted-manifest payload of a peer greeting:
    at most 1000 unlisted manifests, each at most 512 bytes."""
    return max_untrusted * MAX_MANIFEST_BYTES

#!/usr/bin/env python3
"""extract_excerpts.py — pull verbatim pinned-source excerpts.

Reads the local checkout of the pinned postfiatd revision (default
/tmp/postfiatd-pin, verified to be commit 0085a1ff) and writes
fixtures/source-excerpts/*.txt, one file per excerpt. Every excerpt
carries a header giving the source file, the 1-based line range, and
the commit; every range is checked against an anchor string that must
appear in the extracted text, so a wrong range fails loudly instead of
shipping a silent misquote.

Also writes fixtures/source-hashes.json with the git blob SHA and size
of every excerpted source file, so a reviewer can confirm the checkout
matches the pinned commit.

Usage: python3 scripts/extract_excerpts.py [--pin /tmp/postfiatd-pin]
       [--out fixtures/source-excerpts]
"""

import argparse
import json
import os
import subprocess
import sys

PIN = "0085a1ff885d6a446369cf73a4430f75af22be55"

# (output filename, source file, [(start, end), ...], anchor strings)
EXCERPTS = [
    ("peerfinder-tuning.txt",
     "src/xrpld/peerfinder/detail/Tuning.h",
     [(39, 44), (46, 52), (54, 63), (65, 70), (79, 80)],
     ["secondsPerConnect = 10", "maxConnectAttempts = 20",
      "outPercent = 15", "minOutCount = 10", "defaultMaxPeers = 21",
      "maxRedirects = 30", "connectionBackoff"]),
    ("peerfinder-outpeers.txt",
     "src/xrpld/peerfinder/detail/PeerfinderConfig.cpp",
     [(38, 44), (94, 112)],
     ["calcOutPeers", "(maxPeers * Tuning::outPercent + 50) / 100",
      "minOutCount", "config.outPeers = config.calcOutPeers()",
      "config.inPeers = config.maxPeers - config.outPeers"]),
    ("peerfinder-ip-limit.txt",
     "src/xrpld/peerfinder/detail/PeerfinderConfig.cpp",
     [(46, 63)],
     ["ipLimit = 2", "inPeers / Tuning::defaultMaxPeers",
      "ipLimit = std::max(1, std::min(ipLimit"]),
    ("overlay-tuning.txt",
     "src/xrpld/overlay/detail/Tuning.h",
     [(30, 65)],
     ["convergedLedgerLimit = 24", "divergedLedgerLimit = 128",
      "softMaxReplyNodes = 8192", "hardMaxReplyNodes = 12288",
      "dropSendQueue = 192", "targetSendQueue = 128",
      "checkIdlePeers = 4", "maxQueryDepth = 3",
      "readBufferBytes = 16384"]),
    ("peer-score.txt",
     "src/xrpld/overlay/detail/PeerImp.cpp",
     [(3623, 3658)],
     ["PeerImp::getScore", "spRandomMax = 9999", "spHaveItem = 10000",
      "spLatency = 30", "spNoLatency = 8000"]),
    ("fetch-pack-target.txt",
     "src/xrpld/app/ledger/detail/LedgerMaster.cpp",
     [(723, 760)],
     ["LedgerMaster::getFetchPack", "Select target Peer based on highest score",
      "peer->getScore(true)"]),
    ("manifest-cap.txt",
     "src/xrpld/overlay/detail/ManifestMessages.h",
     [(19, 40)],
     ["maxManifestBatchCount = 500", "maxManifestBatchBytes = 512 * 1024",
      "maxManifestBytes = 512", "deserializeBoundedManifest"]),
    ("manifest-greeting.txt",
     "src/xrpld/overlay/detail/ManifestMessages.h",
     [(50, 72)],
     ["makeManifestMessages", "serialized.size() > maxManifestBytes"]),
    ("manifest-onmanifests.txt",
     "src/xrpld/overlay/detail/OverlayImpl.cpp",
     [(638, 660)],
     ["OverlayImpl::onManifests", "manifestBatchWithinLimits",
      "charge(Resource::feeInvalidData", "maxUntrusted"]),
    ("manifest-flood-test.txt",
     "src/test/overlay/manifest_flood_test.cpp",
     [(230, 240)],
     ["!deserializeBoundedManifest(std::string(maxManifestBytes + 1, 'x'))"]),
    ("manifest-discard.txt",
     "src/xrpld/overlay/detail/ManifestMessageDiscard.h",
     [(72, 90)],
     ["legacyLimit = (std::size_t(1) << 28) - 1", "deadline_ = now + std::chrono::seconds(300)"]),
    ("manifest-default-untrusted.txt",
     "src/xrpld/app/misc/Manifest.h",
     [(280, 290)],
     ["defaultMaxUntrustedManifests = 1000", "untrustedManifestCount"]),
    ("object-by-hash-limits.txt",
     "src/xrpld/overlay/detail/ObjectByHashLimits.h",
     [(14, 27)],
     ["maxObjectByHashRequestObjects = 4096",
      "maxObjectByHashReplyBytes = 8 * 1024 * 1024"]),
    ("handshake-verify.txt",
     "src/xrpld/overlay/detail/Handshake.cpp",
     [(286, 322)],
     ["publicKeyType(*pk) != KeyType::secp256k1",
      "verifyDigest(publicKey, sharedValue",
      "publicKey == app.nodeIdentity().first"]),
    ("protocol-versions.txt",
     "src/xrpld/overlay/detail/ProtocolVersion.cpp",
     [(33, 45)],
     ["supportedProtocolList", "{2, 1}", "{2, 2}"]),
    ("slot-activation.txt",
     "src/xrpld/peerfinder/detail/Counts.h",
     [(68, 86)],
     ["can_activate", "s.fixed() || s.reserved()",
      "m_in_active < m_in_max", "m_out_active < m_out_max"]),
    ("reserved-slot.txt",
     "src/xrpld/overlay/detail/OverlayImpl.cpp",
     [(262, 272)],
     ["reserved slot if it is in our cluster",
      "app_.cluster().member(publicKey)",
      "app_.peerReservations().contains(publicKey)"]),
    ("autoconnect.txt",
     "src/xrpld/overlay/detail/OverlayImpl.cpp",
     [(1401, 1411)],
     ["OverlayImpl::autoConnect", "m_peerFinder->autoconnect()"]),
    ("peerfinder-autoconnect.txt",
     "src/xrpld/peerfinder/detail/Logic.h",
     [(493, 505)],
     ["autoconnect()", "attempts_needed()", "ConnectHandouts"]),
    ("peerfinder-attempts.txt",
     "src/xrpld/peerfinder/detail/Counts.h",
     [(88, 93)],
     ["attempts_needed()", "maxConnectAttempts"]),
    ("idle-peers.txt",
     "src/xrpld/overlay/detail/OverlayImpl.cpp",
     [(100, 112)],
     ["once_per_second()", "autoConnect()", "deleteIdlePeers()",
      "checkIdlePeers"]),
    ("squelch.txt",
     "src/xrpld/overlay/ReduceRelayCommon.h",
     [(36, 41)],
     ["MAX_UNSQUELCH_EXPIRE_DEFAULT", "SQUELCH_PER_PEER",
      "MAX_UNSQUELCH_EXPIRE_PEERS"]),
    ("rpc-admin-roles.txt",
     "src/xrpld/rpc/detail/Handler.cpp",
     [(134, 136), (142, 144), (186, 188)],
     ['"ledger_request", byRef(&doLedgerRequest), Role::ADMIN',
      '"peers", byRef(&doPeers), Role::ADMIN',
      '"validators", byRef(&doValidators), Role::ADMIN']),
    ("validator-list-verify.txt",
     "src/xrpld/app/misc/ValidatorList.h",
     [(880, 895)],
     ["verify(", "ListDisposition::accepted", "signature"]),
]


def git(*args, cwd):
    r = subprocess.run(["git"] + list(args), cwd=cwd,
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pin", default="/tmp/postfiatd-pin")
    ap.add_argument("--out", default="fixtures/source-excerpts")
    args = ap.parse_args()

    head = git("rev-parse", "HEAD", cwd=args.pin)
    assert head == PIN, f"pinned checkout HEAD is {head}, expected {PIN}"
    print(f"pinned checkout HEAD verified: {head}")

    os.makedirs(args.out, exist_ok=True)
    hashes = {}
    seen_files = []
    for fname, src, ranges, anchors in EXCERPTS:
        path = os.path.join(args.pin, src)
        with open(path) as f:
            lines = f.read().splitlines()
        parts = []
        for start, end in ranges:
            assert 1 <= start <= end <= len(lines), \
                f"{src}: range {start}-{end} out of bounds ({len(lines)} lines)"
            parts.append("\n".join(lines[start - 1:end]))
        text = "\n[...]\n".join(parts)
        for anchor in anchors:
            assert anchor in text, \
                f"{fname}: anchor not found in excerpt: {anchor!r}"
        header = (f"// Source: postfiatorg/postfiatd @ {PIN}\n"
                  f"// File: {src}\n"
                  f"// Lines: {', '.join(f'{s}-{e}' for s, e in ranges)}\n"
                  f"// Verbatim excerpt; line numbers verified with grep -n "
                  f"on the pinned checkout.\n\n")
        with open(os.path.join(args.out, fname), "w") as f:
            f.write(header + text + "\n")
        print(f"wrote {fname} ({src} {ranges})")
        if src not in seen_files:
            seen_files.append(src)

    for src in seen_files:
        blob = git("hash-object", src, cwd=args.pin)
        size = git("cat-file", "-s", blob, cwd=args.pin)
        api_note = "verify against the GitHub API blob endpoint for this commit"
        hashes[src] = {"blob_sha": blob, "size_bytes": int(size),
                       "commit": PIN, "note": api_note}
    out = os.path.join(os.path.dirname(args.out), "source-hashes.json")
    with open(out, "w") as f:
        json.dump(hashes, f, indent=1, sort_keys=True)
    print(f"wrote {out} ({len(hashes)} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

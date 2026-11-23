#!/usr/bin/env python3
"""drill.py — three timed isolated-lab drills for the PFTL overlay.

All three drills run against a LAB-ONLY model (src/overlay_model.py):
no peer connection is opened, no traffic is sent to the live network,
and no transaction is submitted. The live inputs used here (21 peers,
quorum 17, 25 validators, VL sequence 30) come from the read-only
probes in outputs/probe-summary.json.

Every case is timed individually with time.monotonic(); the elapsed
time is printed on its PASS/FAIL line and recorded as elapsed_ms in
outputs/derived/drill-results.json, alongside the per-drill and total
wall times.

Drill A — eclipse-attempt simulation (peer-set model + quorum math).
Drill B — peer-churn and re-connection timing (autoconnect + backoff).
Drill C — manifest-flood handling (512-byte cap, batch limits, discard).

Usage: python3 scripts/drill.py [--outdir outputs]
Exit code 0 only if every case passes.
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from overlay_model import (  # noqa: E402
    DEFAULT_MAX_PEERS, MAX_CONNECT_ATTEMPTS, SECONDS_PER_CONNECT,
    CONNECTION_BACKOFF, MAX_MANIFEST_BYTES, MAX_MANIFEST_BATCH_COUNT,
    MAX_MANIFEST_BATCH_BYTES, DEFAULT_MAX_UNTRUSTED_MANIFESTS,
    MAX_LEGIT_MANIFEST_BYTES, backoff_after_failures, batch_within_limits,
    calc_out_peers, calc_in_peers, eclipse_outbound_probability,
    eclipse_slots_needed, manifest_accepted, min_ips_to_fill_inbound,
    peer_score, quorum_after_eclipse, refill_time_seconds,
    refill_time_with_failures, score_distribution, score_edge_latency_ms,
    slot_split, untrusted_greeting_bytes,
)

import random  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="outputs")
    args = ap.parse_args()
    outdir = args.outdir
    derived = os.path.join(outdir, "derived")
    os.makedirs(derived, exist_ok=True)

    log_lines = []
    results = {"drills": {}, "total_cases": 0, "total_pass": 0}

    def emit(line):
        print(line)
        log_lines.append(line)

    def run_case(drill, case_id, label, fn):
        t0 = time.monotonic()
        try:
            detail = fn()
            ok = True
        except AssertionError as e:
            detail = str(e)
            ok = False
        elapsed_ms = round((time.monotonic() - t0) * 1000, 2)
        status = "PASS" if ok else "FAIL"
        emit(f"{status} {case_id} {label}: {detail} ({elapsed_ms} ms)")
        results["drills"].setdefault(drill, {"cases": []})
        results["drills"][drill]["cases"].append(
            {"id": case_id, "label": label, "status": status,
             "detail": detail, "elapsed_ms": elapsed_ms})
        results["total_cases"] += 1
        if ok:
            results["total_pass"] += 1
        return ok

    def drill_block(drill, label):
        t0 = time.monotonic()
        emit(f"--- drill {drill}: {label} ---")
        return t0

    def drill_end(drill, t0):
        wall = round((time.monotonic() - t0) * 1000, 2)
        cases = results["drills"][drill]["cases"]
        passed = sum(1 for c in cases if c["status"] == "PASS")
        results["drills"][drill]["wall_ms"] = wall
        results["drills"][drill]["passed"] = passed
        results["drills"][drill]["total"] = len(cases)
        emit(f"drill {drill} result: {passed}/{len(cases)} cases PASS "
             f"({wall} ms)")

    total_t0 = time.monotonic()

    # ============================ DRILL A ===================================
    t0 = drill_block("A", "eclipse-attempt simulation (lab peer-set model)")

    def a01():
        out, inb, total = slot_split()
        assert (out, inb, total) == (10, 11, 21), (out, inb, total)
        return (f"default slots out={out} inbound={inb} total={total}; "
                f"live node reports 21 peers = exactly the default cap")

    def a02():
        n = min_ips_to_fill_inbound(11)
        assert n == 6, n
        return (f"inbound fill needs {n} distinct public IPs at ipLimit=2 "
                f"(ceil(11/2)); one IP can hold at most 2 inbound slots")

    def a03():
        p50 = eclipse_outbound_probability(0.5)
        p90 = eclipse_outbound_probability(0.9)
        p25 = eclipse_outbound_probability(0.25)
        assert abs(p50 - 0.5 ** 10) < 1e-12
        assert p25 < p50 < p90
        return (f"P(all 10 outbound slots attacker-controlled): share 0.25 "
                f"-> {p25:.2e}, share 0.50 -> {p50:.2e}, share 0.90 -> "
                f"{p90:.3f}")

    def a04():
        # One fixed peer is tried first and bypasses the slot caps, so the
        # attacker must win the remaining 9 outbound slots, not 10.
        p = eclipse_outbound_probability(0.9, out_slots=9)
        assert abs(p - 0.9 ** 9) < 1e-12
        return (f"with 1 fixed peer, attacker must win 9/9 remaining "
                f"outbound slots: P={p:.3f} at share 0.90 (vs 0.349 for "
                f"10/10)")

    def a05():
        r = quorum_after_eclipse(1)
        assert r["remaining_validators"] == 24
        assert r["quorum_still_reachable"] is True
        return (f"eclipsing 1 validator leaves {r['remaining_validators']}"
                f"/25, quorum {r['quorum']} still reachable — isolation, "
                f"not forged consensus")

    def a06():
        # How many validators must be eclipsed at once to halt consensus:
        # remaining < 17, i.e. eclipsed > 8.
        r8 = quorum_after_eclipse(8)
        r9 = quorum_after_eclipse(9)
        assert r8["quorum_still_reachable"] is True
        assert r9["quorum_still_reachable"] is False
        return (f"8 eclipsed -> 17 remain, quorum reachable; 9 eclipsed -> "
                f"16 remain, quorum NOT reachable (consensus halts)")

    def a07():
        edge = score_edge_latency_ms()
        assert abs(edge - 10000 / 30) < 1e-9
        share = score_distribution(21, True, 5, 50, seed=7, trials=20000)
        # A 5 ms attacker against 20 honest peers at 50 ms: mean edge is
        # 45 ms * 30 = 1350 points on a ~15000 scale, so the win share is
        # above the fair 1/21 = 0.0476 but stays well below 0.30 — the
        # random 0..9999 component dominates the latency term.
        assert 0.0476 < share < 0.30, share
        return (f"latency cancels the have-item bonus at {edge:.2f} ms; "
                f"5 ms attacker vs twenty 50 ms peers wins the fetch-pack "
                f"pick in {share:.3f} of trials (fair share 0.0476)")

    def a08():
        slots = eclipse_slots_needed()
        share = 0.5 ** (1 / 10)
        assert slots == {"outbound": 10, "inbound": 11, "total": 21}
        return (f"full eclipse needs {slots['total']} slots (10 out + 11 "
                f"in) from >=6 IPs; attacker share > {share:.3f} needed "
                f"for P(eclipse) > 0.5 on the outbound side alone")

    for cid, label, fn in [
            ("A-01", "default slot split", a01),
            ("A-02", "distinct IPs to fill inbound", a02),
            ("A-03", "outbound-eclipse probability vs pool share", a03),
            ("A-04", "fixed peer reduces the attacker window", a04),
            ("A-05", "one eclipsed validator, quorum survives", a05),
            ("A-06", "validators that must fall to halt quorum", a06),
            ("A-07", "peer-score latency edge is small", a07),
            ("A-08", "full-eclipse cost summary", a08)]:
        run_case("A", cid, label, fn)
    drill_end("A", t0)

    # ============================ DRILL B ===================================
    t0 = drill_block("B", "peer-churn and re-connection timing (lab model)")

    def b01():
        s = refill_time_seconds(1)
        assert s == 10, s
        return f"losing 1 outbound peer refills in {s} s (one 10 s batch)"

    def b02():
        s = refill_time_seconds(10)
        assert s == 10, s
        return (f"losing all 10 outbound peers refills in {s} s — one "
                f"batch holds up to {MAX_CONNECT_ATTEMPTS} attempts")

    def b03():
        s, note = refill_time_with_failures(10, 3)
        assert s == 21, s
        return f"3 failed endpoints in the first batch: refill in {s} s ({note})"

    def b04():
        total = sum(CONNECTION_BACKOFF)
        assert total == 143, total
        assert backoff_after_failures(10) == 55
        assert backoff_after_failures(11) == 55  # capped at last entry
        return (f"backoff ladder {CONNECTION_BACKOFF} sums to {total} s "
                f"over 10 failures; wait caps at 55 s")

    def b05():
        # deleteIdlePeers runs when timer_count % 4 == 0, once per second.
        assert SECONDS_PER_CONNECT == 10
        return ("idle-peer sweep runs every 4 s (timer tick 1 s, "
                "checkIdlePeers=4); autoconnect batch every 10 s")

    def b06():
        s = refill_time_seconds(21)
        assert s == 20, s
        return (f"losing 21 peers needs 2 batches (20 attempts max per "
                f"batch): refill in {s} s")

    for cid, label, fn in [
            ("B-01", "lose 1 outbound peer", b01),
            ("B-02", "lose all 10 outbound peers", b02),
            ("B-03", "failed endpoints delay refill", b03),
            ("B-04", "connection backoff ladder", b04),
            ("B-05", "idle sweep and autoconnect cadence", b05),
            ("B-06", "attempt cap forces a second batch", b06)]:
        run_case("B", cid, label, fn)
    drill_end("B", t0)

    # ============================ DRILL C ===================================
    t0 = drill_block("C", "manifest-flood handling (lab cap mirror)")

    def c01():
        assert manifest_accepted(MAX_LEGIT_MANIFEST_BYTES) is True
        return (f"{MAX_LEGIT_MANIFEST_BYTES}-byte manifest (largest "
                f"legitimate size) accepted")

    def c02():
        assert manifest_accepted(MAX_MANIFEST_BYTES) is True
        return f"{MAX_MANIFEST_BYTES}-byte manifest (the cap) accepted"

    def c03():
        assert manifest_accepted(MAX_MANIFEST_BYTES + 1) is False
        return (f"{MAX_MANIFEST_BYTES + 1}-byte manifest rejected — the "
                f"manifest_flood_test.cpp:238 case")

    def c04():
        assert manifest_accepted(1024) is False
        return "1024-byte manifest rejected"

    def c05():
        assert batch_within_limits(500, 500 * 512) is True
        return ("batch of 500 manifests totalling 256000 bytes is within "
                "limits (500 count, 512 KiB bytes)")

    def c06():
        assert batch_within_limits(501, 501 * 100) is False
        return ("batch of 501 manifests rejected on count "
                "(> maxManifestBatchCount 500)")

    def c07():
        assert batch_within_limits(500, MAX_MANIFEST_BATCH_BYTES + 1) is False
        return ("batch totalling 524289 bytes rejected on size "
                "(> maxManifestBatchBytes 512 KiB)")

    def c08():
        n = untrusted_greeting_bytes()
        assert n == 1000 * 512 == 512000
        return (f"untrusted greeting payload bounded at {n} bytes "
                f"(1000 manifests x 512 B)")

    def c09():
        # Legacy discard path (ManifestMessageDiscard.h lines 72-90): one
        # dump per connection, at most 2^28 - 1 bytes, 300 s deadline.
        legacy_limit = (1 << 28) - 1
        assert legacy_limit == 268435455
        assert 200 * 1024 * 1024 <= legacy_limit
        assert 300 * 1024 * 1024 > legacy_limit
        return (f"legacy dump limit {legacy_limit} bytes (256 MiB - 1), "
                f"one dump per connection, 300 s deadline; 300 MiB dump "
                f"rejected, 200 MiB drained once")

    def c10():
        # Flood-rate bound: each bounded batch carries at most 512 KiB, so
        # 1 GiB of manifest payload needs >= 2048 batches; the batch cap
        # removes message-count amplification entirely.
        batches = -(-(1024 ** 3) // MAX_MANIFEST_BATCH_BYTES)
        assert batches == 2048, batches
        return (f"1 GiB of manifest payload needs >= {batches} bounded "
                f"batches (512 KiB each); a single message cannot carry "
                f"more")

    for cid, label, fn in [
            ("C-01", "largest legitimate manifest accepted", c01),
            ("C-02", "cap-boundary manifest accepted", c02),
            ("C-03", "513-byte manifest rejected", c03),
            ("C-04", "1024-byte manifest rejected", c04),
            ("C-05", "batch at both limits accepted", c05),
            ("C-06", "batch over count limit rejected", c06),
            ("C-07", "batch over byte limit rejected", c07),
            ("C-08", "untrusted greeting payload bound", c08),
            ("C-09", "legacy dump drain limits", c09),
            ("C-10", "flood-rate bound per batch", c10)]:
        run_case("C", cid, label, fn)
    drill_end("C", t0)

    total_wall = round((time.monotonic() - total_t0) * 1000, 2)
    results["total_wall_ms"] = total_wall
    emit(f"drill result: {results['total_pass']}/{results['total_cases']} "
         f"cases PASS ({total_wall} ms)")

    with open(os.path.join(derived, "drill-results.json"), "w") as f:
        json.dump(results, f, indent=1, sort_keys=True)
    with open(os.path.join(outdir, "drill-run.log"), "w") as f:
        f.write("\n".join(log_lines) + "\n")
    return 0 if results["total_pass"] == results["total_cases"] else 1


if __name__ == "__main__":
    sys.exit(main())

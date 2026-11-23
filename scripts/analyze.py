#!/usr/bin/env python3
"""analyze.py — derive the peer-surface, eclipse-input, and manifest-limit
tables from the read-only probe outputs and the lab drill results.

Reads outputs/probe-summary.json and outputs/derived/drill-results.json
(or --outdir equivalents) and writes:
  outputs/derived/peer-surface.json
  outputs/derived/eclipse-inputs.json
  outputs/derived/manifest-limits.json
  outputs/derived/run-checks.json   (PASS/FAIL assertions, exit code)

Usage: python3 scripts/analyze.py [--outdir outputs]
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from overlay_model import (  # noqa: E402
    DEFAULT_MAX_PEERS, calc_out_peers, calc_in_peers,
    eclipse_outbound_probability, eclipse_slots_needed,
    min_ips_to_fill_inbound, quorum_after_eclipse,
    MAX_MANIFEST_BYTES, MAX_MANIFEST_BATCH_COUNT,
    MAX_MANIFEST_BATCH_BYTES, DEFAULT_MAX_UNTRUSTED_MANIFESTS,
    MAX_LEGIT_MANIFEST_BYTES, score_edge_latency_ms,
    untrusted_greeting_bytes,
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="outputs")
    args = ap.parse_args()
    derived = os.path.join(args.outdir, "derived")
    os.makedirs(derived, exist_ok=True)

    with open(os.path.join(args.outdir, "derived", "probe-summary.json")) as f:
        probe = json.load(f)
    with open(os.path.join(derived, "drill-results.json")) as f:
        drill = json.load(f)

    checks = []

    def check(name, ok, detail):
        checks.append({"check": name, "status": "PASS" if ok else "FAIL",
                       "detail": detail})
        print(f"{'PASS' if ok else 'FAIL'} {name}: {detail}")
        return ok

    # --- peer surface -------------------------------------------------------
    peers = probe.get("peers")
    out, inb = calc_out_peers(), calc_in_peers()
    peer_surface = {
        "probed_at_utc": probe.get("probed_at_utc"),
        "build_version": probe.get("build_version"),
        "network_id": probe.get("network_id"),
        "complete_ledgers": probe.get("complete_ledgers"),
        "peers_reported": peers,
        "default_max_peers": DEFAULT_MAX_PEERS,
        "peers_equal_default_cap": peers == DEFAULT_MAX_PEERS,
        "outbound_slots_at_default": out,
        "inbound_slots_at_default": inb,
        "validation_quorum": probe.get("validation_quorum"),
        "server_state": probe.get("server_state"),
        "validated_ledger_seq": probe.get("validated_ledger_seq"),
        "validated_ledger_age_seconds": probe.get("validated_ledger_age"),
        "load_factor": probe.get("load_factor"),
        "io_latency_ms": probe.get("io_latency_ms"),
        "peer_disconnects_total": probe.get("peer_disconnects"),
        "ledger_current_index": probe.get("ledger_current_index"),
        "ledger_closed_index": probe.get("ledger_closed_index"),
        "feature_entries": probe.get("feature_entries"),
        "feature_enabled": probe.get("feature_enabled"),
        "admin_rpc_refusals": {
            "peers": probe.get("peers_rpc_http_status"),
            "validators": probe.get("validators_rpc_http_status"),
            "ledger_request": probe.get("ledger_request_rpc_http_status"),
        },
        "validator_list": probe.get("validator_list"),
        "explorer": probe.get("explorer"),
        "cadence": probe.get("cadence"),
    }
    with open(os.path.join(derived, "peer-surface.json"), "w") as f:
        json.dump(peer_surface, f, indent=1, sort_keys=True)

    # --- eclipse inputs -----------------------------------------------------
    eclipse_inputs = {
        "slots": eclipse_slots_needed(),
        "min_ips_to_fill_inbound": min_ips_to_fill_inbound(inb),
        "eclipse_probability_by_pool_share": {
            str(s): eclipse_outbound_probability(s) for s in
            [0.1, 0.25, 0.5, 0.75, 0.9, 0.95]},
        "share_needed_for_p_eclipse_over_half":
            0.5 ** (1 / 10),
        "quorum_after_eclipse": {
            str(n): quorum_after_eclipse(n) for n in [1, 8, 9]},
        "score_latency_edge_ms": score_edge_latency_ms(),
    }
    with open(os.path.join(derived, "eclipse-inputs.json"), "w") as f:
        json.dump(eclipse_inputs, f, indent=1, sort_keys=True)

    # --- manifest limits ----------------------------------------------------
    manifest_limits = {
        "max_manifest_bytes": MAX_MANIFEST_BYTES,
        "max_legit_manifest_bytes": MAX_LEGIT_MANIFEST_BYTES,
        "max_manifest_batch_count": MAX_MANIFEST_BATCH_COUNT,
        "max_manifest_batch_bytes": MAX_MANIFEST_BATCH_BYTES,
        "default_max_untrusted_manifests": DEFAULT_MAX_UNTRUSTED_MANIFESTS,
        "untrusted_greeting_bytes_bound": untrusted_greeting_bytes(),
        "legacy_dump_limit_bytes": (1 << 28) - 1,
        "legacy_dump_deadline_seconds": 300,
        "batches_needed_for_1gib": -(-(1024 ** 3) // MAX_MANIFEST_BATCH_BYTES),
    }
    with open(os.path.join(derived, "manifest-limits.json"), "w") as f:
        json.dump(manifest_limits, f, indent=1, sort_keys=True)

    # --- run checks ---------------------------------------------------------
    ok = True
    ok &= check("peers-at-default-cap",
                peers == DEFAULT_MAX_PEERS,
                f"live peers={peers}, defaultMaxPeers={DEFAULT_MAX_PEERS}")
    ok &= check("quorum-17-of-25",
                probe.get("validation_quorum") == 17,
                f"validation_quorum={probe.get('validation_quorum')}")
    ok &= check("validator-list-25",
                (probe.get("validator_list") or {}).get("validators_in_blob") == 25,
                f"validators in VL blob={(probe.get('validator_list') or {}).get('validators_in_blob')}")
    ok &= check("validator-list-seq-30",
                (probe.get("validator_list") or {}).get("blob_sequence") == 30,
                f"VL blob sequence={(probe.get('validator_list') or {}).get('blob_sequence')}")
    ok &= check("admin-rpc-refused",
                probe.get("peers_rpc_http_status") == 403
                and probe.get("validators_rpc_http_status") == 403,
                f"peers={probe.get('peers_rpc_http_status')}, "
                f"validators={probe.get('validators_rpc_http_status')}")
    ok &= check("drills-all-pass",
                drill.get("total_pass") == drill.get("total_cases")
                and drill.get("total_cases") == 24,
                f"{drill.get('total_pass')}/{drill.get('total_cases')} cases pass")
    per_case = all("elapsed_ms" in c for d in drill["drills"].values()
                   for c in d["cases"])
    ok &= check("drill-per-case-timing", per_case,
                "every drill case carries elapsed_ms")
    cad = probe.get("cadence") or {}
    ok &= check("cadence-measured",
                cad.get("seconds_per_ledger") is not None
                and 2.0 < cad["seconds_per_ledger"] < 4.0,
                f"{cad.get('ledgers')} ledgers in "
                f"{cad.get('elapsed_seconds')} s = "
                f"{cad.get('seconds_per_ledger')} s/ledger")
    with open(os.path.join(derived, "run-checks.json"), "w") as f:
        json.dump({"checks": checks,
                   "all_pass": bool(ok)}, f, indent=1, sort_keys=True)
    print(f"analyze: {sum(1 for c in checks if c['status'] == 'PASS')}/"
          f"{len(checks)} checks PASS")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

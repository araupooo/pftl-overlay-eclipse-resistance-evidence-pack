#!/usr/bin/env python3
"""probe_all.py — read-only live probes of the PFTL testnet overlay surface.

Writes UNEDITED probe outputs under outputs/ (or --outdir) and a
human-readable probe-run.log. No transaction is submitted, no vote is
cast, and NO peer connection is opened to the live network: every probe
is an HTTP POST to the public JSON-RPC endpoint or an HTTP GET of a
public document. Admin-only RPC methods (peers, validators,
ledger_request) are expected to return HTTP 403 from the public proxy;
that refusal is itself a recorded measurement.

Usage: python3 scripts/probe_all.py [--outdir outputs] [--skip-cadence]
The cadence measurement takes ~60 s (two ledger_current reads).
"""

import argparse
import base64
import hashlib
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

RPC = "https://rpc.testnet.postfiat.org/"
VL_URL = "https://postfiat.org/testnet_vl.json"
EXPLORER_URLS = [
    "https://explorer.testnet.postfiat.org/",
    "https://explorer.testnet.postfiat.org/health",
    "https://explorer.postfiat.org/",
]


def utcnow():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def rpc(method, params=None):
    body = {"method": method, "params": [params] if params is not None else [{}]}
    req = urllib.request.Request(
        RPC, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, {"http_error": e.code, "body": e.read().decode(errors="replace")[:500]}
    except Exception as e:
        return None, {"error": str(e)}


def http_get(url):
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:500]
    except Exception as e:
        return None, str(e).encode()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="outputs")
    ap.add_argument("--skip-cadence", action="store_true")
    args = ap.parse_args()
    import os
    outdir = args.outdir
    os.makedirs(outdir, exist_ok=True)
    os.makedirs(os.path.join(outdir, "derived"), exist_ok=True)
    log_lines = []

    def log(msg):
        line = f"[{utcnow()}] {msg}"
        print(line)
        log_lines.append(line)

    log("probe start — read-only RPC + public GETs only; no peer connections, no transactions")
    calls = 0
    results = {}

    # --- JSON-RPC probes ----------------------------------------------------
    for method in ["server_info", "ledger_current", "ledger_closed", "fee",
                   "feature", "validators", "peers", "ledger_request"]:
        status, data = rpc(method)
        calls += 1
        results[method] = data
        fname = os.path.join(outdir, f"rpc-{method}.json")
        with open(fname, "w") as f:
            json.dump({"http_status": status, "method": method,
                       "probed_at_utc": utcnow(), "response": data},
                      f, indent=1, sort_keys=True)
        if status == 200:
            log(f"rpc {method} -> HTTP 200 (saved {fname})")
        else:
            log(f"rpc {method} -> HTTP {status} (saved {fname})")
        time.sleep(0.5)

    # --- Validator list document --------------------------------------------
    status, body = http_get(VL_URL)
    calls += 1
    vl_path = os.path.join(outdir, "testnet_vl.json")
    with open(vl_path, "wb") as f:
        f.write(body if isinstance(body, bytes) else body.encode())
    log(f"GET {VL_URL} -> HTTP {status}, {len(body)} bytes (saved {vl_path})")
    vl_info = {"http_status": status, "bytes": len(body)}
    if status == 200:
        try:
            vl = json.loads(body)
            blobs = vl.get("blobs_v2", [])
            vl_info["format"] = "v2 (blobs_v2)"
            vl_info["publisher_key"] = vl.get("public_key")
            vl_info["manifest_chars"] = len(vl.get("manifest", ""))
            if blobs:
                blob = json.loads(base64.b64decode(blobs[0]["blob"]))
                vl_info["blob_sequence"] = blob.get("sequence")
                vl_info["blob_effective"] = blob.get("effective")
                vl_info["blob_expiration"] = blob.get("expiration")
                vl_info["validators_in_blob"] = len(blob.get("validators", []))
                vl_info["blob_bytes_decoded"] = len(base64.b64decode(blobs[0]["blob"]))
                vl_info["signature_chars"] = len(blobs[0].get("signature", ""))
        except Exception as e:
            vl_info["parse_error"] = str(e)
    log(f"validator list: {json.dumps(vl_info)}")

    # --- Explorer health ------------------------------------------------------
    explorer = {}
    for url in EXPLORER_URLS:
        status, body = http_get(url)
        calls += 1
        explorer[url] = {"http_status": status, "body_head": body[:200].decode(errors="replace")}
        log(f"GET {url} -> HTTP {status}")
        time.sleep(0.5)

    # --- Cadence (60 s window) ----------------------------------------------
    cadence = None
    if not args.skip_cadence:
        _, d0 = rpc("ledger_current")
        calls += 1
        t0 = time.monotonic()
        seq0 = d0.get("result", {}).get("ledger_current_index")
        log(f"cadence t0: ledger_current_index={seq0}")
        time.sleep(60)
        _, d1 = rpc("ledger_current")
        calls += 1
        t1 = time.monotonic()
        seq1 = d1.get("result", {}).get("ledger_current_index")
        elapsed = t1 - t0
        cadence = {"start_seq": seq0, "end_seq": seq1,
                   "ledgers": (seq1 - seq0) if seq0 and seq1 else None,
                   "elapsed_seconds": round(elapsed, 1),
                   "seconds_per_ledger": round(elapsed / (seq1 - seq0), 3)
                   if seq0 and seq1 and seq1 > seq0 else None}
        log(f"cadence: {cadence}")

    # --- Derived summary ------------------------------------------------------
    si = results.get("server_info", {}).get("result", {}).get("info", {})
    summary = {
        "probed_at_utc": utcnow(),
        "rpc_calls": calls,
        "rpc_endpoint": RPC,
        "build_version": si.get("build_version"),
        "network_id": si.get("network_id"),
        "complete_ledgers": si.get("complete_ledgers"),
        "peers": si.get("peers"),
        "validation_quorum": si.get("validation_quorum"),
        "server_state": si.get("server_state"),
        "validated_ledger_seq": (si.get("validated_ledger") or {}).get("seq"),
        "validated_ledger_age": (si.get("validated_ledger") or {}).get("age"),
        "load_factor": si.get("load_factor"),
        "io_latency_ms": si.get("io_latency_ms"),
        "peer_disconnects": si.get("peer_disconnects"),
        "hostid": si.get("hostid"),
        "ledger_current_index": results.get("ledger_current", {}).get("result", {}).get("ledger_current_index"),
        "ledger_closed_index": results.get("ledger_closed", {}).get("result", {}).get("ledger_index"),
        "feature_entries": len(results.get("feature", {}).get("result", {}).get("features", {})),
        "feature_enabled": sum(1 for v in results.get("feature", {}).get("result", {}).get("features", {}).values() if v.get("enabled")),
        "validators_rpc_http_status": results.get("validators", {}).get("http_error"),
        "peers_rpc_http_status": results.get("peers", {}).get("http_error"),
        "ledger_request_rpc_http_status": results.get("ledger_request", {}).get("http_error"),
        "validator_list": vl_info,
        "explorer": explorer,
        "cadence": cadence,
    }
    with open(os.path.join(outdir, "derived", "probe-summary.json"), "w") as f:
        json.dump(summary, f, indent=1, sort_keys=True)
    log(f"probe summary written: {json.dumps(summary, sort_keys=True)}")

    # --- probe-run.log (unedited record incl. full digests) -------------------
    log("digests of probe outputs (full SHA-256):")
    for name in sorted(os.listdir(outdir)):
        p = os.path.join(outdir, name)
        if os.path.isfile(p):
            log(f"  sha256 {sha256_file(p)}  {name}")
    log(f"probe end — {calls} HTTP calls total (RPC + GETs)")
    with open(os.path.join(outdir, "probe-run.log"), "w") as f:
        f.write("\n".join(log_lines) + "\n")


if __name__ == "__main__":
    main()

# Runbook C — Manifest-Flood Handling Drill (Lab Cap Mirror)

## Purpose

Measure the manifest-flood bounds in the pinned code by mirroring the
exact inequalities the code enforces. Lab-only: the checks run against
the Python mirror in `src/overlay_model.py`, not against a live peer,
and no flood traffic is sent anywhere.

## Decision tree

```
A manifest (or a batch) arrives from a peer
├── Is the single manifest larger than 512 bytes?
│   ├── YES → rejected at decode (deserializeBoundedManifest);
│   │         the 513-byte case is the pinned test's case (C-03, C-04)
│   └── NO → accepted (C-01, C-02); largest legitimate size is 487 bytes
├── Is the batch over the count limit?
│   ├── YES → 501 manifests rejected (C-06)
│   └── NO → check the byte limit
├── Is the batch over the byte limit?
│   ├── YES → 524289 bytes rejected (C-07)
│   └── NO → accepted; 500 manifests / 256000 bytes is within both (C-05)
├── Are the manifests untrusted (unlisted keys)?
│   └── At most 1000 per message, 512000 bytes per greeting (C-08);
│       unlisted manifests are rate-limited, listed ones are not,
│       and only listed manifests persist to disk
└── Is this a legacy oversized dump from a 1.0.4 peer?
    └── Drained once per connection, at most 256 MiB - 1 bytes, 300 s
        deadline; a repeat dump or a larger one is a protocol failure (C-09)
```

## Cases (10/10 PASS, 0.06 ms)

| Case | What was measured | Result |
| --- | --- | --- |
| C-01 | Largest legitimate manifest accepted | 487-byte manifest accepted |
| C-02 | Cap-boundary manifest accepted | 512-byte manifest accepted |
| C-03 | 513-byte manifest rejected | Rejected — the `manifest_flood_test.cpp:238` case |
| C-04 | 1024-byte manifest rejected | Rejected |
| C-05 | Batch at both limits accepted | 500 manifests totalling 256000 bytes within limits |
| C-06 | Batch over count limit rejected | 501 manifests rejected (> 500) |
| C-07 | Batch over byte limit rejected | 524289 bytes rejected (> 512 KiB) |
| C-08 | Untrusted greeting payload bound | 512000 bytes (1000 manifests x 512 B) |
| C-09 | Legacy dump drain limits | Limit 268435455 bytes (256 MiB - 1), one dump per connection, 300 s deadline; 300 MiB dump rejected, 200 MiB drained once |
| C-10 | Flood-rate bound per batch | 1 GiB of manifest payload needs >= 2048 bounded batches (512 KiB each) |

Per-case elapsed times are on the PASS lines in
`outputs/drill-run.log` and as `elapsed_ms` in
`outputs/derived/drill-results.json`.

## How to run

```sh
python3 scripts/drill.py   # runs all three drills; drill C is cases C-01..C-10
```

## Interpretation

The manifest path is the most tightly bounded part of the overlay: a
single manifest cannot exceed 512 bytes, a batch cannot exceed 500
manifests or 512 KiB, untrusted manifests are capped per message and
never persisted, and the legacy oversized-dump path is a one-shot drain
with a 300-second deadline. An attacker cannot amplify one message into
unbounded work: 1 GiB of manifest payload would need at least 2048
separately bounded batches (C-10). The residual exposure is volume, not
amplification — a peer can still be made to process 512 KiB of manifest
data per message, and the legacy drain path can occupy a connection for
up to 300 seconds with a single 256 MiB dump.

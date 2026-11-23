# Runbook B — Peer-Churn and Re-Connection Drill (Lab Model)

## Purpose

Measure how fast a node refills lost peer slots under the pinned
autoconnect policy, and how failed endpoints slow recovery. Lab-only:
a timing model of `secondsPerConnect`, `maxConnectAttempts`, and the
connection-backoff ladder. No peer connection is opened and no traffic
is sent to the live network.

## Decision tree

```
Peers are lost (churn, disconnect, restart)
├── How many outbound slots are empty?
│   ├── <= 20 → one autoconnect batch refills them in 10 s (B-01, B-02)
│   └── > 20 → one extra batch per 20 slots: 21 slots take 20 s (B-06)
├── Did endpoints in the batch fail?
│   ├── NO → refill completes in the first batch
│   └── YES → failed endpoints back off (1 s first step) and retry in
│       the next 10 s batch: 21 s total for 3 failures in 10 (B-03)
├── Do endpoints keep failing?
│   └── Backoff climbs the Fibonacci ladder to 55 s per failure,
│       143 s over 10 consecutive failures (B-04)
└── Meanwhile, idle peers are swept every 4 s (B-05)
```

## Cases (6/6 PASS, 0.07 ms)

| Case | What was measured | Result |
| --- | --- | --- |
| B-01 | Lose 1 outbound peer | Refills in 10 s (one 10 s batch) |
| B-02 | Lose all 10 outbound peers | Refills in 10 s — one batch holds up to 20 attempts |
| B-03 | 3 failed endpoints in the first batch | Refill in 21 s (10 + 1 backoff + 10 retry batch) |
| B-04 | Connection backoff ladder | [1, 1, 2, 3, 5, 8, 13, 21, 34, 55] sums to 143 s over 10 failures; wait caps at 55 s |
| B-05 | Idle sweep and autoconnect cadence | Idle-peer sweep every 4 s; autoconnect batch every 10 s |
| B-06 | Attempt cap forces a second batch | Losing 21 peers needs 2 batches (20 attempts max per batch): refill in 20 s |

Per-case elapsed times are on the PASS lines in
`outputs/drill-run.log` and as `elapsed_ms` in
`outputs/derived/drill-results.json`.

## How to run

```sh
python3 scripts/drill.py   # runs all three drills; drill B is cases B-01..B-06
```

## Interpretation

Recovery is fast when the address cache holds live candidates: a full
10-slot outbound loss refills in a single 10-second batch. The
vulnerability is not the refill speed but the cache: if the cache is
full of dead endpoints, each failure costs a backoff step, and the
ladder grows fast (1, 1, 2, 3, 5, 8, 13, 21, 34, 55). After a few
consecutive failures a node can spend over two minutes retrying before
it is back to full strength. Keeping the address cache fresh — and
keeping fixed peers configured — matters more than the batch interval.

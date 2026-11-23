# Decision Memo — PFTL Peer-to-Peer Overlay and Eclipse-Resistance

## Verdict: BOUNDED BUT UNAUDITABLE FROM OUTSIDE

The overlay in pinned postfiatd 0085a1ff is soundly bounded against the
three attacks this pack examines, and the bounds are measured, not
asserted: 24/24 lab drill cases pass. But the live peer surface cannot
be audited from outside the operator, and the live node runs exactly at
its default slot cap. The verdict follows from five facts, each with its
evidence pointer.

## The five facts

1. **The flood bound is real and measured.** A manifest larger than 512
   bytes is rejected at decode time (drill C-03, the
   `manifest_flood_test.cpp:238` case); a batch is bounded at 500
   manifests and 512 KiB (C-05..C-07); untrusted manifests in a greeting
   are bounded at 1000 per message, 512000 bytes total (C-08). Source:
   `fixtures/source-excerpts/manifest-cap.txt` (ManifestMessages.h
   lines 19-40).

2. **A full eclipse is expensive, not impossible.** At default settings
   a victim holds 10 outbound and 11 inbound slots. Filling the inbound
   side needs at least 6 distinct public IPs (ipLimit 2). Winning all
   10 outbound slots by pool share alone needs a share above 0.933 for
   even odds (A-08); at 0.90 share the probability is 0.349 (A-03). A
   single fixed peer shrinks the attacker's window further, because
   fixed peers are tried first and bypass the caps (A-04).

3. **An eclipse cannot forge consensus.** Eclipsing 1 of 25 validators
   leaves 24, and quorum is 17 (A-05). Nine validators must be eclipsed
   at once before the remaining 16 fall below quorum (A-06). Eclipse is
   isolation, not forgery. The converged/diverged thresholds (24 and 128
   ledgers) bound how far an isolated node can drift before it is
   flagged diverged.

4. **Churn recovery is fast when the address cache is healthy, slow
   when it is not.** Losing all 10 outbound peers refills in a single
   10-second batch (B-02), because up to 20 attempts run at once. But
   each failed endpoint backs off along a Fibonacci ladder to 55 s, 143 s
   over 10 failures (B-04), so a poisoned cache delays recovery.

5. **The live node cannot be audited from outside.** The `peers`,
   `validators`, and `ledger_request` RPC methods are `Role::ADMIN`
   (Handler.cpp lines 136, 144, 188) and the public proxy returns HTTP
   403 for all three. The live node reports 21 peers — exactly the
   default cap — but nobody outside the operator can see who they are,
   whether any are fixed peers, or whether the address cache is diverse.
   The two questions that would settle eclipse exposure (fixed peers?
   peer diversity?) are therefore UNVERIFIED (C-29) and UNTESTABLE
   (C-30) from the public surface.

## What would change the verdict

- Publishing the peer list (or a diversity summary) for the public node
  would move F-03 from HIGH to a measured low: the audit gap is the
  largest single weakness found.
- Configuring fixed peers on the public node would close the cheapest
  eclipse path (A-04); today the public cannot tell whether any exist.
- Raising `max_peers` above the 21 default would give the node spare
  slots; today a new honest peer must wait for a disconnect (F-01).
- Nothing in the drill results would change the flood verdict: the caps
  are code-enforced and the lab mirror agrees with the pinned test.

## Scope note

This pack measures the overlay as specified in code and as visible from
the public RPC surface. It does not measure the real peer graph, the
real address cache, or real attack traffic against live peers — all three
are outside the lab-only boundary. Claims that depend on those are
marked UNVERIFIED or UNTESTABLE in `docs/claim-index.md`.

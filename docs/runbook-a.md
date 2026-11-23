# Runbook A — Eclipse-Attempt Simulation (Lab Peer-Set Model)

## Purpose

Measure what a full eclipse of one node costs under the pinned
defaults, and what it buys the attacker. Lab-only: a peer-set model
plus quorum arithmetic. No peer connection is opened and no traffic is
sent to the live network.

## Decision tree

```
Victim at default settings (21 slots: 10 out, 11 in)
├── Does the victim have fixed peers?
│   ├── YES → fixed peers are tried first and bypass the caps;
│   │         the attacker must win the REMAINING outbound slots only,
│   │         and can never displace a fixed peer (case A-04)
│   └── NO → the attacker must win all 10 outbound slots by pool share
│             (case A-03) AND fill all 11 inbound slots (case A-02)
├── Can the attacker fill the inbound side?
│   └── Needs >= 6 distinct public IPs (ipLimit 2 per IP, case A-02)
├── If fully eclipsed, can the attacker forge consensus?
│   └── NO — quorum needs 17 of 25 validations; eclipsing 1 validator
│       leaves 24 (A-05); 9 must fall at once to halt quorum (A-06)
└── Can the attacker bias ledger-fetch targeting?
    └── Only slightly: a 5 ms peer wins the fetch-pack pick in 18.2%
        of trials vs 4.76% fair share (A-07); randomness dominates
```

## Cases (8/8 PASS, 322.64 ms)

| Case | What was measured | Result |
| --- | --- | --- |
| A-01 | Default slot split | out=10, inbound=11, total=21; live node reports 21 peers = exactly the cap |
| A-02 | Distinct IPs to fill inbound | 6 (ceil(11/2) at ipLimit=2) |
| A-03 | P(all 10 outbound slots attacker-controlled) | share 0.25 -> 9.54e-07; 0.50 -> 9.77e-04; 0.90 -> 0.349 |
| A-04 | 1 fixed peer shrinks the window | attacker must win 9/9 remaining slots: P=0.387 at share 0.90 (vs 0.349 for 10/10) |
| A-05 | 1 eclipsed validator | 24/25 remain, quorum 17 still reachable |
| A-06 | Validators that must fall to halt quorum | 8 eclipsed -> 17 remain (reachable); 9 eclipsed -> 16 remain (halted) |
| A-07 | Peer-score latency edge | bonus cancels at 333.33 ms; 5 ms attacker wins the pick in 0.182 of trials (fair 0.0476) |
| A-08 | Full-eclipse cost summary | 21 slots from >=6 IPs; pool share > 0.933 needed for P(eclipse) > 0.5 |

Per-case elapsed times are on the PASS lines in
`outputs/drill-run.log` and as `elapsed_ms` in
`outputs/derived/drill-results.json`.

## How to run

```sh
python3 scripts/drill.py   # runs all three drills; drill A is cases A-01..A-08
```

## Interpretation

Eclipse is expensive because it must win two independent lotteries at
once (outbound pool share and inbound IP diversity) and because fixed
peers, where configured, are untouchable. The binding constraint is the
outbound side: at a 0.50 pool share the probability of winning all 10
outbound slots is under 0.001. But the defence is probabilistic, not
absolute: at 0.90 share the probability is 0.349 per full draw, and the
live node — at exactly 21 peers with no spare slots — cannot be checked
from outside for fixed peers or peer diversity (finding F-03). And even
a successful eclipse only isolates: it cannot manufacture the 17
validations quorum needs.

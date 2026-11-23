# Risk Register

| ID | Severity | Risk | Evidence |
| --- | --- | --- | --- |
| R-01 | HIGH | Live node at slot cap: a new honest peer cannot connect until a slot frees, and an attacker holding a slot blocks recovery | F-01; `outputs/rpc-server_info.json` (peers 21) |
| R-02 | HIGH | Eclipse at 90% address-pool share succeeds with probability 0.349 per full outbound draw on a node with no fixed peers | F-02; drill A-03 |
| R-03 | HIGH | Peer identities are unobservable from outside, so the network cannot audit whether the public node's 21 peers are diverse or Sybil-controlled | F-03; `outputs/rpc-peers.json` (HTTP 403) |
| R-04 | MEDIUM | ipLimit of 2 per IP is weak: 6 distinct public IPs fill all 11 inbound slots | F-04; PeerfinderConfig.cpp lines 46-63 |
| R-05 | MEDIUM | Fixed-peer configuration of the public node is unknown; without fixed peers, autoconnect draws from the public address cache, which an attacker can pollute | C-29; drill A-04 |
| R-06 | MEDIUM | Fetch-pack target selection is latency-biased: a 5 ms attacker wins the pick in 18.2% of trials, concentrating ledger-fetch load on the fastest peer | F-05; drill A-07 |
| R-07 | MEDIUM | A manifest batch of up to 512 KiB per message is large: a peer can be made to process half a megabyte of manifest data per message | F-06; drill C-05 |
| R-08 | MEDIUM | The legacy dump path lets one connection drain up to 256 MiB over 300 s; a 1.0.4 peer's cache dump still consumes bandwidth and time | F-06; drill C-09 |
| R-09 | MEDIUM | Churn recovery depends on the address cache: dead endpoints cost a backoff step each (up to 55 s), so a poisoned cache delays refill | F-08; drill B-04 |
| R-10 | LOW | Only protocol versions 2.1 and 2.2 are spoken; a future version split could strand 2.1 peers | F-10; ProtocolVersion.cpp lines 40-45 |
| R-11 | LOW | Squelch concentrates validation relay on a random subset per round; a squelched peer sees fewer validations that round | F-09; Slot.h lines 208-217 |
| R-12 | LOW | Send-queue disconnect (192 messages, 4 intervals) can trigger on a slow honest peer under load, not only on attackers | F-11; overlay Tuning.h lines 46-52 |
| R-13 | LOW | Converged/diverged thresholds (24/128 ledgers) let an eclipsed node drift up to 24 ledgers before it is flagged diverged | overlay Tuning.h lines 32-36 |
| R-14 | INFO | Cluster and reservation slots bypass all caps: anyone able to add a reservation bypasses the slot limits entirely | F-12; OverlayImpl.cpp lines 262-272 |

Summary: 14 risks — 3 HIGH, 6 MEDIUM, 4 LOW, 1 INFO.

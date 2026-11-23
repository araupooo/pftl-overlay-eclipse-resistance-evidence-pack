# Gap Register

| ID | Gap | Why it is open | What would close it |
| --- | --- | --- | --- |
| G-01 | Live peer identities (who the 21 peers are) | `peers` RPC is `Role::ADMIN`; the public proxy returns HTTP 403 | Operator-published peer list or diversity summary |
| G-02 | Whether the live node configures fixed peers | Not publicly observable; autoconnect order cannot be seen from outside | Operator disclosure of fixed-peer configuration |
| G-03 | Real-world eclipse probability against the live node | Testing it would require attacking the live network; outside the lab-only boundary | Lab result only (drill A); no live test is acceptable |
| G-04 | Manifest flood against a live peer | Testing it would require flooding a live peer; outside the lab-only boundary | Lab result only (drill C); no live test is acceptable |
| G-05 | Validator-list blob signature verification | Needs Ed25519, which is not in the Python standard library | A verification run with an Ed25519 implementation (e.g. libsodium) against the publisher key |
| G-06 | Peer latency distribution on the live network | Not observable via public RPC | Admin `peers` output, or a measurement node of the reviewer's own |
| G-07 | Address-cache contents of the live node | Not observable via public RPC | Operator disclosure or a local node run with the same configuration |

Summary: 7 gaps.

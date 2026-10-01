# Experiment log

## Benchmark selection

Initial experiments used a Huawei DPDP benchmark. That dataset was not retained as the primary two-stage coordination benchmark because committed completion times were soft penalties and the resulting successor sets were essentially unchanged by the first-stage decision.

Li & Lim PDPTW was then examined because hard pickup and delivery windows make future feasibility depend on first-stage choices.

## Candidate instances

LC101, LR101, and LRC101 were screened. Each contains 53 pickup-delivery requests.

## Dynamic construction

Target DoD: 0.50  
Seed: 20261001

LC101 main realization:

- \(|J|=27\)
- \(|K|=26\)
- 198 feasible transitions out of 702
- density 0.2821
- \(|U_j|\): min 0, median 6, mean 7.33, max 19

## Maximum matching

Maximum matching size in the LC101 bipartite compatibility graph: 18.

## Conflict graph

- nodes: 198
- edges: 2464
- density: 0.12634
- degree range: 16--42
- 26 distinct degree values
- one connected component

## Economic thresholds

For feasible JK chains with \(B>0\):

- n = 196
- min = 0.1193
- p10 = 0.2440
- p25 = 0.3442
- median = 0.4784
- p75 = 0.6473
- p90 = 1.1539
- max = 5.0837

## Dense optimization grid

- \(m=1,\ldots,53\)
- \(\alpha=0.1,\ldots,1.5\)

Maximum observed relative sequential loss: 80.073% at \(m=2,\alpha=0.2\).

Residual loss examples at \(m=53\):

- alpha 0.2: 41.165%
- alpha 0.3: 6.895%
- alpha 0.6: 0.631%
- alpha 1.0: 0%

## Alpha 0.2 diagnostic

At \(m=53,\alpha=0.2\):

- \(W^{joint}=165.936809\)
- \(W^{sep}=97.630\)
- gap = 68.307
- five joint JK chains have negative standalone first-stage value
- sum of optional chain gains = 68.307, matching the joint-sequential gap up to rounding

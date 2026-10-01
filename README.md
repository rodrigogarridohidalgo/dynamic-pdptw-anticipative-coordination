# Dynamic PDPTW Anticipative Coordination

Reproducibility repository for experiments on anticipative versus sequential decision making in a dynamic Pickup and Delivery Problem with Time Windows (PDPTW).

The experiments use the Li & Lim PDPTW benchmark distributed by SINTEF and construct dynamic two-stage instances by assigning release times to a subset of pickup-delivery requests.

The main experimental instance is `lc101`.

## Main research question

How much value is lost when first-stage pickup-delivery decisions are made myopically, without anticipating future requests, relative to a joint anticipative optimization?

The main performance measure is

\[
\Psi_S(m,\alpha)
=
1-\frac{W^{sep}(m,\alpha)}
        {W^{joint}(m,\alpha)}.
\]

where:

- \(m\) is fleet size;
- \(\alpha\) controls the economic value of productive transport;
- \(W^{joint}\) is the anticipative two-stage optimum;
- \(W^{sep}\) is the sequential benchmark.

## Benchmark

Source: SINTEF TOP — Li & Lim PDPTW benchmark

https://www.sintef.no/projectweb/top/pdptw/li-lim-benchmark/

Initial screening:

- `lc101.txt`
- `lr101.txt`
- `lrc101.txt`

Each contains 106 non-depot tasks, corresponding to 53 pickup-delivery requests.

## Main derived LC101 instance

Dynamic construction:

- total requests: 53
- initially known requests \(J\): 27
- future dynamic requests \(K\): 26
- target degree of dynamism: 0.50
- realized degree of dynamism: 26/53 = 0.4906
- random seed: `20261001`

For each dynamically revealed request \(r\),

\[
\rho_r^{max}=b_{p_r}-d(0,p_r).
\]

A reaction margin equal to half of the pickup time-window width is retained:

\[
\delta_r=\frac{1}{2}(b_{p_r}-a_{p_r}),
\]

and release time is generated as

\[
\rho_r\sim U\left(0,\max\{0,\rho_r^{max}-\delta_r\}\right).
\]

Static requests have \(\rho_r=0\).

## Two-stage compatibility

For the main LC101 realization:

- possible \(J\times K\) pairs: 702
- feasible \(j\rightarrow k\) transitions: 198
- transition density: 0.2821
- \(|U_j|\): min 0, median 6, mean 7.33, max 19
- initially known requests with at least one successor: 25/27
- future requests reachable from at least one \(j\): 19/26
- maximum bipartite matching size: 18

## Conflict graph

Each feasible two-stage transition \(j\rightarrow k\) is represented by one node. Two nodes conflict if they share the same first-stage request \(j\) or the same second-stage request \(k\).

For LC101:

- nodes: 198
- edges: 2464
- density: 0.12634
- degree range: 16--42
- distinct degree values: 26
- connected components: 1

## Economic model

For a single request \(r\),

\[
A_r=d(0,O_r)+d(O_r,D_r),\qquad
B_r=q_r d(O_r,D_r).
\]

For a feasible chain \(j\rightarrow k\),

\[
A_{jk}
=
d(0,O_j)+d(O_j,D_j)+d(D_j,O_k)+d(O_k,D_k),
\]

\[
B_{jk}
=
q_jd(O_j,D_j)+q_kd(O_k,D_k).
\]

Net value is \(v=\alpha B-A\).

## Experimental grid

Dense experiment:

- fleet size: \(m=1,\ldots,53\)
- \(\alpha=0.1,0.2,\ldots,1.5\)

Main outputs:

- `results/optimization/lc101_joint_vs_sequential_dense.csv`
- `results/optimization/lc101_gap_decomposition.csv`

## Main findings in the current experiment

The maximum relative sequential loss is approximately 80.1% at \(m=2,\alpha=0.2\).

For sufficiently large fleets, a residual anticipative gap remains for low and intermediate \(\alpha\):

- \(\alpha=0.2\): 41.165%
- \(\alpha=0.3\): 6.895%
- \(\alpha=0.6\): 0.631%
- \(\alpha\ge0.8\): 0% in the tested grid

At \(\alpha=0.2\), the residual gap is explained by intertemporal complementarity: requests that are unattractive individually may become profitable as the first leg of a feasible two-stage chain.

## Reproduction

Use Python 3.11:

`python -m pip install -r requirements.txt`

The original benchmark instances belong in `data/raw/`. Derived instances, optimization outputs, and figures are stored under `data/derived/` and `results/`.

## Repository structure

- `data/raw/`: original Li & Lim instances
- `data/derived/`: generated dynamic instances
- `scripts/`: experiment scripts
- `results/`: generated numerical results and figures
- `docs/`: methodological notes and experiment log

## Benchmark citation

Li, H. and Lim, A. (2001). *A Metaheuristic for the Pickup and Delivery Problem with Time Windows*. Proceedings of the 13th IEEE International Conference on Tools with Artificial Intelligence.

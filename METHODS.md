# Methods

## Request reconstruction

Each positive-demand task is interpreted as a pickup node \(O_r\); its delivery sibling identifies \(D_r\).

## Dynamic realization

Requests are partitioned into

\[
J=\{r:\rho_r=0\},\qquad K=\{r:\rho_r>0\}.
\]

For the main LC101 realization, \(|J|=27\) and \(|K|=26\).

## Request feasibility

From state \((x,t)\), pickup service starts at

\[
s_O=\max\{t+d(x,O_r),\rho_r,a_{O_r}\}.
\]

The pickup is feasible if \(s_O\le b_{O_r}\).

Delivery service starts at

\[
s_D=\max\{s_O+\ell_O+d(O_r,D_r),a_{D_r}\},
\]

and is feasible if \(s_D\le b_{D_r}\).

## Two-stage compatibility

For each \(j\in J\), serve \(j\) from the depot at \(t=0\). A future request \(k\in K\) belongs to \(U_j\) if it remains feasible from the finishing state of \(j\).

The feasible transition set is

\[
F=\{(j,k):k\in U_j\}.
\]

For the main LC101 realization, \(|F|=198\).

## Conflict graph

Each feasible transition \(p=(j,k)\in F\) becomes one node. Two chain nodes conflict if they share \(j\) or \(k\).

For LC101:

- nodes: 198
- edges: 2464
- density: 0.12634
- degree min / median / mean / max: 16 / 24 / 24.89 / 42
- distinct degree values: 26
- connected components: 1

## Economics

Single request:

\[
A_r=d(0,O_r)+d(O_r,D_r),\qquad B_r=q_rd(O_r,D_r).
\]

Chain:

\[
A_{jk}=d(0,O_j)+d(O_j,D_j)+d(D_j,O_k)+d(O_k,D_k),
\]

\[
B_{jk}=q_jd(O_j,D_j)+q_kd(O_k,D_k).
\]

Net value:

\[
v=\alpha B-A.
\]

## Joint benchmark

The joint benchmark knows both current and future requests, including future release times. It can choose \(j\)-only, \(k\)-only, and feasible \(j\rightarrow k\) alternatives, subject to request exclusivity and fleet-size limit \(m\).

Its optimum is \(W^{joint}(m,\alpha)\).

## Sequential benchmark

Stage 1 knows only \(J\) and maximizes the standalone first-stage objective. Among all first-stage optima, the implementation selects the one with the best eventual continuation, making the sequential benchmark deliberately favorable.

Its completed value is \(W^{sep}(m,\alpha)\).

## Metrics

Relative sequential loss:

\[
\Psi_S(m,\alpha)=1-\frac{W^{sep}(m,\alpha)}{W^{joint}(m,\alpha)}.
\]

Absolute gap:

\[
G(m,\alpha)=W^{joint}(m,\alpha)-W^{sep}(m,\alpha).
\]

Residual gap with a nonbinding-fleet reference:

\[
G_\infty(\alpha)=G(53,\alpha).
\]

Fleet interaction:

\[
I_F(m,\alpha)=G(m,\alpha)-G_\infty(\alpha).
\]

This is an interaction term, not a causal decomposition.

## Dense grid

- \(m=1,\ldots,53\)
- \(\alpha=0.1,0.2,\ldots,1.5\)

## Current empirical regimes

For the present LC101 dynamic realization:

- near \(\alpha=0.2\): substantial residual complementarity gap;
- approximately \(\alpha=0.3\) to \(0.7\): mixed residual-complementarity and fleet-interaction regime;
- from approximately \(\alpha=0.8\) upward: zero residual gap in the tested grid, with observed differences arising under finite fleet size.

These boundaries are instance-specific.

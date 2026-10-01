# Data

## Source

Li & Lim Pickup and Delivery Problem with Time Windows benchmark, distributed by SINTEF TOP:

https://www.sintef.no/projectweb/top/pdptw/li-lim-benchmark/

Documentation:

https://www.sintef.no/projectweb/top/pdptw/documentation/

## Raw instances used

- `lc101.txt`
- `lr101.txt`
- `lrc101.txt`

Each contains 106 non-depot tasks, corresponding to 53 pickup-delivery requests.

## Format

First row:

`NUMBER_OF_VEHICLES  VEHICLE_CAPACITY  SPEED`

Subsequent rows:

`TASK_ID X Y DEMAND EARLIEST_TIME LATEST_TIME SERVICE_TIME PICKUP_SIBLING DELIVERY_SIBLING`

Task 0 is the depot.

## Dynamic transformation

The original benchmark is static. This project creates a dynamic realization by assigning positive release times to approximately half of the pickup-delivery requests.

Main parameters:

- target DoD: 0.50
- realized DoD: 26/53 = 0.4906
- random seed: `20261001`

For pickup node \(p_r\),

\[
\rho_r^{max}=b_{p_r}-d(0,p_r)
\]

and

\[
\delta_r=\frac{1}{2}(b_{p_r}-a_{p_r}).
\]

Dynamic requests use

\[
\rho_r\sim U(0,\max\{0,\rho_r^{max}-\delta_r\}).
\]

Static requests have \(\rho_r=0\).

## Candidate-family screening

### LC101
- \(|J|=27\)
- \(|K|=26\)
- transitions: 198/702
- density: 0.2821
- \(|U_j|\): min 0, median 6, mean 7.33, max 19

### LRC101
- transitions: 51/702
- density: 0.0726
- \(|U_j|\): min 0, median 1, mean 1.89, max 18

### LR101
- transitions: 29/702
- density: 0.0413
- \(|U_j|\): min 0, median 0, mean 1.07, max 4

LC101 was selected as the main case because it provides an intermediate compatibility regime.

## Raw-data availability

The original Li & Lim benchmark files are not redistributed in this repository.

For reproducibility, `scripts/download_li_lim.sh` downloads the required instances directly from the SINTEF benchmark site and places them in `data/raw/`.

The files used are:

- `lc101.txt`
- `lr101.txt`
- `lrc101.txt`

Because `data/raw/*.txt` is excluded by `.gitignore`, locally downloaded benchmark files remain outside version control.

# Experiments

## Baseline
Run the default configuration and record:
- PDR
- mean end-to-end delay
- forwarding count
- duplicate ratio
- TTL drops
- expiry drops
- average neighbors
- channel load
- collision count
- SINR distribution
- MCS distribution

## Experiment A: density
Use 5, 10, 20, 40 vehicles.

Hypothesis:
Increasing density increases channel occupancy and interference, eventually
reducing PDR and increasing collisions.

## Experiment B: resource pool
Change resource_pool_size:
5, 10, 20, 40.

Compare:
- collision probability
- PDR
- latency

## Experiment C: CAM rate
Test:
10 Hz, 5 Hz, 2 Hz, 1 Hz.

Compare:
- channel load
- PDR
- latency

## Experiment D: Mode-2 style selection
Compare the current occupancy-aware selector with a random selector.
This becomes the first defendable algorithmic baseline.

## Experiment E: dissemination
Compare:
- forwarding OFF
- forwarding ON
- TTL 1/2/3/4

Measure multi-hop reachability and overhead.

## Experiment F: channel quality
Change:
- transmit power
- path-loss exponent
- shadowing
- interference radius

Plot PDR vs distance and SINR vs distance.

## Important
The simulator is system-level. Do not claim exact 3GPP PHY conformance.
Use 3GPP specifications for standards compliance and the cited papers for
architecture/resource-allocation justification.

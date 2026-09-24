# Experiment 001 context — causal C3 × C4 comparison

Status: **design seed for the next iteration; do not silently expand scope.**

## Scientific question

Does adding PV-inverter reactive support as the first control stage reduce BESS active-energy use and/or PV curtailment when the same distributed consensus controller is retained for BESS active-power action?

## C3 — active-power consensus baseline

```text
Q_PV = 0 (PF = 1)
if overvoltage:
    same current P_BESS consensus controller
    -> BESS charge within physical limits
    -> residual PV curtailment if needed
```

## C4 — Q first, same P consensus second

```text
if overvoltage:
    local Q_PV support within PV-inverter capability
    -> solve again at same timestamp
    if overvoltage persists:
        exact same P_BESS consensus used in C3
        -> BESS charge within same physical limits
        -> residual PV curtailment if needed
```

## Single independent variable

The presence of the **Q_PV first stage**.

Hold constant between C3 and C4:

- feeder and topology;
- PV locations and ratings;
- BESS locations and kW/kWh ratings;
- initial SOC and SOC bounds;
- efficiency assumptions;
- load and irradiance profiles;
- 24 hourly sequential snapshots;
- communication graph;
- leader definition;
- consensus equation, gains, epsilon, iteration cap, voltage threshold/tolerance;
- curtailment rule;
- result extraction.

Do not add SOC weighting, VCSF, MPC, degradation, or leaderless control to C4 unless a later experiment explicitly studies them.

## Important distinction from Kitso et al. (2025)

Kitso et al. compare leader-follower and leaderless BESS coordination in an 18-node CIGRE LV network. Their leader-follower law uses a BESS utilization factor, and their leaderless method adds SOC balancing. They do not include PV curtailment. Their paper is useful as a benchmark for coordinated BESS utilization and agent unavailability, but it is not identical to the current export-target consensus controller.

## Initial outputs for C3 × C4

Minimum metrics:

- `Vmax` and `Vmin` per hourly snapshot;
- number of violating hourly snapshots;
- PV available/generated energy;
- curtailment kWh and %;
- BESS charging energy and SOC/stored-kWh trajectories;
- `Q_PV` kvar and kvarh in C4;
- control iterations/status;
- per-BESS utilization so unequal burden is visible.

Optional later metrics: hosting capacity, Gini/Jain, losses, multi-day readiness, communication failures.

## Hypothesis form

Use a falsifiable, non-numeric hypothesis:

> Adding PV-inverter reactive support before the unchanged active-power BESS consensus reduces the active-energy burden on BESS and can postpone residual PV curtailment while maintaining voltage limits, relative to the same consensus operating with PV inverters at unit power factor.

Do not pre-commit to the result. A resistive feeder may show weak Q effectiveness; that outcome is scientifically informative.

## Before implementation

The next design iteration must explicitly fix:

1. exact C3 consensus equation from the current working script;
2. Q-control law for C4 (e.g. local Volt-VAr or proportional absorption);
3. PV inverter kVA headroom / watt-vs-var priority;
4. SOC initial/bounds and charge efficiency values;
5. whether Storage is charge-only in the 24 h first experiment;
6. exact hourly profile source and hour indexing convention;
7. output schema and run manifest.

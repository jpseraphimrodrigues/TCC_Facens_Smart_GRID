# PV + BESS physical/control model

## Current project baseline

A recurring four-unit prototype uses:

- PV units at experimental buses associated with 824, 816, 828, 830;
- PV nominal powers 1200, 600, 400, 200 kW;
- four BESS units initially assumed at 800 kW / 4000 kWh each;
- overvoltage threshold near 1.05 pu;
- leader-follower consensus acting on net-export targets;
- BESS charging first, then residual PV curtailment.

These BESS sizes are assumed experimental values, not optimized sizing.

## Curtailment definition

Canonical definition:

```text
P_curt_i(t) = max(P_PV_available_i(t) - P_PV_generated_i(t), 0)
```

Do not subtract local load from the curtailment definition. Load affects net export and voltage, but curtailment is PV energy that was available and not generated.

## Allocation rule

Given an export target:

```text
reduction_required = max(PV_available - export_target, 0)
max_by_energy = energy_room / (dt_h * eta_charge)
BESS_charge = min(reduction_required, P_charge_max, max_by_energy)
PV_curtailment_command = reduction_required - BESS_charge
```

Apply the final commands, solve electrically, and record measured PV generation and Storage power. Final curtailment should be derived from measured generation, not only from the command.

## SOC / energy state

The existing exploratory script starts Storage empty and uses ideal charge efficiency. That is a model assumption, not a universal requirement.

When the experiment adds realistic bounds/efficiency, keep them identical across compared controllers unless SOC/efficiency is the experimental variable.

Do not put SOC into consensus weights merely because it is available. Physical SOC constraints and SOC-aware consensus are different control designs.

## PV inverter vs BESS converter

Model them separately when they are separate devices:

PV inverter:

```text
P_PV^2 + Q_PV^2 <= S_PV^2
```

BESS converter:

```text
P_BESS^2 + Q_BESS^2 <= S_BESS^2
```

Do not incorrectly combine `P_BESS` and `Q_PV` under one kVA circle unless the hardware model explicitly uses a shared converter.

## Q control

When a scenario enables PV reactive support, define explicitly:

- sign convention (absorption vs injection);
- deadband/trigger;
- Volt-VAr or proportional law;
- `Qmax(t)` from the PV inverter rating and current active generation;
- whether Q acts locally or through consensus;
- whether P has watt priority or var priority.

Do not assume Q is always more effective. Low-voltage networks can be relatively resistive; effectiveness depends on feeder R/X and location. Treat the benefit of Q as an experimental hypothesis.

## BESS temporal integrity

Inside a physical hour, consensus may require many `SolveSnap()` calls. These are control iterations, not energy-integration intervals. Storage energy/SOC must be updated exactly once for that hour.

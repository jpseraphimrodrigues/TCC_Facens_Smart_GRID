# AltDSS/OpenDSS execution model

## Reference architecture

Use Python as the study engine and OpenDSS/AltDSS as the electrical solver.

Recommended separation:

- **network layer**: clear/compile feeder, validate buses/lines, voltage bases;
- **profile layer**: load and irradiance curves;
- **asset layer**: PVSystem, Storage, curves, ratings;
- **controller layer**: consensus/local/Q/curtailment logic;
- **solver layer**: SolveSnap and convergence checks;
- **measurement layer**: voltages, powers, SOC/energy, violations;
- **results layer**: raw long-format records, summaries, figures.

## IEEE 34 recurring configuration

Recurring project buses include `824`, `816`, `828`, `830`, `850`, and `832`. A four-unit BESS/PV prototype also uses auxiliary buses such as `824pv`, `816pv`, `828pv`, and `830pv`, connected through short experimental lines.

Do not assume every experiment uses all six buses or the same powers. Read the active experiment configuration.

## Manual 24-step daily simulation

The preferred daily BESS/consensus execution is sequential and Python-driven.

Pseudo-code:

```python
for step in range(24):
    solution.Hour = step_or_defined_hour
    solution.Seconds = 0

    apply_profiles_for_step(step)
    reset_step_commands()

    solve_snap()
    base = measure_state()

    while control_required(base) and iterations < max_iterations:
        commands = controller(base, state)
        apply_commands(commands)
        solve_snap()
        base = measure_state()

    record_final_state(base)
    solution.FinishTimeStep()  # exactly once
```

### Why this matters

Consensus usually requires several electrical solves at the same physical timestamp. Advancing OpenDSS time inside the controller loop would incorrectly integrate BESS energy and shift LoadShapes between control iterations.

### Use of `Mode=Daily`

It is acceptable to set:

```python
solution.Mode = SolveModes.Daily
solution.StepSize = 3600
solution.Number = 1
```

when the only purpose is allowing `Daily` LoadShapes to evaluate at the manually selected `Hour`. Do **not** use OpenDSS native multi-step Daily execution as the study loop when Python consensus must intervene inside each snapshot.

An alternative is to run pure snapshot mode and explicitly write load/PV multipliers each hour. Either approach is valid if time advancement is controlled by Python and state integration occurs once per physical step.

## Load and PV profiles

Existing experiments use 24/48/96-point curves. Utilities exist to:

- normalize curves;
- resample a 24 h profile to 48 or 96 points;
- convert step index to decimal hour;
- assign distinct LoadShapes to groups of loads;
- create shared PV irradiance and temperature shapes.

For the first new BESS experiment, retain 24 hourly snapshots unless resolution is itself being studied.

## Voltage bases and pu sanity

After creating in-memory buses/assets:

```text
Set VoltageBases=[69, 24.9, 14.376, 4.16]
CalcVoltageBases
```

Use the actual levels of the active feeder if they differ. Reject pu arrays with NaN/Inf. Treat values far above normal pu range as a voltage-base/configuration error before interpreting them physically.

## Scenario reset

Every method comparison should:

1. `Clear`;
2. compile the same base DSS;
3. recreate identical LoadShapes/assets;
4. apply the same load multiplier and profiles;
5. apply only the controller difference for that scenario.

This avoids cross-scenario state leakage from Storage, taps, controls, or modified PV properties.

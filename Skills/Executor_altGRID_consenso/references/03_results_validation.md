# Measurements, results, plots, and validation

## Canonical raw record

Prefer one row per `scenario × timestep × unit` containing at least:

- scenario / method;
- step, hour, `dt_h`;
- unit, PV name, BESS name, bus;
- `V_initial_pu`, `V_final_pu`, `V_min_pu`;
- `PV_available_kW`, `PV_generated_kW`;
- `BESS_charge_kW`, `BESS_discharge_kW`;
- `Q_PV_kvar`, `Q_BESS_kvar` when applicable;
- `export_kW`;
- `curtailment_kW`;
- `SOC_initial`, `SOC_final` or stored kWh;
- consensus iterations;
- status / infeasibility / saturation flags.

## Derived energy metrics

For each interval:

```text
E_available = P_available * dt_h
E_generated = P_generated * dt_h
E_curt = max(P_available - P_generated, 0) * dt_h
```

Daily curtailment percentage:

```text
100 * sum(E_curt) / sum(E_available)
```

For BESS:

```text
E_charge_grid = P_charge * dt_h
Delta_E_stored = eta_charge * P_charge * dt_h
```

Use the exact Storage sign convention of the active AltDSS API when extracting measured terminal powers. In the current prototype, PV generation is typically read as negative terminal active power and Storage charging as positive terminal active power; convert explicitly to the study's positive conventions.

## Voltage metrics

Collect:

- network Vmax and Vmin per step;
- monitored PV/BESS-bus voltage per step;
- maximum phase voltage per bus;
- count/list of overvoltage buses;
- count/list of undervoltage buses;
- optional phase-level violation counts.

For hourly studies, describe violation duration as **violating snapshots** or equivalent hours; do not report minute-level duration unless time resolution supports it.

## Comparison metrics already used in project work

Depending on the experiment, existing analyses include:

- curtailment per PV and total in kWh/%;
- voltage violations;
- iterations/convergence;
- PLD-weighted economic loss;
- Gini/Jain or other distribution/equity indicators;
- technical losses;
- hosting-capacity sweeps.

Do not add all metrics automatically. Select only those that answer the current hypothesis, while retaining enough raw data for later derivation.

## Recommended plots

### Single scenario

1. Vmax/Vmin across the day, with limits and iteration count.
2. Per-unit PV available/generated, BESS charge/discharge, export, curtailment.
3. SOC or stored kWh by BESS.
4. Load/PV profiles.
5. Q_PV when reactive support exists.

### Cross-scenario

1. Vmax comparison.
2. total and per-PV curtailment comparison.
3. BESS energy-use comparison.
4. SOC trajectories.
5. iterations/convergence comparison.
6. optional utilization/fairness across agents.

Save publication figures to PNG/PDF (or SVG where useful), not only interactive windows.

## Validation checklist

Before interpreting results:

- every `SolveSnap()` converged;
- the same feeder/profile/ratings/initial state were used across compared cases;
- `P_generated <= P_available`;
- `P_curt >= 0`;
- `E_available ≈ E_generated + E_curt`;
- BESS power <= rating;
- SOC/energy stays within declared bounds;
- no simultaneous charge/discharge if the model disallows it;
- time did not advance inside control iterations;
- BESS energy changed once per physical timestep;
- voltage values are valid pu;
- iteration-limit cases are clearly flagged, never reported as successful regulation.

## Output directory convention

A recommended experiment tree:

```text
Resultados/
  EXP_XXX/
    raw/
      resultados_long.csv
    tables/
      resumo_metodos.xlsx
    figures/
      01_tensao.png
      02_potencias.png
      03_soc.png
      04_curtailment.png
    metadata/
      config.yaml
      run_manifest.json
```

The raw CSV should remain the source of truth; Excel and plots are derived products.

---
name: Executor_altGRID_consenso
description: Execute, audit, compare, and extend AltDSS/OpenDSS experiments for PV, BESS, curtailment, hosting capacity, and distributed consensus control (proportional, Olfati-Saber, CORA/iCORA, leader-follower). Use for IEEE 34-bus sequential-snapshot studies, controller implementation, result extraction, plots, and reproducible experiment design. Do not use for generic power-system questions that do not require building or executing an AltDSS experiment.
---

# Executor_altGRID_consenso

Use this skill as the execution playbook for the master's experiments based on AltDSS/OpenDSS, IEEE 34-bus feeders, distributed PV, BESS, curtailment, and consensus control.

## Core rule

Protect experimental causality before writing code. Never change more control logic than the experiment requires, and never silently change network data, load/PV profiles, time resolution, leader selection, communication graph, equipment ratings, SOC assumptions, or convergence criteria between cases.

## Before modifying or running an experiment

1. Inspect the repository and identify the active `.dss`, Python entrypoint, input curves, and output directory.
2. State the current scenario and the single independent variable being changed.
3. Rebuild every compared scenario from the same network baseline (`Clear` + compile) so there is no state leakage.
4. Preserve the exact control equations already selected for the baseline unless the user explicitly asks to change them.
5. Read only the supporting references needed for the task:
   - `references/01_altdss_execution_model.md` for circuit construction and manual sequential snapshots.
   - `references/02_consensus_methods.md` for consensus implementations and distinctions.
   - `references/03_results_validation.md` for measurements, exports, plots, and validation.
   - `references/04_bess_pv_control.md` for PV/BESS physical modeling and curtailment.
   - `references/05_experiment_001_context.md` for the current C3×C4 experiment direction.

## Non-negotiable simulation invariant: manual sequential snapshots

Run a daily study as explicit sequential snapshots controlled by Python. For the initial daily experiment, use 24 steps of 1 h unless the experiment specification explicitly changes resolution.

For each step `t`:

1. Set the time explicitly (`Hour`, `Seconds`).
2. Apply the load and PV state for that step.
3. Reset step-level control commands to their intended pre-control state.
4. Run `SolveSnap()` for the uncontrolled/base state.
5. Measure voltages and available PV power.
6. If control is required, iterate controller → dispatch → `SolveSnap()` repeatedly **without advancing time**.
7. Stop on voltage criterion, physical infeasibility, or iteration limit.
8. Record measurements from the final solved electrical state, not only commanded setpoints.
9. Advance stored-energy state exactly once for the step (`FinishTimeStep()` or an explicitly equivalent external SOC update).
10. Move to the next timestamp.

Do not delegate the full day to native OpenDSS stepping (`Solve Number=24`, repeated `Solution.Solve()` advancement, etc.) when consensus must act inside each time step. `Mode=Daily` may be used only to let objects evaluate their `Daily` LoadShapes at the manually selected timestamp; Python remains responsible for advancing the 24 snapshots.

## Circuit construction policy

- Compile the base feeder first; do not overwrite the original DSS just to run an experiment.
- Add experimental connection lines, PVSystem, Storage, LoadShape, XYCurve, and control objects in memory or in a generated experiment-specific DSS include.
- Validate required buses/lines before simulation.
- Explicitly configure voltage bases and call `CalcVoltageBases` before trusting pu values.
- Keep nominal equipment ratings fixed during a run. Curtailment is a dispatch decision, not a change in nameplate rating.
- Prefer `pctPmpp` or equivalent active-power control for PV curtailment. Treat legacy code that changes `PVSystem.kVA` as a historical implementation, not the preferred physical dispatch model.

## Consensus policy

Supported families include:

- no control / local benchmark;
- consensus on absolute power;
- proportional consensus on `rho = P_applied/P_available`;
- Olfati-Saber consensus with leader voltage correction;
- CORA/iCORA with saturation-residual redistribution;
- current leader-follower PV+BESS export-target consensus;
- literature leader-follower / leaderless utilization-factor controls when explicitly selected as separate benchmarks.

Do not conflate these algorithms. Record the state variable, units, graph, leader definition, epsilon, gains, limits, and stopping rule for every case.

## Physical-control policy

Separate PV inverter and BESS converter limits unless the modeled hardware explicitly shares a converter.

- PV curtailment: `P_curt = P_PV_available - P_PV_generated`.
- BESS charging is limited by power rating, available energy room, SOC constraints, efficiency assumptions, and its own converter rating.
- Do not place SOC inside the consensus law unless that is the explicit experimental variable.
- Multiple controller iterations at the same timestamp do not represent multiple hours of battery charging.
- Never update SOC/energy once per controller iteration.

## Required outputs

At minimum, produce machine-readable results and plots sufficient to reproduce the claim:

- timestamp / step and scenario;
- per-unit PV available/generated power;
- BESS charge/discharge power and SOC/energy;
- curtailment kW, kWh, and percentage;
- export/import where relevant;
- network Vmax/Vmin and monitored-bus voltages;
- voltage violations by snapshot; optionally by bus and phase;
- consensus iterations, convergence/status, and saturation/unavailability events;
- reactive power when Q-control is enabled.

Prefer a long-format CSV as the canonical raw output. Excel comparison workbooks and matrix-style voltage/violation sheets are derived outputs. Save publication plots to files rather than relying only on interactive windows.

## Validation before accepting a run

Reject or flag the run when any of the following occurs:

- non-converged power flow;
- invalid/non-finite pu voltage or suspicious pu values (`Vmax > 2` is a strong voltage-base warning);
- applied PV power above available PV power;
- negative curtailment beyond numerical tolerance;
- BESS command outside physical limits;
- SOC/energy updated more than once per timestep;
- compared cases use different profiles, ratings, graph, initial SOC, time resolution, or stopping criteria without being declared as experimental variables;
- controller hits iteration limit without reporting the case as unresolved/infeasible.

Check energy identities such as `E_available = E_generated + E_curtailment` within tolerance. When a battery is included, separately check its stored-energy balance.

## Experimental design rule

When comparing controllers, start from the simplest causal contrast. Use ablation cases if a proposal adds more than one conceptual mechanism. Do not claim that a more complex controller is superior until the electrical results show it under identical physical assumptions.

For the current project direction, load `references/05_experiment_001_context.md` before implementing the first new experiment.

## Deliverables for implementation tasks

Return:

1. the experiment definition and what is held constant;
2. code changes, organized by network/model/controller/measurement/output layers;
3. validation checks executed;
4. generated CSV/XLSX/figures paths;
5. concise technical interpretation separating **FATO**, **INFERÊNCIA**, and **HIPÓTESE**;
6. unresolved modeling risks before treating the result as publishable.

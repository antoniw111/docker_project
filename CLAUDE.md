# docker_project — CFD detonation + Cantera validation

## What this project is
Computational-combustion coursework (PL: *metody komputerowe w spalaniu*).
Shock-tube detonation of **lean hydrogen–air** (15% mol H2, phi ≈ 0.42) simulated
in **OpenFOAM/ddtFoam**, with a thermochemical **validation layer in Cantera**.
The CFD main project is the "przejściówka"; the Cantera analysis is the add-on
required by the instructor.

Physical case: an incident shock runs down the tube toward a wedge; Mach
reflection (triple point) at the wedge apex focuses/ignites the mixture and a
detonation forms and propagates back upstream. For 15% H2 it is **marginal** —
the detonation decays before reaching the upstream probes.

## Environment (two Docker services, shared `docker_root` volume)
- `openfoam`: OpenFOAM 2.1.1 (Ubuntu 14.04 legacy) + **ddtFoam** (Ettner DDT solver).
  Base image `openfoam211` must exist locally — it is NOT built by this repo.
- `cantera`: python:3.14-slim + Cantera (3.2.0, has cp314 wheels) + SDToolbox.

Run: `./run_openfoam.sh` brings services up; exec into the relevant container.

### Known gotchas
- **Cantera 3.x dropped `.cti`** — use `.yaml` mechanisms (`gri30.yaml`, `h2o2.yaml`).
  SDToolbox 2018 demos reference `.cti`; swap them.
- `run_openfoam.sh` does not export `MY_UID`/`MY_GID`, so compose defaults to
  1000:1000. The `cantera` container runs as root and writes root-owned files
  into the shared `docker_root` — watch for permission mismatches.
- `CANTERA_DATA` in `Dockerfile.cantera` has a leading colon (empty base var).

## Analysis workflow (the Cantera add-on)
Goal: validate CFD wave speeds against detonation theory.

1. **TOA from probes** (no Cantera): read probe-pressure CSV (ParaView export),
   get incident-wave speed `W` from first-rise times (probes 2->5, +x) and
   detonation speed `D` from peak times (wedge->5->4, -x).
2. **Cantera, frozen normal shock**: from `W`, fill state (P0,T0,X) -> post-shock
   P2, T2, and **particle (gas) velocity** `u_p = W(1 - rho1/rho2)`.
3. **Cantera, CJ detonation**: equilibrium-Hugoniot minimum wave-speed method
   (validated on stoich H2-air: 1969 vs lit. 1968 m/s). RH **enthalpy form**:
   `h2 - h1 = 0.5*(P2 - P1)*(v1 + v2)` (NOT the internal-energy form — that bug
   gave ~7% low D_CJ).
4. **Compare in lab frame**: detonation runs into pre-compressed, moving gas, so
   `D_lab = D_CJ(at P2,T2) - u_p`.

Pure-Cantera implementation (no SDToolbox dependency) is in
`analysis/detonation_validation.py`.

## Validated results (case `5_725_bara_15H2_35_25_deg`, T0=293 K)
- Incident wave: W = 564 m/s, a0 = 371 m/s, M = 1.52, P2 = 2.60 bar (== CFD
  plateau ~2.5 bar, validation #1), T2 = 391 K, **u_p = 268 m/s**.
- Detonation: D_CJ(fill) = 1516 m/s; D_CJ(compressed gas) = 1524 m/s;
  **D_lab = 1256 m/s** == CFD 1194–1319 m/s, mean ~1257 (validation #2).
- CJ result is mechanism-independent (gri30 vs h2o2 <0.6%; frozen-shock part
  identical) — it rests on thermo+equilibrium, not kinetics. No need for the
  detailed H2 kinetic mech (O'Conaire) used in the CFD.

## File map
- `analysis/detonation_validation.py` — TOA + Cantera; configurable at top
  (CSV path, MECH, X, T0, P0, probe x-coords). Run in the `cantera` container.
- `analysis/p_combined_probes.csv` — probe-pressure data (ParaView export).
- `report/raport_detonacja.tex` (+ `fig_pt.pdf`, `fig_xt.pdf`) — LaTeX report.

## Conventions
- Deliverables (reports) are written in **Polish**. Code/comments may be PL or EN.
- Reports: LaTeX compiled with **pdflatex**. This setup needed
  `\usepackage[provide=*,polish]{babel}` because `polish.ldf` was missing;
  a full TeX install can use `[polish]{babel}`.
- Figures: matplotlib -> vector PDF, generated from the probe CSV (avoid raw
  ParaView screenshots in reports).
- Engineering numerics: Python + CSV + LaTeX. Keep notation Polish-convention.

## Open items / TODO
- Fill temperature now set to T0=293 K (script + report). Ideally still
  cross-check against the CFD `0/T` initial field — affects all derived qty.
- Process remaining runs (other H2 %, inflow speeds) and find the
  detonable/non-detonable boundary (D_CJ, induction length, cell size vs % H2).
- Optional: cross-check D_CJ against SDToolbox `CJspeed` (using `.yaml`).

# Seasonal Thermal Energy Storage for load shifting
This repository contains the code written as part of my master thesis
about the load shifting potential of seasonal thermal energy storage.

The main code is in
 - `modelbuilder.py` defining parameter values and building the model, using
   - `params.py` helper for assigning parameters 
   - `variables.py` defining all variables
   - `constraints.py` defining all constraints
   - `objective_function.py` defining the objective function
   - `solution_writer.py` aggregates the variables from the model's minimum into csv files.

By passing parameters to `modelbuilder.py`, the model uses different parameters for tariffs, 
uses different electricity price profiles, and enables different investment opportunities.
To run all cases, see `all_cases.ps1`.

The results are written to subfolders of `Results/`, and include the net hourly power import,
and usage of the STES if available.

## Power flow
In `Power_flow/`, there is code for inserting the resulting load profiles into the CINELDI reference MV grid,
and running power flow analysis.

## Plotting
The `Plotting/` folder contains several files used to visualize
the results of the optimization model and the power flow.

## Other folders
The rest of the folders contain data used by the model, and any python scripts used to preprocess the data.
 - `Lastprofiler` contains the data from Hofmann et al., 2023, "Norwegian hourly residential electricity demand data with consumer characteristics during the European energy crisis".
 - `PV_profiler` contains a PV production profile generated from Renewables.ninja
 - `Temperaturprofiler` contains the hourly outside temperature at Blindern, Oslo, in 2021, from the frost API.
 - `PROFet` contains an hourly estimate of the ratio between electric and thermal demand in houses and apartments in Oslo, 2021, created by passing the outside temperature to the PROFet tool.
 - `Historic_spot_prices` contains actual spot price profiles from the NO1 price zone
 - `Framtidspriser` contains NVE's estimates for electricity prices in 2030, and code to turn them into hourly price profiles.
 - `CINELDI_MV_reference_system` contains CINELDI's reference MV grid, with hourly load profiles.
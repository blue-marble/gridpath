### 1. Create working directory
Create a directory to use and navigate to the directory. We'll use the 
following name for our base directory:
ra_toolkit_test

### 2. Put the base CSVs in this directory
(Shared as ra_toolkit_csvs_empty)
ra_toolkit_test/ra_toolkit_csvs

### 3. Ensure ra_toolkit_settings file is in the base directory

### 4. (OK to skip) Ensure temporal_scenarios.csv settings are correct (Ana to move this to settings)

### 5. Run RA toolkit

From the base directory run:
gridpath_run_ra_toolkit


### 6. Load the CSVs into the database
gridpath_load_csvs --database ./ra_toolkit.db --csv_location ./ra_toolkit_csvs

### 7. Load the scenarios
gridpath_load_scenarios --database ./ra_toolkit.db --csv_path ./ra_toolkit_csvs/scenarios.csv

### 8. Run cases
gridpath_run_e2e --log --database ./ra_toolkit.db --scenario_location ./Simulations --results_export_rule USE --n_parallel_get_inputs 24 --n_parallel_solve 24 --scenario monte_carlo_2

gridpath_run_e2e --log --database ./ra_toolkit.db --scenario_location .
/Simulations --results_export_rule USE --n_parallel_get_inputs 24 
--n_parallel_solve 24 --scenario sync

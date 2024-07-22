## GridPath RA Toolkit How-To

The GridPath RA Toolkit generates GridPath input CSV files for use in
resource adequacy studies, including weather-dependent load profiles as well as 
wind and solar profiles, generator availabilities, and hydro conditions.

This assumes you have GridPath installed into a Python environment and the 
environment activated. You can install with:

```bash
pip install GridPath
```

To use the RA Toolkit, follow these steps:

## 1. Create working directory
Create a directory to use and navigate to the directory. We'll use the 
following name for our base directory: *ra_toolkit_example*

## 2. Put the base CSVs in this directory
The csvs will be in: *ra_toolkit_example/ra_toolkit_csvs*.

## 3. Ensure ra_toolkit_settings file is in the base directory

You can find sample settings in the 
*db/utilities/ra_toolkit/ra_toolkit_settings_sample.csv*  file.

## 4. Ensure temporal_scenarios.csv settings are correct

## 5. Run RA toolkit

From the base directory run:
gridpath_run_ra_toolkit

## 6. Load the CSVs into the database
gridpath_load_csvs --database ./ra_toolkit.db --csv_location ./ra_toolkit_csvs

## 7. Load the scenarios
gridpath_load_scenarios --database ./ra_toolkit.db --csv_path ./ra_toolkit_csvs/scenarios.csv

## 8. Run cases
gridpath_run_e2e --log --database ./ra_toolkit.db --scenario_location ./Simulations --results_export_rule USE --n_parallel_get_inputs 24 --n_parallel_solve 24 --scenario monte_carlo_2

gridpath_run_e2e --log --database ./ra_toolkit.db --scenario_location ./Simulations --results_export_rule USE --n_parallel_get_inputs 24 --n_parallel_solve 24 --scenario sync


## GridPath RA Toolkit Modules

### Create the Database

Run the *db/create_database.py* script to create an empty GridPath database.

### Load Raw Data

Use the *load_raw_data.py* script to load raw 
data inputs including:
   * Weather: load, wind, and solar profiles, and thermal derates
   * Weather: day bins for the historical record
   * Hydro: year-month data
   * Availability: unit outage characteristics

### Weather Iterations

#### Sync Mode

Create the GridPath CSVs for load and variable generator profiles with
*create_sync_load_input_csvs.py* and *create_sync_var_gen_input_csvs.py*.

#### Monte Carlo Mode

1. Run *create_monte_carlo_draws.py* to create the weather
   draws and to create the synthetic weather iteration data for those draws. 
2. Create input CSVs for GridPath for load and variable gen. Use 
*create_monte_carlo_load_input_csvs.py* and 
   *create_monte_carlo_var_gen_input_csvs.py*.


### Hydro Iterations
Run *create_hydro_iteration_inputs.py* to create hydro iteration inputs from 
year-month inputs.

### Availability Iterations

Run *create_availability_iteration_inputs.py* to create 
weather-independent availability inputs from outage probability inputs. Use 
*create_monte_carlo_gen_weather_derate_input_csvs.py* and 
*create_sync_gen_weather_derate_input_csvs.py* to create weather-dependent 
derates.

### Temporal Scenarios

Run *create_temporal_scenarios.py* to create GridPath temporal scenario IDs 
using the RA Toolkit data.

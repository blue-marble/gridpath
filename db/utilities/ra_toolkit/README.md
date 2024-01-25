# GridPath RA Toolkit How-To

The GridPath RA Toolkit generates GridPath input CSV files for use in
resource adequacy studies, including weather-dependent load profiles as well as 
wind and solar profiles, generator availabilities, and hydro conditions. To run the GridPath RA Toolkit, use the**run_ra_toolkit.py** script in this directory. The settings for the script are provided via the wrapper_settings.csv file. To understand what the Toolkit does or run individual steps from it, continue reading below. 

# GridPath RA Toolkit Modules

## Create the Database

Run the **db/create_database.py** script to create an empty GridPath database.

## Load Raw Data

Use the **db/utilities/ra_toolkit/load_raw_data.py** script to load raw 
data inputs including:
   * Weather: hourly load and renewable profiles
   * Weather: day bins for the historical record
   * Hydro: year-month data
   * 

## Weather Iterations

### Sync Mode
Create the GridPath CSVs for load and variable generator profiles:
* create_sync_load_input_csvs.py
* create_sync_var_gen_input_csvs.py

### MC Mode

1. Run *create_monte_carlo_draws.py" to create the 
   draws and to create the synthetic weather iteration data for those draws. 
2. Create input CSVs for GridPath for load and variable gen:
   * For Sync, use *create_sync_load_input_csvs.py* and 
     *create_sync_var_gen_input_csvs.py*
   * For Monte Carlo, use *create_monte_carlo_load_input_csvs.py* and 
     *create_monte_carlo_var_gen_input_csvs.py*


## Hydro Iterations
Run *create_hydro_iteration_inputs.py* -- create hydro iteration inputs 
   for a particular temporal scenario ID from year-month inputs

## Outage Iterations

Run *create_availability_iteration_inputs.py* -- create availability inputs 
   for a particular temporal scenario ID from outage probability inputs

## Temporal Scenarios

Run *create_temporal_scenarios.py*

## GridPath RA Toolkit

The GridPath RA Toolkit generates GridPath input CSV files for use in
resource adequacy studies, including weather-dependent load profiles as well as 
wind and solar profiles, generator availabilities, and hydro conditions. To run 
the GridPath RA Toolkit, use the *run_ra_toolkit.py* script in this 
directory. The settings for the script are provided via the 
ra_toolkit_settings_sample.csv file. To understand what the Toolkit does or run 
individual steps from it, continue reading below. 

## GridPath RA Toolkit Modules

### Create the Database

Run the *gridpath_run_ra_toolkit -step create_database* to create an empty GridPath database.

### Load Raw Data

Use the *gridpath_run_ra_toolkit -step load_raw_data* to load raw 
data inputs including:
   * Weather: load, wind, and solar profiles, and thermal derates
   * Weather: day bins for the historical record
   * Hydro: year-month data
   * Availability: unit outage characteristics

### Weather Iterations

#### Sync Mode

Create the GridPath CSVs for load and variable generator profiles with
*gridpath_run_ra_toolkit -step create_sync_load_input_csvs* and *gridpath_run_ra_toolkit -step create_sync_var_gen_input_csvs*.

#### Monte Carlo Mode

1. Run *gridpath_run_ra_toolkit -step create_monte_carlo_draws* to create the weather draws and to create the synthetic weather iteration data for those draws. 
2. Create input CSVs for GridPath for load and variable gen. Use 
*gridpath_run_ra_toolkit -step create_monte_carlo_load_input_csvs* and 
   *gridpath_run_ra_toolkit -step create_monte_carlo_var_gen_input_csvs*.


### Hydro Iterations
Run *gridpath_run_ra_toolkit -step create_hydro_iteration_inputs* to create hydro iteration inputs from year-month inputs.

### Availability Iterations

Run *gridpath_run_ra_toolkit -step create_availability_iteration_inputs* to create 
weather-independent availability inputs from outage probability inputs. Use 
*gridpath_run_ra_toolkit -step 
create_monte_carlo_gen_weather_derate_input_csvs* and *gridpath_run_ra_toolkit -step create_sync_gen_weather_derate_input_csvs* to create weather-dependent 
derates.

### Temporal Scenarios

Run *gridpath_run_ra_toolkit -step create_temporal_scenarios* to create GridPath temporal scenario IDs using the RA Toolkit data.

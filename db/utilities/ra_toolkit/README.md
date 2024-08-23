## GridPath RA Toolkit How-To

The GridPath RA Toolkit generates GridPath input CSV files for use in
resource adequacy studies, including weather-dependent load profiles as well as 
wind and solar profiles, generator availabilities, and hydro conditions. To run 
the GridPath RA Toolkit, use the *run_ra_toolkit.py* script in this 
directory. The settings for the script are provided via the 
ra_toolkit_settings_sample.csv file. To understand what the Toolkit does or run 
individual steps from it, continue reading below. 

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

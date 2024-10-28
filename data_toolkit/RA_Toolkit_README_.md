## GridPath RA Toolkit

The GridPath RA Toolkit generates GridPath input CSV files for use in
resource adequacy studies, including weather-dependent load profiles as well as 
wind and solar profiles, generator availabilities, and hydro conditions. To run 
the GridPath RA Toolkit, use the *gridpath_run_ra_toolkit* command. See the 
help menu for usage with *--help*. Sample settings for the command are provided 
via the ra_toolkit_settings_sample.csv file in *db/utilities/ra_toolkit*. To 
understand what the Toolkit does or run individual steps from it, continue 
reading below. 

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

### 1. Create working directory
Create a directory to use and navigate to the directory. We'll use the 
following name for our base directory: *ra_toolkit_base*

### 2. Put the base CSVs in this directory
The csvs will be in: *ra_toolkit_base/csvs_test_examples*. You can download the 
CSVs from *db/csvs_test_examples* for use in this step. The raw data used by 
the RA toolkit is in *db/csvs_test_examples/raw_data_ra_toolkit* and other 
inputs are also used to create the RA scenarios below.

### 3. Create your ra_toolkit_settings file is in the base directory
You can find sample settings in the 
*db/utilities/ra_toolkit/ra_toolkit_settings_sample.csv*  file.

### 3. Run RA toolkit

From the working directory run:
gridpath_run_ra_toolkit --settings_csv PATH_TO_YOUR_SETTINGS_CSV

**Example:**
```bash
gridpath_run_ra_toolkit --settings_csv ../utilities/ra_toolkit/ra_toolkit_settings_sample.csv
```

### 4. Load the CSVs into the database
Load the input CSVs into the database with:
*gridpath_load_csvs --database PATH_TO_YOUR_DB --csv_location PATH_TO_YOUR_INPUT_CSVS*

**Example:**
```bash
gridpath_load_csvs --database ./ra_toolkit.db --csv_location ./csvs_test_examples
```

### 5. Load the scenarios
Load the scenarios into the database with *gridpath_load_scenarios --database PATH_TO_YOUR_DB --csv_path PATH_TO_YOUR_SCENARIO_CSV*

**Example:**
```bash
gridpath_load_scenarios --database ./ra_toolkit.db --csv_path ./csvs_test_examples/scenarios.csv
```

### 6. Run cases
Run the RA example cases.

**Examples:**
```bash
gridpath_run_e2e --log --database ./ra_toolkit.db --scenario_location ./Simulations --results_export_rule USE --n_parallel_get_inputs 2 --n_parallel_solve 2 --scenario ra_toolkit_monte_carlo
```
```bash
gridpath_run_e2e --log --database ./ra_toolkit.db --scenario_location ./Simulations --results_export_rule USE --n_parallel_get_inputs 2 --n_parallel_solve 2 --scenario ra_toolkit_sync
```

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
Run *gridpath_run_ra_toolkit -step create_hydro_iteration_input_csvs* to create hydro iteration inputs from year-month inputs.

### Availability Iterations

Run *gridpath_run_ra_toolkit -step create_availability_iteration_input_csvs* to create 
weather-independent availability inputs from outage probability inputs. Use 
*gridpath_run_ra_toolkit -step 
create_monte_carlo_gen_weather_derate_input_csvs* and *gridpath_run_ra_toolkit -step create_sync_gen_weather_derate_input_csvs* to create weather-dependent 
derates.

### Temporal Scenarios

Run *gridpath_run_ra_toolkit -step create_temporal_scenarios* to create GridPath temporal scenario IDs using the RA Toolkit data.

## GridPath Data Toolkit Demo

These are instructions for creating a bare-bones production cost model (PCM) 
for the 2026 WECC system with the GridPath Data Toolkit.

**Important Note**:
These instructions are just to demo the Toolkit functionality. This will *not* 
create a fully usable, production-ready PCM, as multiple data gaps would 
need tobe filled and some of the datasets would require substantial additional 
cleaning and validation for full usability.

## Install GridPath

The instructions here assume you have GridPath installed into a Python 
environment and the environment activated. You can install with:

```bash
pip install GridPath
```

See the GridPath documentation for installation instructions.

## Create working directory

```
mkdir gridpath_open_data_demo
cd gridpath_open_data_demo
```

## Get demo user-defined inputs first

The first step is to download user-defined demo inputs for the PCM model. The 
user-defined inputs include mappings between raw data columns and GridPath 
parameters (e.g., telling GridPath to model combined cycle gas turbines as 
the gen_commit_lin operational type) as well as some generic data to fill data gaps (e.g., a generic heat curve since unit-level data are not currently available). Users can change these definitions by modifying the various 'user_defined' input files.

```bash
gridpath_get_pcm_demo_inputs
```

## Download data from PUDL

Next, we download the data from PUDL. This will download the *pudl.sqlite* 
database as well as the RA Toolkit wind and solar profiles Parquet file, and 
the EIA930 hourly interchange data Parquet file. See *--help* menu for 
options. Data are to *./pudl_download* by default. Note these are relatively 
large files and the download process may take a few minutes depending on 
your internet speed.

```bash
gridpath_get_pudl_data
```

## Get subset of raw data for GridPath from downloaded PUDL data

Once we have downloaded the full PUDL database, we will get a subset of the 
data that the GridPath Data Toolkit currently uses and convert it to 
GridPath raw data format.

This will create the following files in the user-specified raw data directory:
* pudl_eia860_generators.csv
* pudl_eia930_hourly_interchange.csv
* pudl_eiaaeo_fuel_prices.csv
* pudl_ra_toolkit_var_profiles.csv

```bash
gridpath_pudl_to_gridpath_raw
```


## Get other GridPath RA Toolkit data not yet on PUDL

We'll fill some missing data, namely load forecast data and hydro data, with 
data from the GridPath RA Toolkit. Note that this is the same dataset as what 
is on the GridLab RA Toolkit website but with a modified data structure and 
it is currently stored on Blue Marble's Google Drive.
* ra_toolkit_load.csv
* ra_toolkit_hydro.csv

```bash
gridpath_get_ra_toolkit_data_raw

```

## Processing the data with the Open Data Toolkit
This currently assumes we are running from the data_toolkit directory.

```bash
gridpath_run_data_toolkit --settings_csv ./raw_data/open_data_toolkit_settings_sample.csv
```

## Load processed input data into GridPath IO database as usual
This currently assumes we are running from the db directory

```bash
gridpath_create_database --database ./gridpath_data_toolkit_demo.db
```

## Load the input CSVs created with the GridPath Data Toolkit into a GridPath database

### Move the *csv_structure.csv* and *scenarios.csv* file to the *demo_csvs* directory to tell GridPath what to load
```bash
mv ./raw_data/csv_structure.csv ./demo_csvs
mv ./raw_data/scenarios.csv ./demo_csvs
```

### Load the inputs
```bash
gridpath_load_csvs --database ./gridpath_data_toolkit_demo.db --csv_location ./demo_csvs
```

### Load the scenario definitions
```bash
gridpath_load_scenarios --database ./gridpath_data_toolkit_demo.db --csv_path ./demo_csvs/scenarios.csv
```

## Run the demo WECC 2026 PCM case
```bash
gridpath_run_e2e --database ./gridpath_data_toolkit_demo.db --log --n_parallel_get_inputs 48 --n_parallel_solve 48 --scenario_location ./scenarios --scenario test_w_tx_days
```

## View some results

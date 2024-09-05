## Download data from PUDL

```bash
gridpath_get_pudl_data
```
Downloads data to *./pudl_download* by default.
This will download the *pudl.sqlite* database as well as the RA Toolkit 
wind and solar profiles Parquet file, and the EIA930 hourly interchange 
data Parquet file. See *--help* menu for options.

## Get subset of raw data for GridPath from downloaded PUDL data

```bash
gridpath_pudl_to_gridpath_raw
```
Gets subset of the downloaded PUDL data and converts it to GridPath raw data 
format.
This will create the following files in the user-specified raw data directory:
* pudl_eia860_generators.csv
* pudl_eia930_hourly_interchange.csv
* pudl_eiaaeo_fuel_prices.csv
* pudl_ra_toolkit_var_profiles.csv

## Get other GridPath RA Toolkit data not yet on PUDL

```bash
gridpath_get_ra_toolkit_data_raw
```
Also get the load data and hydro data from the GridPath RA Toolkit dataset. 
Note that this is the same dataset but in a changed format from what is on the 
GridLab RA Toolkit website and is currently stored on Blue Marble's Google Drive .
* ra_toolkit_load.csv
* ra_toolkit_hydro.csv


## Processing the data with the Open Data Toolkit

```bash
gridpath_run_data_toolkit
```

## Load processed input data into GridPath IO database as usual

```bash
gridpath_create_database --database ./open_data_raw.db
```

```bash
gridpath_load_csvs --database ./open_data.db --csv_location ./csvs_open_data
```

```bash
gridpath_load_scenarios --database ./open_data.db --csv_path ./csvs_open_data/scenarios.csv
```

```bash
gridpath_run_e2e --database ./db/open_data.db --log --n_parallel_get_inputs 24 --n_parallel_solve 24 --scenario_location ./scenarios --scenario test_w_tx_days
```

## Get raw data from PUDL

```bash
gridpath_get_pudl_data
```
Downloads data to *./pudl_download* by default.
This will download the *pudl.sqlite* database as well as the RA Toolkit 
wind and solar profiles Parquet file, and the EIA930 hourly interchange 
data Parquet file. See *--help* menu for options.

## Get raw data for GridPath from PUDL

```bash
gridpath_pudl_to_gridpath_raw
```
Gets subset of the downloaded PUDL data and converts it to GridPath raw data 
format.
This will create the following files in the user-specified raw data directory:
* eia860_generators.csv
* eia930_hourly_interchange.csv
* eiaaeo_fuel_prices.csv
* var_profiles.csv

## Processing the data with the Open Data Toolkit

python run_open_data_toolkit.py

gridpath_create_database --database ./open_data.db

gridpath_load_csvs --database ./open_data.db --csv_location ./csvs_open_data

gridpath_load_scenarios --database ./open_data.db --csv_path ./csvs_open_data/scenarios.csv

gridpath_run_e2e --database ./db/open_data.db --log --n_parallel_get_inputs 24 --n_parallel_solve 24 --scenario_location ./scenarios --scenario test_w_tx_days

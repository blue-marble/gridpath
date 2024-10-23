## Processing the data with the Open Data Toolkit

```bash
gridpath_run_data_toolkit
```

## Load processed input data into GridPath IO database as usual

```bash
gridpath_create_database --database ./open_data.db
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

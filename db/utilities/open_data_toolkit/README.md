
python run_open_data_toolkit.py

gridpath_load_csvs --database ./open_data.db --csv_location ./csvs_open_data

gridpath_load_scenarios --database ./open_data.db --csv_path ./csvs_open_data/scenarios.csv

gridpath_run_e2e --database ./db/open_data.db --log --n_parallel_get_inputs 24 --n_parallel_solve 24 --scenario_location ./examples --scenario test

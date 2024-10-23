#####################
GridPath Data Toolkit
#####################

.. automodule:: data_toolkit

Obtaining Raw Data
##################

****
PUDL
****
.. automodule:: data_toolkit.raw_data.pudl

Download Datasets
*****************
.. automodule:: data_toolkit.raw_data.pudl.download_data_from_pudl

Convert to GridPath Raw Format
******************************
.. automodule:: data_toolkit.raw_data.pudl.pudl_to_gridpath_raw_data

*******************
GridPath RA Toolkit
*******************
.. automodule:: data_toolkit.raw_data.ra_toolkit
.. automodule:: data_toolkit.raw_data.ra_toolkit.get_ra_toolkit_data


Using the GridPath Data Toolkit
###############################

The various functionalities available in the GridPath Data Toolkit can be
accessed via the ``gridpath_run_data_toolkit`` command. See the ``--help``
menu for the available individual Toolkit steps. You may run individual steps
only or list the steps you want to run with their respective arguments in a
settings file you can point to with the ``--settings_csv`` argument.
Descriptions of the individual steps available in the Toolkit are below.

******************************
Building the Raw Data Database
******************************

The first step in using the GridPath Data Toolkit is to create a raw data
database. You may do so with the following command:

>>> gridpath_run_data_toolkit --single_step create_database --database PATH/TO/RAW/DB --db_schema ./raw_data_db_schema.sql --omit_data


****************
Loading Raw Data
****************

.. automodule:: data_toolkit.load_raw_data


****************
Load Zone Inputs
****************

.. automodule:: data_toolkit.system.eia930_load_zone_input_csvs

***************
Temporal Inputs
***************

.. automodule:: data_toolkit.temporal.create_monte_carlo_weather_draws

***********
Load Inputs
***********

.. automodule:: data_toolkit.system.create_sync_load_input_csvs
.. automodule:: data_toolkit.system.create_sync_load_input_csvs.create_load_profile_csv
.. automodule:: data_toolkit.system.create_monte_carlo_load_input_csvs
.. automodule:: data_toolkit.system.create_monte_carlo_load_input_csvs.create_load_profile_csv

**************
Project Inputs
**************

.. automodule:: data_toolkit.project.portfolios.eia860_to_project_portfolio_input_csvs
.. automodule:: data_toolkit.project.load_zones.eia860_to_project_load_zone_input_csvs
.. automodule:: data_toolkit.project.capacity_specified.eia860_to_project_specified_capacity_input_csvs
.. automodule:: data_toolkit.project.fixed_cost.eia860_to_project_fixed_cost_input_csvs
.. automodule:: data_toolkit.project.opchar.eia860_to_project_opchar_input_csvs

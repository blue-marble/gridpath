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

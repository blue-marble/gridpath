**************
Using GridPath
**************


Running GridPath from the Command Line
======================================

The gridpath_run and gridpath_run_e2e commands
----------------------------------------------

If you install GridPath via the setup script following the instructions above,
you can use the command :code:`gridpath_run` to run a scenario from any
directory -- as long as your GridPath Python environment is enabled and the
scenario folder contains the appropriate .tab files -- as
follows::

    gridpath_run --scenario SCENARIO_NAME --scenario_location /PATH/TO/SCENARIO

If you are using the database, you can use the command :code:`gridpath_run_e2e`
to run GridPath end-to-end, i.e. get inputs for the scenario from the database,
solve the scenario problem, import the results into the database, and
process them::

    gridpath_run_e2e --scenario SCENARIO_NAME --scenario_location /PATH/TO/SCENARIO

To see usage and other optional arguments, e.g. how to specify a
solver, check the help menu, e.g.::

    gridpath_run --help


Examples
========
To run any of the problems in the *examples* directory, you also need
to specify a scenario location (as these are not in the default
*scenarios* subdirectory). For example, to run the *test* scenario in
the *examples* directory, run the following::

    python run_scenario.py --scenario test --scenario_location ../examples


Workflow
========

.. image:: ../graphics/gridpath_workflow.png

GridPath requires a large amount of data on a range of electricity system
aspects such as zonal and transmission topography, load profiles, generator
capacities and operating characteristics, renewable profiles, hydropower
operations, reserve requirements, reliability policies, environmental
policies, etc. Data is managed via an SQLite database. GridPath includes
utilities to assist the user with importing raw data into the correct
database tables and data format.

With the database built, the user can then create scenarios by selecting
subsets of the data (e.g. selecting a particular load profile or a different
portoflio of generators). In GridPath's database, these subsets of data are
called subscenarios. A scenario generally consists of a list of
subscenarios and GridPath includes utilities to select the correct data for
each scenario. The user also selects desired features, which tells GridPath
which database tables to look at.

Currently, scenario input files are written to disk in TAB files. These are
similar to CSVs, but use tabs instead of commas to delimit values. In the
future, we may support other file formats, including CSVs. We may also skip
the writing of files altogether, although keeping an additional record of what
goes into a scenario is often useful.

The next step is for the Python model (consisting of various modules that
create the model formulation) to read in the TAB-delimited input files and
create the optimization problem. The compiled model file is then sent to the
solver. GridPath is solver-agnostic and supports a wide range of solvers.

Once the solver finishes solving, it returns the results to GridPath.
GridPath's modules then write CSV results files to disk. The user can select
to manually or automatically import these results into the database.

Finally, GridPath includes functionality to process the results and creates
various visualizations.

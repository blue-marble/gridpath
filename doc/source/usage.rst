**************
Using GridPath
**************

Workflow
========

.. image:: ../graphics/gridpath_workflow.png

GridPath input and scenario data are managed via an SQLite database. GridPath
includes utilities to assist the user with importing raw data into the correct
database tables and data format. With the inputs loaded, the user can then
create scenarios by selecting subsets of the data (e.g. selecting a
particular load profile or a different portoflio of generators). In
GridPath's database, these subsets of data are called subscenarios. A
scenario generally consists of a list of subscenarios and GridPath includes
utilities to select the correct data for each scenario. The user also selects
desired features, which tells GridPath which database tables to look at.

See the :ref:`building-the-database-section-ref` section for more details on
how to set up and load inputs into the database, and create scenarios.

Scenario input files are written to disk in TAB files. The next step is for
the Python model (consisting of various modules that create the model
formulation) to read in the TAB-delimited input files and
create the optimization problem. The compiled model file is then sent to the
solver. GridPath is solver-agnostic and supports a wide range of solvers.

See the :ref:`running-gridpath-scenarios-section-ref` section below for how
to run a GridPath scenario.

Once the solver finds a solution, it returns the results to GridPath.
GridPath's modules then write CSV results files to disk. The user can select
to manually or automatically import these results into the database.

Finally, GridPath includes functionality to process the results and creates
various visualizations. See the :ref:`visualization-section-ref` section for
more details.


.. _running-gridpath-scenarios-section-ref:

Running GridPath Scenarios
==========================

The gridpath_run_e2e and gridpath_run commands
----------------------------------------------

Once you have loaded inputs into the database and created a scenario,
you can use the command :code:`gridpath_run_e2e` to run a scenario from any
directory -- as long as your GridPath Python environment is enabled -- as
follows::

    gridpath_run_e2e --database /PATH/TO/DATABASE --scenario SCENARIO_NAME
    --scenario_location /PATH/TO/SCENARIO

The above command runs GridPath end-to-end, i.e. gets inputs for the scenario
from the database, solves the scenario problem, imports the results into the
database, and processes them.

If you are not using the database (not recommended), you can use
the command :code:`gridpath_run` to point to a scenario for which input .tab files have
already been written::

    gridpath_run --scenario SCENARIO_NAME --scenario_location /PATH/TO/SCENARIO

To see usage and other optional arguments, e.g. how to specify a
solver, check the help menu, e.g.::

    gridpath_run_e2e --help

Running several scenarios in parallel
-------------------------------------

To run a set of scenarios against one database, solving several at a time,
use :code:`gridpath_run_e2e_parallel`::

    gridpath_run_e2e_parallel --database /PATH/TO/DATABASE
    --scenario_location /PATH/TO/SCENARIOS --scenarios SCENARIO_1 SCENARIO_2
    SCENARIO_3 --n_parallel_scenarios 2

Up to :code:`--n_parallel_scenarios` scenarios get their inputs and are
solved at once, each in its own process; their results are imported into
the database one scenario at a time, as each finishes solving, since the
SQLite database can only have one writer at a time. Every other argument is a
:code:`gridpath_run_e2e` argument applied to every scenario (e.g.
:code:`--log`, :code:`--quiet`, :code:`--n_parallel_solve`). Options that
differ by scenario can be given in a CSV passed with :code:`--scenarios_csv`
(scenario names across the top row after :code:`scenario`, one row per option
below). The number of scenarios to run at once is usually limited by the
memory each solve needs rather than by CPU cores.

A scenario that fails is marked :code:`run_error` in the database and the
run continues with the remaining scenarios; the command exits with a
non-zero status if any scenario failed. The database is switched to WAL
journal mode for the duration of the run, which is not supported on network
file systems.

If the inputs have already been written and you only want to solve several
scenarios at once without importing results, :code:`gridpath_run_parallel`
takes the same CSV format and calls :code:`gridpath_run` for each scenario.

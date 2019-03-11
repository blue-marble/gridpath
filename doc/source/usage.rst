*****
Usage
*****

===========
Source Code
===========
GridPath's source code is stored in a GitHub repository. The repository is
currently private but you will soon be able to obtain the source code by
cloning it. `See instructions on GitHub <https://help.github
.com/en/articles/cloning-a-repository>`_.


============
Requirements
============

GridPath is written and tested in Python 3, uses an SQLite database to store
input and output data, and requires a solver to produce results.

Python
------

Running GridPath's source requires a Python 3 installation and several
Python packages.

Python Virtual Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^
We highly recommend that you set up a Python virtual
environment for GridPath to ensure that the appropriate packages are
installed and avoid interfering with the requirements of other Python
programs you may be using. One cross-platform way to set up a virtual
environment is via the Anaconda Python distribution. `You can obtain the
Anaconda here <https://www.anaconda.com/distribution/>`_. Once
it is installed, open a terminal and navigate to the GridPath root
directory. On a Windows machine, create the GridPath environment with::

    conda env create --name gridpath -f environment_pc.yml

On MacOS, the equivalent command is::

    conda env create --name gridpath -f environment_mac.yml

To activate the environment before running GridPath, enter the following::

    source activate gridpath

You can of course choose another way to manage your virtual environments,
e.g. with the *venv* Python 3 package (if you are using a single Python
version) or *pyenv* and *pyenv-virtualenv* (if you need more than one Python
versions).

Packages
^^^^^^^^

GridPath currently is requires the following Python packages: *Pyomo*,
*pandas*, and *matplotlib*. You can also install *sphinx* to build the docs
from source. To install the necessary packages, navigate to the GridPath
root directory, activate your GridPath environment, and run::

    python setup.py install

.. note:: The exact GridPath package installation instructions will likely
    change some, as we figure out how to make the platform more user-friendly.

.. todo:: setuptools not set up yet

Database
--------
While not strictly required -- you can generate TAB-delimited scenario input
files any way you like -- GridPath includes support for input and output
data management via an SQLite database. We recommend that you store data in
the database and use GridPath's built-in tools for loading input data into the
database, creating scenarios and generating scenario input files, and
importing scenario results into the database. We recommend `SQLite Studio
<https://sqlitestudio.pl/index.rvt>`_ as an SQLite database GUI.

Solver
------
You will need a solver to get optimization results. GridPath assumes you
will be using `Cbc (Coin-or branch and cut) <https://projects.coin-or
.org/Cbc>`_ by default, but you can specify a different solver as long as it
is `supported by Pyomo <https://pyomo.readthedocs
.io/en/latest/solving_pyomo_models.html#supported-solvers>`_,
e.g. GLPK, CPLEX, Gurobi, etc.



====================
Testing the Codebase
====================

To test the GridPath codebase, use the unittest module as follows::

    python -m unittest discover tests

Scenario directories are assumed to be located in ./scenarios/ by
default. For example, the inputs, results, and logs for a scenario
named 'test' would be in *./scenarios/test/*.

=============================
Running from the Command Line
=============================

You can run scenarios via the *run_scenario.py* script in the root
directory. The scenario name should be specified with the *--scenario*
argument. For example, to run a scenario named *test* from the GridPath
root directory, run the following::

    python run_scenario.py --scenario test

To see usage and other optional arguments, e.g. how to specify a
solver, check the help menu::

    python run_scenario.py --help

========
Examples
========
To run any of the problems in the *examples* directory, you also need
to specify a scenario location (as these are not in the default
*scenarios* subdirectory). For example, to run the *test* scenario in
the examples directory, run the following::

    python run_scenario.py --scenario test --scenario_location examples

.. note:: Some of the examples require a non-linear solver such as ipopt. If
    you don't have a non-linear solver, you will not be able to solve these
    examples and some of the unit tests will fail.

========
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

The next step is of the Python model (consisting of various modules that
create the model formulation) to read in the TAB-delimited input files and
create the optimization problem. The compiled model file is then sent to the
solver. GridPath is solver-agnostic and supports a wide range of solvers.

Once the solver finishes solving, it returns the results to GridPath.
GridPath's modules then write CSV results files to disk. The user can select
to manually or automatically import these results into the database.

Finally, GridPath includes functionality to process the results and creates
various visualizations.

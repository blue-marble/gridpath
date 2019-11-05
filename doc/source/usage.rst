*****
Usage
*****

================
Using a Terminal
================

To install GridPath, you will need to use a command-line interface. Once
installed, you will be able to interact with the platform through the user
interface.

On Windows, you can use cmd.exe, Windows PowerShell, or another command-line
interface. On Mac, you can use the Terminal application.


==================
GridPath Directory
==================

You first need to create a directory where to download GridPath's source
code. We will refer to this directory as :code:`PATH/TO/GRIDPATH`.

===========
Source Code
===========
GridPath's source code is stored in a GitHub repository. You will need
Git to download the source code.

--------------
Installing Git
--------------
Git installation instructions are `here <https://git-scm.com/book/en/v2/Getting-Started-Installing-Git>`_

On Windows, use the Git installer available `here <https://git-scm
.com/download/win>`_.

On MacOS, type :code:`git --version` on the command line; if you don't have
Git installed already, you will be prompted to install it.

On RPM-based Linux distributions (e.g Fedora), use :code:`sudo dnf install
git-all`; on Debian-based Linux distributions (e.g. Ubuntu), use :code:`sudo
apt install git-all`.

-------------------------------
Cloning the GridPath Repository
-------------------------------

Once you have Git installed, clone the repository with::

    git clone https://github.com/anamileva/gridpath.git PATH/TO/GRIDPATH

For more info on cloning repositories, see `the instructions on GitHub
<https://help.github.com/en/articles/cloning-a-repository>`_.

We will eventually distribute GridPath through pypi and conda, so cloning the
repository will eventually not be required except for users who want to edit
the source code.


============
Requirements
============

GridPath is written and tested in Python 3, uses an SQLite database to store
input and output data, and requires a solver to produce results.

------
Python
------

Running GridPath's source requires a Python 3 installation and several
Python packages. You can get the official CPython distribution `here
<https://www.python.org/downloads/>`_, the Anaconda Python distribution
`here <https://www.anaconda.com/distribution/>`_, or `another Python
distribution <https://wiki.python.org/moin/PythonDistributions>`_.


^^^^^^^^^^^^^^^^^^^^^^^^^^
Python Virtual Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^
We highly recommend that you set up a Python virtual
environment for GridPath to ensure that the appropriate packages are
installed and avoid interfering with the requirements of other Python
programs you may be using. Below are instructions for how to set up a
virtual environment using Python's *venv* module or with Anaconda. Make sure
to keep track of where your virtual environment directory is located, as you
will need to locate it if you are using the GridPath user interface. We will
refer to the GridPath Python environment directory as
:code:`PATH/TO/PYTHON/ENV`.

venv
****
The `venv <https://docs.python.org/3/library/venv.html>`_ package is part of
the Python 3 standard library and is a lightweight method for managing
virtual environments. Once you have installed Python 3, you can create the
virtual environment for GridPath by running::

    python3 -m venv PATH/TO/PYTHON/ENV

This will create the virtual environment in the :code:`PATH/TO/PYTHON/ENV`
directory.

On Windows, you can activate the virtual environment by running appropriate
activation script from inside the Scripts directory of the virtual
environment directory.

From cmd.exe::

    C:\> PATH\TO\PYTHON\ENV\Scripts\activate.bat

On Linux-based systems including MacOS, use::

    source PATH/TO/PYTHON/ENV/bin/activate

Anaconda
********
Another way to set up a virtual environment is via the Anaconda Python
distribution. `You can obtain Anaconda here <https://www.anaconda
.com/distribution/>`_. Create the GridPath environment with::

    conda env create --name gridpath

By default, environments are installed into the `envs` directory in your
conda directory. To activate the environment before running GridPath, enter
the following::

    source activate gridpath


^^^^^^^^
Packages
^^^^^^^^

You can install all needed Python packages, including those for the extra
features, by navigating to the the GridPath directory PATH/TO/GRIDPATH and
running:::

    pip install .[all]

Use the editable `-e` flag if you would like to edit the GridPath source code::

    pip install -e .[all]

Alternatively, if you don't want the extra features, you can install only the
required packages with::

    pip install .

Read below for what the extra features are to determine whether you need them.

Optional packages
*****************

The extra features are: 1) the GridPath user interface and 2) building/editing
the documentation.

GridPath's optional features can be installed individually as follows.

For editing or building documentation from source, run::

    pip install -e .[doc]

For using the GridPath user interface, run::

    pip install -e .[ui]

If you would like to edit the user-interface code, you will need Node.js in
addition to Python and will be required to install various node packages.
See the User Interface section for more info.


--------
Database
--------
While not strictly required -- you can generate TAB-delimited scenario input
files any way you like -- GridPath includes support for input and output
data management via an SQLite database. We recommend that you store data in
the database and use GridPath's built-in tools for loading input data into the
database, creating scenarios and generating scenario input files, and
importing scenario results into the database. We recommend `SQLite Studio
<https://sqlitestudio.pl/index.rvt>`_ as an SQLite database GUI.

------
Solver
------
You will need a solver to get optimization results. GridPath assumes you
will be using `Cbc (Coin-or branch and cut) <https://projects.coin-or
.org/Cbc>`_ by default, but you can specify a different solver as long as it
is `supported by Pyomo <https://pyomo.readthedocs
.io/en/latest/solving_pyomo_models.html#supported-solvers>`_,
e.g. GLPK, CPLEX, Gurobi, etc.

You can find the latest instructions for installing Cbc `here
<https://github.com/coin-or/Cbc#download>`_. On Windows, you can also
download the Cbc executable from the `AMPL website <https://ampl
.com/products/solvers/open-source/#cbc>`_. GridPath allows you to specify
the location of the solver executable; to get it to be recognized,
automatically, you can also add it to your PATH system variables (see
instructions for Windows `here <https://www.java.com/en/download/help/path
.xml>`_).


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

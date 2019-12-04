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

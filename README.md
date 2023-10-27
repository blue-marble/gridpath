[![GridPath Test Suite Status](https://github.com/blue-marble/gridpath/actions/workflows/test_gridpath.yml/badge.svg?branch=main)](https://github.com/blue-marble/gridpath/actions/workflows/test_gridpath.yml)
[![Documentation Status](https://readthedocs.org/projects/gridpath/badge/?version=latest)](https://gridpath.readthedocs.io/en/latest/?badge=latest)
[![Coverage Status](https://coveralls.io/repos/github/blue-marble/gridpath/badge.svg?branch=main)](https://coveralls.io/github/blue-marble/gridpath?branch=main)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Lint Black](https://github.com/blue-marble/gridpath/actions/workflows/black.yml/badge.svg?branch=main)](https://github.com/blue-marble/gridpath/actions/workflows/black.yml)
[![DOI](https://zenodo.org/badge/65574330.svg)](https://zenodo.org/badge/latestdoi/65574330)

# Welcome to GridPath

<p align="center" width="100%">
    <img src="https://github.com/blue-marble/gridpath/blob/main/doc/graphics/gridpath_logo.png?raw=true" width="20%"/>
</p>

![Approaches](https://github.com/blue-marble/gridpath/blob/main/doc/graphics/approaches.png?raw=true)


GridPath is a versatile power-system planning platform capable of a range of
planning approaches including production-cost, capacity-expansion, 
asset-valuation, and reliability modeling.

# Documentation
GridPath's documentation is hosted on [Read the Docs](https://gridpath.readthedocs.io/en/latest/).

# Installation

## Python
GridPath is tested on Python 3.9, 3.10, and 3.11. Get one of those Python versions [here](https://www.python.org/downloads/ "Python download").

## GridPath Python environment
You should create a Python environment for your GridPath installation, e.g. via 
`venv`, [a lightweight environment manager](https://docs.python.org/3/library/venv.html "venv") 
that is part of the standard Python distribution. Make sure to [create](https://docs.python.org/3/library/venv.html#creating-virtual-environments "create") [activate](https://docs.python.org/3/library/venv.html#how-venvs-work "activate") the environment before installing GridPath.

## Install GridPath from PyPi

Once you have _created and activated_ the GridPath Python environment, you 
can install the latest version of GridPath from PyPi with:

```bash
pip install GridPath
```

## Install GridPath from source

You can alternatively download the GridPath source code and install from 
source.

```bash
pip install .[all]
```

**NOTE:** If you plan to edit the GridPath code, you should install with the `-e` flag.

## Solver
You will need a solver to use this platform. GridPath assumes you will be using Cbc (Coin-or branch and cut) by default, but you can specify a 
different solver.


# Usage

## The gridpath_run and gridpath_run_e2e commands
If you install GridPath via the setup script following the instructions above, 
you can use the command `gridpath_run` to run a scenario from any directory 
-- as long as your GridPath Python environment is enabled -- as follows:
```bash
gridpath_run --scenario SCENARIO_NAME --scenario_location 
/PATH/TO/SCENARIO 
```

If you are using the database, you can use the command `gridpath_run_e2e` to 
run GridPath end-to-end, i.e. get inputs for the scenario from the database, 
solve the scenario problem, import the results into the database, and 
process them. Refer to the documentation for how to build the database.

```bash
gridpath_run_e2e --scenario SCENARIO_NAME --scenario_location 
/PATH/TO/SCENARIO 
```

To see usage and other optional arguments, e.g. how to specify a 
solver, check the help menu, e.g.:
```bash
gridpath_run --help
```

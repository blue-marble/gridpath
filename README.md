[![GridPath Test Suite Status](https://github.com/blue-marble/gridpath/actions/workflows/test_gridpath.yml/badge.svg?branch=main)](https://github.com/blue-marble/gridpath/actions/workflows/test_gridpath.yml)
[![Documentation Status](https://readthedocs.org/projects/gridpath/badge/?version=latest)](https://gridpath.readthedocs.io/en/latest/?badge=latest)
[![Coverage Status](https://coveralls.io/repos/github/blue-marble/gridpath/badge.svg?branch=main)](https://coveralls.io/github/blue-marble/gridpath?branch=main)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Lint Black](https://github.com/blue-marble/gridpath/actions/workflows/black.yml/badge.svg?branch=main)](https://github.com/blue-marble/gridpath/actions/workflows/black.yml)
[![DOI](https://zenodo.org/badge/65574330.svg)](https://zenodo.org/badge/latestdoi/65574330)

# Welcome to GridPath

<p style="text-align:center;"><img src="https://lh5.googleusercontent.com/vdOTo-MiWgNwRgOfHH252zJ4tHWffo4nlcVCgJoS5ns9JWhrow2v_3Za22kBJMfn4CfcMLKg9NO3DdaGiqhczc4=w16383" alt="drawing" width="20%"/>

![Approaches](https://lh5.googleusercontent.com/IOfwnLoGGhwO0F11aynM1b3dkWB7YvmrpwhAprfPgLfnemEVxbwXA7IAbwGcPsBrubQYIaiIqEoNffJMIrARIt0_oFt20W4e3KF_OM1OkZ9S8FsO=w1280)

GridPath is a versatile power-system planning platform capable of a range of
planning approaches including production-cost, capacity-expansion, 
asset-valuation, and reliability modeling.

# Documentation
GridPath's documentation is hosted on [Read the Docs](https://gridpath.readthedocs.io/en/latest/).

# Installation

## Python
GridPath is developed and tested on Python 3.8. Get Python 3.8
[here](https://www.python.org/downloads/ "Python download").

## Python Packages
You should create a Python environment for your GridPath installation, e.g. via 
`venv`, [a lightweight environment manager](https://docs.python.org/3/library/venv.html, "venv") 
that is part of the standard Python distribution. You can install all needed Python 
packages, including the developer extras, by navigating to the GridPath root 
directory (which is where this `README.md` file is located) and running:
```bash
pip install -e .[all]
```

For most users, installing GridPath's base set of Python packages and those needed 
to use the graphical user interface would be sufficient. You can do so by running:
```bash
pip install -e .[ui]
```

NOTE: if you don't plan to edit the GridPath code, you can install without the 
`-e` option.

## Solver
You will need a solver to use this platform. GridPath assumes you will be 
using Cbc (Coin-or branch and cut) by default, but you can specify a 
different solver (see the **Usage** section).

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
process them.

```bash
gridpath_run_e2e --scenario SCENARIO_NAME --scenario_location 
/PATH/TO/SCENARIO 
```

To see usage and other optional arguments, e.g. how to specify a 
solver, check the help menu, e.g.:
```bash
gridpath_run --help
```

NOTE: To activate your gridpath environment, use the following command (
assuming your environment is called "env", is created with `venv`, and is stored 
in the GridPath root folder):
```bash
source env/bin/activate
```

## Help
In general, you can check usage of GridPath's scripts by calling the `--help` 
option, e.g.:
```bash
python get_scenario_inputs.py --help
```

# Testing

To test the GridPath codebase, use the unittest module as follows from the 
root directory:
```bash
python -m unittest discover tests
```

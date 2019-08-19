# Welcome to GridPath

GridPath is a production-cost simulation and capacity-expansion power system 
model.

# Installation

## Python
GridPath is developed and tested on Python 3.7. Get Python [here](https://www.python.org/downloads/ "Python download").

## Packages
You can install all needed Python packages, including those for the extra 
features, by navigating to the the 
GridPath root directory (which is where this `README.txt` file is located) and 
running:
```bash
pip install -e .[all]
```

Alternatively, if you don't want the extra features, you can install only the 
required packages with:
```bash
pip install -e .
```

NOTE: if you don't plan to edit the GridPath code, you can install without the 
`-e` option.

## Extra packages
The extra features are 1) building/editing documentation and 2) the GridPath
user interface.

GridPath's optional features can be installed individually as follows.

For editing or building documentation from source, run:
```bash
pip install -e .[documentation]
```

For using the GridPath user interface, run:
```bash
pip install -e .[ui]
```

## Solver
You will need a solver to use this platform. GridPath assumes you will be 
using Cbc (Coin-or branch and cut) by default, but you can specify a 
different solver (see the **Usage** section).

# Usage

## The run_gridpath command
If you install GridPath via the setup script following the instructions above, 
you can use the command `run_gridpath` to run a scenario from any directory 
-- as long as your GridPath Python environment is enabled -- as follows:
```bash
run_gridpath --scenario SCENARIO_NAME --scenario_location 
/PATH/TO/SCENARIO 
```

To see usage and other optional arguments, e.g. how to specify a 
solver, check the help menu:
```bash
run_gridpath --help
```

## The run_scenario.py script
You can also run scenarios via the `run_scenario.py` script in the 
`./gridpath/` directory. The scenario name should be specified with the 
`--scenario` argument. For example, to run a scenario named 'test' (located 
in the `./scenarios/` directory) navigate to the `./gridpath/` directory and 
run the following:
```bash
python run_scenario.py --scenario test
```

Scenario directories are assumed to be located in the `./scenarios/` 
directory by default. For example, the inputs, results, and logs for a 
scenario named 'test' would be in `./scenarios/test/`.

To run any of the problems in the `./examples/` directory, you also need 
to specify a scenario location (as the examples are not located in the default 
`./scenarios/` subdirectory). For example, to run the 'test' scenario in 
the examples directory, run the following (from the `./gridpath/` directory):
```bash
python run_scenario.py --scenario test --scenario_location examples
```

To see usage and other optional arguments, e.g. how to specify a 
solver, check the help menu:
```bash
python run_scenario.py --help
```

# Testing

To test the GridPath codebase, use the unittest module as follows from the 
root directory:
```bash
python -m unittest discover tests
```

Some of the examples require a non-linear solver such as ipopt. If you 
don't have a non-linear solver, you will not be able to solve these examples 
and some of the unit tests will fail.

# Help
In general, you can check usage of GridPath's scripts by calling the `--help` 
option , e.g.:
```bash
python get_scenario_inputs.py --help
```
# Documentation

TBD

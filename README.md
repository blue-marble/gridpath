# Welcome to GridPath

GridPath is a production-cost simulation and capacity-expansion power system 
model.

# Installation

## Python
GridPath is developed and tested on Python 3.7. Get Python 
[here](https://www.python.org/downloads/ "Python download").

## Packages
We highly recommend that you create a Python environment for your GridPath
installation, e.g. via `venv`, [a lightweight environment manager](
https://docs.python.org/3/library/venv.html, "venv") that is part of the 
standard Python distribution. You can install all needed Python packages,
including those for the extra features, by navigating to the GridPath root
directory (which is where this `README.md` file is located) and running:
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
pip install -e .[doc]
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

## The run_scenario.py and run_end_to_end.py scripts
You can also run scenarios via the `run_scenario.py` script in the 
`./gridpath/` directory (note: "." represents the root directory, i.e. where
this `README.md` file is located). The scenario name should be specified with 
the `--scenario` argument. For example, to run a scenario named 'test' (located 
in the `./scenarios/` directory) navigate to the `./gridpath/` directory and 
run the following:
```bash
python run_scenario.py --scenario test
```

Scenario directories are assumed to be located in the `./scenarios/` 
directory by default. For example, the inputs, results, and logs for a 
scenario named 'test' would be in `./scenarios/test/`. You can also run
scenarios located in directories other than `./scenarios` by specifying the 
path to that directory with (absolute path or path relative to `./gridpath`). 
For example, to run the 'test' scenario in the examples directory, run the 
following (from the `./gridpath/` directory):
```bash
python run_scenario.py --scenario test --scenario_location ../examples
``` 

If you are using the database, you can use the `run_end_to_end.py` script to 
run GridPath end-to-end, i.e. get inputs for the scenario from the database, 
solve the scenario problem, import the results into the database, and 
process them.

```bash
python run_end_to_end.py --scenario test
```

To see usage and other optional arguments, e.g. how to specify a 
solver, check the help menu, e.g.:
```bash
python run_scenario.py --help
```

# Testing

To test the GridPath codebase, use the unittest module as follows from the 
root directory:
```bash
python -m unittest discover tests
```


# Help
In general, you can check usage of GridPath's scripts by calling the `--help` 
option, e.g.:
```bash
python get_scenario_inputs.py --help
```


# Documentation

To build the documentation from source, navigate to the `./doc` folder in
your terminal and type the following command:
```bash
make html
```

This will build the documentation in HTML format in the `./doc/build/html`
folder. You can view the documentation by double clicking any of the .html
files (we recommend starting at `index.html`). 

Note that you will first need to install 
[Sphinx](http://www.sphinx-doc.org/en/master/) on your computer (see the 
Installation section above). In the future, the latest documentation build will
be hosted online so you don't have to build it from source yourself. 


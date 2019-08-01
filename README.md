Welcome to GridPath, a production-cost simulation and 
capacity-expansion power system model.

GridPath is developed and tested on Python 3.7. You can install all needed 
packages, including those for the extra features, by navigating to the the 
GridPath root directory (which is where this README file is located) and 
running:
>> pip install .[all]

The extra features are 1) building/editing documentation and 2) the GridPath
user interface.

Alternatively, if you don't want the extra features, you can install only the 
required packages with:
>> pip install .

GridPath's optional features can be installed indivdually as follows.

For editing or building documentation from source, run:
>> pip install .[documentation]

For using the GridPath user interface, run:
>> pip install .[ui]

The exact package versions for GridPath's development environment can be 
found in 'requirements.txt'.

You will need a solver to use this platform. GridPath assumes you will be 
using Cbc (Coin-or branch and cut) by default, but you can specify a 
different solver (see below).

Some of the examples require a non-linear solver such as ipopt. If you 
don't have a non-linear solver, you will not be able to solve these examples 
and some of the unit tests will fail.

To test the GridPath codebase, use the unittest module as follows from the 
root directory:
>> python -m unittest discover tests

Scenario directories are assumed to be located in the ./scenarios/ 
directory by default. For example, the inputs, results, and logs for a 
scenario named 'test' would be in ./scenarios/test/.

You can run scenarios via the 'run_scenario.py' script in the ./gridpath/ 
directory. The scenario name should be specified with the '--scenario' 
argument. For example, to run a scenario named 'test,' navigate to the 
./gridpath/ directory and run the following:
>> python run_scenario.py --scenario test

To see usage and other optional arguments, e.g. how to specify a 
solver, check the help menu:
>> python run_scenario.py --help

In general, you can check usage of GridPath's scripts by calling the '--help' 
option , e.g.:
>> python get_scenario_inputs.py --help

To run any of the problems in the 'examples' directory, you also need 
to specify a scenario location (as these are not in the default 
'scenarios' subdirectory). For example, to run the 'test' scenario in 
the examples directory, run the following (from the ./gridpath/ directory):
>> python run_scenario.py --scenario test --scenario_location examples

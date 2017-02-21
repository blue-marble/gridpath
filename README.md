Welcome to GridPath, a production-cost simulation and 
capacity-expansion power system model.

You will need a solver to use this model. GridPath assumes you will be 
using Cbc (Coin-or branch and cut) by default, but you can specify a 
different solver.

Scenario directories are assumed to be located in ./scenarios/ by 
default. For example, the inputs, results, and logs for a scenario 
named 'test' would be in ./scenarios/test/.

You can run scenarios via the 'run_scenario.py' script in the root 
directory. The scenario name should be specified with the '--scenario' 
argument. For example, to run a scenario named 'test' from the GridPath
root directory, run the following:
>> python run_scenario.py --scenario test

To see usage and other optional arguments, e.g. how to specify a 
solver, run:
>> python run_scenario.py --help

To run any of the problems in the 'examples' directory, you also need 
to specify a scenario location (as these are not in the default 
'scenarios' subdirectory). For example, to run the 'test' scenario in 
the examples directory, run the following:
>> python run_scenario.py --scenario test --scenario_location examples

Some of the examples require a non-linear solver such as ipopt. If you 
don't have ipopt, you will not be able to solve these examples and some 
of the tests will fail.

To test the model, use the unittest module as follows:
>> python -m unittest discover tests
 
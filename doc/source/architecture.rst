************
Architecture
************

This section describes GridPath's modular architecture, i.e. how the modules
are linked and work together (as opposed to their formulation or the
functionality they add).

gridpath.auxiliary.module_list
==============================

.. automodule:: gridpath.auxiliary.module_list
    :members: all_modules_list, optional_modules_list,
        cross_feature_modules_list, determine_modules, load_modules

gridpath.auxiliary.dynamic_components
=====================================
.. automodule:: gridpath.auxiliary.dynamic_components
    :members: DynamicComponents


run_scenario.py
===============

.. automodule:: run_scenario
    :members: main, parse_arguments, ScenarioStructure, run_scenario,
        run_optimization, create_and_solve_problem,
        populate_dynamic_components, create_abstract_model,
        load_scenario_data, create_problem_instance, fix_variables, solve

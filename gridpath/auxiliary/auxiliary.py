#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Various auxiliary functions used in other modules
"""

import datetime
from importlib import import_module
import os.path
import sys


def load_subtype_modules(
        required_subtype_modules, package, required_attributes
):
    """
    Load subtype modules (e.g. capacity types, operational types, etc).
    This function will also check that the subtype module have certain
    required attributes.

    :param required_subtype_modules:
    :param package:
    :param required_attributes:
    :return:
    """
    imported_subtype_modules = dict()
    for m in required_subtype_modules:
        try:
            imp_m = \
                import_module(
                    "." + m,
                    package=package
                )
            imported_subtype_modules[m] = imp_m
            for a in required_attributes:
                if hasattr(imp_m, a):
                    pass
                else:
                    raise Exception(
                        "ERROR! No " + str(a) + " function in subtype module "
                        + str(imp_m) + ".")
        except ImportError:
            print("ERROR! Subtype module " + m + " not found.")

    return imported_subtype_modules


def load_gen_storage_capacity_type_modules(required_capacity_modules):
    return load_subtype_modules(
            required_capacity_modules,
            "gridpath.project.capacity.capacity_types",
            ["capacity_rule", "capacity_cost_rule"]
        )


def load_reserve_type_modules(required_reserve_modules):
    return load_subtype_modules(
        required_reserve_modules,
        "gridpath.project.operations.reserves",
        []
         )


# TODO: add curtailment rules as required?
def load_operational_type_modules(required_operational_modules):
    return load_subtype_modules(
        required_operational_modules,
        "gridpath.project.operations.operational_types",
        ["power_provision_rule", "fuel_burn_rule",
         "startup_shutdown_rule"]
         )


def load_prm_type_modules(required_prm_modules):
    return load_subtype_modules(
        required_prm_modules,
        "gridpath.project.reliability.prm.prm_types",
        ["elcc_eligible_capacity_rule",]
         )


def load_tx_capacity_type_modules(required_tx_capacity_modules):
    return load_subtype_modules(
            required_tx_capacity_modules,
            "gridpath.transmission.capacity.capacity_types",
            ["min_transmission_capacity_rule",
             "max_transmission_capacity_rule"]
        )


def join_sets(mod, set_list):
    """
    Join sets in a list.
    If list contains only a single set, return just that set.

    :param mod:
    :param set_list:
    :return:
    """
    if len(set_list) == 0:
        return []
    elif len(set_list) == 1:
        return getattr(mod, set_list[0])
    else:
        joined_set = set()
        for s in set_list:
            for element in getattr(mod, s):
                joined_set.add(element)
    return joined_set


def generator_subset_init(generator_parameter, expected_type):
    """
    Initialize subsets of generators by subtype based on subtype flags.
    Need to return a function with the model as argument, i.e. 'lambda mod'
    because we can only iterate over the
    generators after data is loaded; then we can pass the abstract model to the
    initialization function.

    :param generator_parameter:
    :param expected_type:
    :return:
    """
    return lambda mod: \
        list(g for g in mod.PROJECTS if getattr(mod, generator_parameter)[g]
             == expected_type)


def check_list_has_single_item(l, error_msg):
    if len(l) > 1:
        raise ValueError(error_msg)
    else:
        pass


def find_list_item_position(l, item):
    """

    :param l:
    :param item:
    :return:
    """
    return [i for i, element in enumerate(l) if element == item]


def check_list_items_are_unique(l):
    """
    Check if items in a list are unique

    :param l:
    A list
    :return:
    Nothing
    """
    for item in l:
        positions = find_list_item_position(l, item)
        check_list_has_single_item(
            l=positions,
            error_msg="Service " + str(item) + " is specified more than once" +
            " in generators.tab.")


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


class Logging:
    """
    Log output to both standard output and a log file. This will be 
    accomplished by assigning this class to sys.stdout.
    """

    def __init__(self, logs_dir):
        """
        Assign sys.stdout and a log file as output destinations

        :param logs_dir: 
        """
        self.terminal = sys.stdout
        self.log_file_path = \
            os.path.join(
                logs_dir, datetime.datetime.now().strftime(
                                              '%Y-%m-%d_%H-%M-%S') + ".log"
            )
        self.log_file = open(self.log_file_path, "w", buffering=1)

    def __getattr__(self, attr):
        """
        Default to sys.stdout when calling attributes for this class

        :param attr: 
        :return: 
        """
        return getattr(self.terminal, attr)

    def write(self, message):
        """
        Output to both terminal and a log file

        :param message: 
        :return: 
        """
        self.terminal.write(message)
        self.log_file.write(message)

    def flush(self):
        """
        Flush both the terminal and the log file

        :return: 
        """
        self.terminal.flush()
        self.log_file.flush()


def get_scenario_id_and_name(scenario_id_arg, scenario_name_arg, c, script):
    """
    huh

    :param scenario_id_arg: 
    :param scenario_name_arg: 
    :param c: 
    :param script: 
    :return: 
    """
    if scenario_id_arg is None and scenario_name_arg is None:
        raise TypeError(
            """ERROR: Either scenario_id or scenario_name must be specified. 
            Run 'python """ + script + """'.py --help' for help."""
        )
    elif scenario_id_arg is not None and scenario_name_arg is None:
        scenario_id = scenario_id_arg
        scenario_name = c.execute(
            """SELECT scenario_name
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
    elif scenario_id_arg is None and scenario_name_arg is not None:
        scenario_name = scenario_name_arg
        scenario_id = c.execute(
            """SELECT scenario_id
               FROM scenarios
               WHERE scenario_name = '{}';""".format(scenario_name)
        ).fetchone()[0]
    else:
        # If both scenario_id and scenario_name
        scenario_name_db = c.execute(
            """SELECT scenario_name
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id_arg)
        ).fetchone()[0]
        if scenario_name_db == scenario_name_arg:
            scenario_id = scenario_id_arg
            scenario_name = scenario_name_arg
        else:
            raise ValueError("ERROR: scenario_id and scenario_name don't "
                             "match in database.")

    return scenario_id, scenario_name

#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from pyomo.environ import Expression


from gridpath.auxiliary.auxiliary import load_subtype_modules
from gridpath.auxiliary.dynamic_components import required_availability_modules


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    # Import needed availability type modules
    imported_availability_modules = \
        load_availability_type_modules(
            getattr(d, required_availability_modules))

    # First, add any components specific to the availability type modules
    for op_m in getattr(d, required_availability_modules):
        imp_op_m = imported_availability_modules[op_m]
        if hasattr(imp_op_m, "add_module_specific_components"):
            imp_op_m.add_module_specific_components(m, d)

    def availability_derate_rule(mod, g, tmp):
        """

        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        # TODO: make the no_availability type module, which will be the
        #  default for the availability type param (it will just return 1 as
        #  the derate)
        availability_type = mod.availability_type[g]
        return imported_availability_modules[availability_type]. \
            availability_derate_rule(mod, g, tmp)

    m.Availability_Derate = Expression(
        m.PROJECT_OPERATIONAL_TIMEPOINTS, rule=availability_derate_rule
    )


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """
    imported_availability_modules = \
        load_availability_type_modules(
            getattr(d, required_availability_modules)
        )
    for op_m in getattr(d, required_availability_modules):
        if hasattr(imported_availability_modules[op_m],
                   "load_module_specific_data"):
            imported_availability_modules[op_m].load_module_specific_data(
                m, data_portal, scenario_directory, subproblem, stage)
        else:
            pass


def validate_inputs(subscenarios, subproblem, stage, conn):
    """

    :param subscenarios:
    :param subproblem:
    :param stage:
    :param conn:
    :return:
    """
    # TODO: what is our process for iterating over types to do type-specific
    #  validation?
    from gridpath.project.availability.availability_types\
        .exogenous import validate_inputs
    validate_inputs(subscenarios=subscenarios, subproblem=subproblem,
                    stage=stage, conn=conn)


def load_availability_type_modules(required_availability_types):
    """

    :param required_availability_types:
    :return:
    """
    return load_subtype_modules(
        required_subtype_modules=required_availability_types,
        package="gridpath.project.availability.availability_types",
        required_attributes=["availability_derate_rule"]
    )

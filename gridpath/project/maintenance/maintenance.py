#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

from pyomo.environ import Expression


from gridpath.auxiliary.auxiliary import load_subtype_modules
from gridpath.auxiliary.dynamic_components import required_maintenance_modules


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """

    # Import needed maintenance type modules
    imported_maintenance_modules = \
        load_maintenance_type_modules(
            getattr(d, required_maintenance_modules))

    # First, add any components specific to the maintenance type modules
    for op_m in getattr(d, required_maintenance_modules):
        imp_op_m = imported_maintenance_modules[op_m]
        if hasattr(imp_op_m, "add_module_specific_components"):
            imp_op_m.add_module_specific_components(m, d)

    def maintenance_derate_rule(mod, g, tmp):
        """

        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        # TODO: make the no_maintenance type module, which will be the
        #  default for the maintenance type param (it will just return 1 as
        #  the derate)
        maintenance_type = mod.maintenance_type[g]
        return imported_maintenance_modules[maintenance_type]. \
            maintenance_derate_rule(mod, g, tmp)

    m.Maintenance_Derate = Expression(
        m.PROJECT_OPERATIONAL_TIMEPOINTS, rule=maintenance_derate_rule
    )


def load_maintenance_type_modules(required_maintenance_types):
    """

    :param required_maintenance_types:
    :return:
    """
    return load_subtype_modules(
        required_subtype_modules=required_maintenance_types,
        package="gridpath.project.maintenance.maintenance_types",
        required_attributes=["maintenance_derate_rule"]
    )

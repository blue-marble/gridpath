#!/usr/bin/env python

import os.path
from pyomo.environ import Set, Param, Expression


from modules.auxiliary.dynamic_components import required_capacity_modules, \
    capacity_type_operational_period_sets, \
    storage_only_capacity_type_operational_period_sets
from modules.auxiliary.auxiliary import \
    load_gen_storage_capacity_type_modules, join_sets, \
    make_project_time_var_df


def add_model_components(m, d):
    """

    :param m:
    :param d:
    :return:
    """
    m.PROJECTS = Set()
    m.load_zone = Param(m.PROJECTS, within=m.LOAD_ZONES)
    m.capacity_type = Param(m.PROJECTS)

    # Import needed capacity type modules
    imported_capacity_modules = \
        load_gen_storage_capacity_type_modules(
            getattr(d, required_capacity_modules))

    # First, add any components specific to the capacity type modules
    for op_m in getattr(d, required_capacity_modules):
        imp_op_m = imported_capacity_modules[op_m]
        if hasattr(imp_op_m, "add_module_specific_components"):
            imp_op_m.add_module_specific_components(m, d)

    m.PROJECT_OPERATIONAL_PERIODS = \
        Set(dimen=2,
            initialize=lambda mod: 
            join_sets(mod, getattr(d, capacity_type_operational_period_sets))
            )

    def capacity_rule(mod, g, p):
        gen_cap_type = mod.capacity_type[g]
        return imported_capacity_modules[gen_cap_type].\
            capacity_rule(mod, g, p)

    m.Capacity_MW = Expression(m.PROJECT_OPERATIONAL_PERIODS,
                               rule=capacity_rule)

    m.STORAGE_OPERATIONAL_PERIODS = \
        Set(dimen=2,
            initialize=lambda mod: 
            join_sets(
                mod,
                getattr(d, storage_only_capacity_type_operational_period_sets)
            )
            )

    def energy_capacity_rule(mod, g, p):
        cap_type = mod.capacity_type[g]
        if hasattr(imported_capacity_modules[cap_type], "energy_capacity_rule"):
            return imported_capacity_modules[cap_type]. \
                energy_capacity_rule(mod, g, p)
        else:
            raise Exception("Project " + str(g)
                            + " is of capacity type " + str(cap_type)
                            + ". This capacity type module does not have "
                            + "a function 'energy_capacity_rule,' "
                            + "but " + str(g)
                            + " is defined as storage project.")

    m.Energy_Capacity_MWh = Expression(
        m.STORAGE_OPERATIONAL_PERIODS,
        rule=energy_capacity_rule)

    # Define various sets to be used in operations module
    m.OPERATIONAL_PERIODS_BY_PROJECT = \
        Set(m.PROJECTS,
            rule=lambda mod, gen: set(
                p for (g, p) in mod.PROJECT_OPERATIONAL_PERIODS if
                g == gen)
            )

    def gen_op_tmps_init(mod):
        gen_tmps = set()
        for g in mod.PROJECTS:
            for p in mod.OPERATIONAL_PERIODS_BY_PROJECT[g]:
                for tmp in mod.TIMEPOINTS_IN_PERIOD[p]:
                    gen_tmps.add((g, tmp))
        return gen_tmps
    m.PROJECT_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2, rule=gen_op_tmps_init)

    def op_gens_by_tmp(mod, tmp):
        """
        Figure out which generators are operational in each timepoint
        :param mod:
        :param tmp:
        :return:
        """
        gens = list(
            g for (g, t) in mod.PROJECT_OPERATIONAL_TIMEPOINTS if t == tmp)
        return gens

    m.OPERATIONAL_PROJECTS_IN_TIMEPOINT = \
        Set(m.TIMEPOINTS, initialize=op_gens_by_tmp)


def load_model_data(m, d, data_portal, scenario_directory, horizon, stage):
    data_portal.load(filename=os.path.join(scenario_directory,
                                           "inputs", "projects.tab"),
                     index=m.PROJECTS,
                     select=("project", "load_zone", "capacity_type"),
                     param=(m.load_zone, m.capacity_type)
                     )

    imported_capacity_modules = \
        load_gen_storage_capacity_type_modules(getattr(d, required_capacity_modules))
    for op_m in getattr(d, required_capacity_modules):
        if hasattr(imported_capacity_modules[op_m],
                   "load_module_specific_data"):
            imported_capacity_modules[op_m].load_module_specific_data(
                m, data_portal, scenario_directory, horizon, stage)
        else:
            pass


def export_results(scenario_directory, horizon, stage, m, d):
    """
    Export operations results.
    :param scenario_directory:
    :param horizon:
    :param stage:
    :param m:
    :param d:
    :return:
    """

    d.module_specific_df = []

    imported_capacity_modules = \
        load_gen_storage_capacity_type_modules(getattr(d, required_capacity_modules))
    for op_m in getattr(d, required_capacity_modules):
        if hasattr(imported_capacity_modules[op_m],
                   "export_module_specific_results"):
            imported_capacity_modules[
                op_m].export_module_specific_results(m, d)
        else:
            pass

    capacity_df = make_project_time_var_df(
        m,
        "PROJECT_OPERATIONAL_PERIODS",
        "Capacity_MW",
        ["project", "period"],
        "capacity_mw"
    )

    # Storage is not required, so only make this dataframe if
    # STORAGE_OPERATIONAL_PERIODS set is not empty
    if len(getattr(m, "STORAGE_OPERATIONAL_PERIODS")) > 0:
        energy_capacity_df = make_project_time_var_df(
            m,
            "STORAGE_OPERATIONAL_PERIODS",
            "Energy_Capacity_MWh",
            ["project", "period"],
            "energy_capacity_mwh"
        )
    else:
        energy_capacity_df = []

    # Merge and export dataframes
    dfs_to_merge = [capacity_df] + [energy_capacity_df] + d.module_specific_df

    df_for_export = reduce(lambda left, right:
                           left.join(right, how="outer"),
                           dfs_to_merge)
    df_for_export.to_csv(
        os.path.join(scenario_directory, horizon, stage, "results",
                     "capacity.csv"),
        header=True, index=True)

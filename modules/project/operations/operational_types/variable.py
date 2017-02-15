#!/usr/bin/env python

"""
Operations of variable generators. Can be curtailed (dispatched down).
Can't provide reserves.
"""

import os.path

from pyomo.environ import Param, Set, Var, Constraint, NonNegativeReals, \
    Expression

from modules.auxiliary.auxiliary import generator_subset_init, \
    make_project_time_var_df
from modules.auxiliary.dynamic_components import headroom_variables, \
    footroom_variables, reserve_variable_derate_params, \
    reserve_provision_subhourly_adjustment_params


def add_module_specific_components(m, d):
    """
    Variable generators require a capacity factor for each timepoint.
    :param m:
    :return:
    """
    # Sets and params
    m.VARIABLE_GENERATORS = Set(within=m.PROJECTS,
                                initialize=generator_subset_init(
                                    "operational_type", "variable")
                                )

    m.VARIABLE_GENERATOR_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.VARIABLE_GENERATORS))

    # TODO: allow cap factors greater than 1?
    m.cap_factor = Param(m.VARIABLE_GENERATOR_OPERATIONAL_TIMEPOINTS,
                         within=NonNegativeReals)

    # Variable generators treated as dispatchable (can also be curtailed and
    # provide reserves)
    m.Provide_Variable_Power_MW = \
        Var(m.VARIABLE_GENERATOR_OPERATIONAL_TIMEPOINTS,
            within=NonNegativeReals)

    def max_power_rule(mod, g, tmp):
        """
        Power provision plus upward services cannot exceed available power.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Provide_Variable_Power_MW[g, tmp] + \
            sum(
            getattr(mod, c)[g, tmp]
            / getattr(
                mod, getattr(d, reserve_variable_derate_params)[c]
            )[g]
            for c in getattr(d, headroom_variables)[g]
        ) \
            <= mod.Capacity_MW[g, mod.period[tmp]] * mod.cap_factor[g, tmp]
    m.Variable_Max_Power_Constraint = \
        Constraint(m.VARIABLE_GENERATOR_OPERATIONAL_TIMEPOINTS,
                   rule=max_power_rule)

    def min_power_rule(mod, g, tmp):
        """
        Power provision minus downward services cannot be less than 0.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Provide_Variable_Power_MW[g, tmp] - \
            sum(
            getattr(mod, c)[g, tmp]
            / getattr(
                mod, getattr(d, reserve_variable_derate_params)[c]
            )[g]
            for c in getattr(d, footroom_variables)[g]
        ) \
            >= 0
    m.Variable_Min_Power_Constraint = \
        Constraint(m.VARIABLE_GENERATOR_OPERATIONAL_TIMEPOINTS,
                   rule=min_power_rule)

    def scheduled_curtailment_expression_rule(mod, g, tmp):
        """
        Scheduled curtailment
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Capacity_MW[g, mod.period[tmp]] * mod.cap_factor[g, tmp] - \
            mod.Provide_Variable_Power_MW[g, tmp]

    m.Scheduled_Variable_Generator_Curtailment_MW = \
        Expression(m.VARIABLE_GENERATOR_OPERATIONAL_TIMEPOINTS,
                   rule=scheduled_curtailment_expression_rule)

    def subhourly_curtailment_expression_rule(mod, g, tmp):
        """
        Subhourly curtailment from providing downward reserves
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        subhourly_footroom_adjustment = \
            sum(
                getattr(mod, c)[g, tmp] *
                # This is tricky
                # We need to get the value of the adjustment param
                # The adjustment parameter name varies by reserve type and its
                # value varies by balancing area
                # The balancing area param names also varies by reserve type
                # In the dynamic components, we have created a dictionary
                # that has the reserve variable name as key and a tuple as
                # value for each key: the first value in the tuple is the
                # subhourly adjustment parameter name and the second
                # tuple value is the balancing area parameter name (for this
                # type of reserve)
                # Here, we are getting the value for the following:
                # subhourly_adjustment_param[this type of reserve][
                getattr(mod,
                        getattr(d,
                                reserve_provision_subhourly_adjustment_params
                                )[c][0]  # this is the adjustment param name
                        )[
                    getattr(mod,
                            getattr(
                                d,
                                reserve_provision_subhourly_adjustment_params
                            )[c][1]  # this is the balancing area param name
                            )[g]  # the balancing area (value) varies by g
                ]  # the index of the adjustment param is a balancing area
                # adjustment param name and BA param name vary by reserve type
                for c in getattr(d, footroom_variables)[g]
            )

        return subhourly_footroom_adjustment

    m.Subhourly_Variable_Generator_Curtailment_MW = \
        Expression(m.VARIABLE_GENERATOR_OPERATIONAL_TIMEPOINTS,
                   rule=subhourly_curtailment_expression_rule)

    def subhourly_energy_delivered_expression_rule(mod, g, tmp):
        """
        Subhourly energy delivered from providing upward reserves
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        subhourly_headroom_adjustment = \
            sum(
                getattr(mod, c)[g, tmp] *
                # This is tricky
                # We need to get the value of the adjustment param
                # The adjustment parameter name varies by reserve type and its
                # value varies by balancing area
                # The balancing area param names also varies by reserve type
                # In the dynamic components, we have created a dictionary
                # that has the reserve variable name as key and a tuple as
                # value for each key: the first value in the tuple is the
                # subhourly adjustment parameter name and the second
                # tuple value is the balancing area parameter name (for this
                # type of reserve)
                # Here, we are getting the value for the following:
                # subhourly_adjustment_param[this type of reserve][
                getattr(mod,
                        getattr(d,
                                reserve_provision_subhourly_adjustment_params
                                )[c][0]  # this is the adjustment param name
                        )[
                    getattr(mod,
                            getattr(
                                d,
                                reserve_provision_subhourly_adjustment_params
                            )[c][1]  # this is the balancing area param name
                            )[g]  # the balancing area (value) varies by g
                ]  # the index of the adjustment param is a balancing area
                # adjustment param name and BA param name vary by reserve type
                for c in getattr(d, headroom_variables)[g]
            )

        return subhourly_headroom_adjustment

    m.Subhourly_Variable_Generator_Energy_Delivered_MW = \
        Expression(m.VARIABLE_GENERATOR_OPERATIONAL_TIMEPOINTS,
                   rule=subhourly_energy_delivered_expression_rule)

    def total_curtailment_expression_rule(mod, g, tmp):
        """
        Available energy that was not delivered
        There's an adjustment for subhourly reserve provision:
        1) if downward reserves are provided, they will be called upon
        occasionally, so power provision will have to decrease and additional
        curtailment will be incurred;
        2) if upward reserves are provided (energy is being curtailed),
        they will be called upon occasionally, so power provision will have to
        increase and less curtailment will be incurred
        The subhourly adjustment here is a simple linear function of reserve
        provision.
        :param mod:
        :param g:
        :param tmp:
        :return:
        """
        return mod.Capacity_MW[g, mod.period[tmp]] * mod.cap_factor[g, tmp] - \
            mod.Provide_Variable_Power_MW[g, tmp] \
            + mod.Subhourly_Variable_Generator_Curtailment_MW[g, tmp] \
            - mod.Subhourly_Variable_Generator_Energy_Delivered_MW[g, tmp]

    m.Total_Variable_Generator_Curtailment_MW = \
        Expression(m.VARIABLE_GENERATOR_OPERATIONAL_TIMEPOINTS,
                   rule=total_curtailment_expression_rule)


# Operations
def power_provision_rule(mod, g, tmp):
    """
    Power provision from variable generators is their capacity times the
    capacity factor in each timepoint minus any curtailment.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """

    return mod.Provide_Variable_Power_MW[g, tmp]


def scheduled_curtailment_rule(mod, g, tmp):
    """
    Variable generation can be dispatched down, i.e. scheduled below the
    available energy
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Scheduled_Variable_Generator_Curtailment_MW[g, tmp]


def subhourly_curtailment_rule(mod, g, tmp):
    """
    If providing downward reserves, variable generators will occasionally
    have to be dispatched down relative to their schedule, resulting in
    additional curtailment within the hour
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Subhourly_Variable_Generator_Curtailment_MW[g, tmp]


def subhourly_energy_delivered_rule(mod, g, tmp):
    """
    If providing upward reserves, variable generators will occasionally be
    dispatched up, so additional energy will be delivered within the hour
    relative to their schedule (less curtailment)
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    return mod.Subhourly_Variable_Generator_Energy_Delivered_MW[g, tmp]


def fuel_cost_rule(mod, g, tmp):
    """
    Variable generators should not have fuel use
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    raise (ValueError(
        "ERROR! Variable generators should not use fuel." + "\n" +
        "Check input data for generator '{}'".format(g) + "\n" +
        "and change its fuel to '.' (no value).")
    )


def startup_rule(mod, g, tmp):
    """
    Variable generators are never started up.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    raise(ValueError(
        "ERROR! Variable generators should not incur startup costs." + "\n" +
        "Check input data for generator '{}'".format(g) + "\n" +
        "and change its startup costs to '.' (no value).")
    )


def shutdown_rule(mod, g, tmp):
    """
    Variable generators are never started up.
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    raise(ValueError(
        "ERROR! Variable generators should not incur shutdown costs." + "\n" +
        "Check input data for generator '{}'".format(g) + "\n" +
        "and change its shutdown costs to '.' (no value).")
    )


def load_module_specific_data(mod, data_portal, scenario_directory,
                              horizon, stage):
    """
    Capacity factors vary by horizon and stage, so get inputs from appropriate
    directory
    :param mod:
    :param data_portal:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """
    data_portal.load(filename=os.path.join(scenario_directory, horizon, stage,
                                           "inputs",
                                           "variable_generator_profiles.tab"),
                     index=(mod.VARIABLE_GENERATORS, mod.TIMEPOINTS),
                     param=mod.cap_factor
                     )


def export_module_specific_results(mod, d):
    """

    :param mod:
    :param d:
    :return:
    """

    scheduled_curtailment_df = \
        make_project_time_var_df(
            mod,
            "VARIABLE_GENERATOR_OPERATIONAL_TIMEPOINTS",
            "Scheduled_Variable_Generator_Curtailment_MW",
            ["project", "timepoint"],
            "scheduled_curtailment_mw"
        )

    d.module_specific_df.append(scheduled_curtailment_df)

    subhourly_curtailment_df = \
        make_project_time_var_df(
            mod,
            "VARIABLE_GENERATOR_OPERATIONAL_TIMEPOINTS",
            "Subhourly_Variable_Generator_Curtailment_MW",
            ["project", "timepoint"],
            "subhourly_curtailment_mw"
        )

    d.module_specific_df.append(subhourly_curtailment_df)

    subhourly_energy_delivered_df = \
        make_project_time_var_df(
            mod,
            "VARIABLE_GENERATOR_OPERATIONAL_TIMEPOINTS",
            "Subhourly_Variable_Generator_Energy_Delivered_MW",
            ["project", "timepoint"],
            "subhourly_energy_delivered_mw"
        )

    d.module_specific_df.append(subhourly_energy_delivered_df)

    total_curtailment_df = \
        make_project_time_var_df(
            mod,
            "VARIABLE_GENERATOR_OPERATIONAL_TIMEPOINTS",
            "Total_Variable_Generator_Curtailment_MW",
            ["project", "timepoint"],
            "total_curtailmen_mw"
        )

    d.module_specific_df.append(total_curtailment_df)

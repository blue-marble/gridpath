#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""

"""

import csv
import os.path
import pandas as pd
from pyomo.environ import Set, Param, Var, Constraint, NonNegativeReals, \
    PercentFraction, value

from gridpath.auxiliary.dynamic_components import required_reserve_modules, \
    reserve_variable_derate_params, \
    reserve_provision_subhourly_adjustment_params
from gridpath.auxiliary.auxiliary import check_list_items_are_unique, \
    find_list_item_position


def generic_determine_dynamic_components(
        d, scenario_directory, horizon, stage,
        reserve_module,
        headroom_or_footroom_dict,
        ba_column_name,
        reserve_provision_variable_name,
        reserve_provision_derate_param_name,
        reserve_provision_subhourly_adjustment_param_name,
        reserve_balancing_area_param_name
):
    """

    :param d:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :param reserve_module:
    :param headroom_or_footroom_dict:
    :param ba_column_name:
    :param reserve_provision_variable_name:
    :param reserve_provision_derate_param_name:
    :param reserve_provision_subhourly_adjustment_param_name:
    :param reserve_balancing_area_param_name:
    :return:
    """

    getattr(d, required_reserve_modules).append(reserve_module)

    with open(os.path.join(scenario_directory, "inputs", "projects.tab"),
              "rb") as projects_file:
        projects_file_reader = csv.reader(projects_file, delimiter="\t")
        headers = projects_file_reader.next()
        # Check that columns are not repeated
        check_list_items_are_unique(headers)
        for row in projects_file_reader:
            # Get generator name; we have checked that column names are unique
            # so can expect a single-item list here and get 0th element
            generator = row[find_list_item_position(headers, "project")[0]]

            # If we have already added this generator to the head/footroom
            # variables dictionary, move on; otherwise, create the
            # dictionary item
            if generator not in getattr(d, headroom_or_footroom_dict).keys():
                getattr(d, headroom_or_footroom_dict)[generator] = list()
            # Some generators get the variables associated with
            # provision of various services (e.g. reserves) if flagged
            # Figure out which these are here based on whether a reserve zone
            # is specified ("." = no zone specified, so project does not
            # contribute to this reserve requirement)
            # The names of the reserve variables for each generator
            if row[find_list_item_position(
                    headers, ba_column_name)[0]] != ".":
                getattr(d, headroom_or_footroom_dict)[generator].append(
                    reserve_provision_variable_name)

    # The names of the headroom/footroom derate params for each reserve
    # variable
    # Will be used to get the right derate for each project providing a
    # particular reserve (derate can vary by reserve type)
    getattr(d, reserve_variable_derate_params)[
        reserve_provision_variable_name
    ] = reserve_provision_derate_param_name

    # The names of the subhourly energy adjustment params and project
    # balancing area param for each reserve variable (adjustment can vary by
    #  reserve type and by balancing area within each reserve type)
    # Will be used to get the right adjustment for each project providing a
    # particular reserve
    getattr(d, reserve_provision_subhourly_adjustment_params)[
        reserve_provision_variable_name] = \
        (reserve_provision_subhourly_adjustment_param_name,
         reserve_balancing_area_param_name)


def generic_add_model_components(m, d,
                                 reserve_projects_set,
                                 reserve_balancing_area_param,
                                 reserve_provision_derate_param,
                                 reserve_balancing_areas_set,
                                 reserve_project_operational_timepoints_set,
                                 reserve_provision_variable_name,
                                 reserve_provision_ramp_rate_limit_param,
                                 reserve_provision_ramp_rate_limit_constraint,
                                 reserve_provision_subhourly_adjustment_param):
    """
    Reserve-related components that will be used by the operational_type
    modules
    :param m:
    :param d:
    :param reserve_projects_set:
    :param reserve_balancing_area_param:
    :param reserve_provision_derate_param:
    :param reserve_balancing_areas_set:
    :param reserve_project_operational_timepoints_set:
    :param reserve_provision_variable_name:
    :param reserve_provision_ramp_rate_limit_param:
    :param reserve_provision_ramp_rate_limit_constraint:
    :param reserve_provision_subhourly_adjustment_param:
    :return:
    """

    setattr(m, reserve_projects_set, Set(within=m.PROJECTS))
    setattr(m, reserve_balancing_area_param,
            Param(getattr(m, reserve_projects_set),
                  within=getattr(m, reserve_balancing_areas_set)
                  )
            )

    setattr(m, reserve_project_operational_timepoints_set,
            Set(dimen=2,
                rule=lambda mod:
                set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                    if g in getattr(mod, reserve_projects_set))
                )
            )

    setattr(m, reserve_provision_variable_name,
            Var(getattr(m, reserve_project_operational_timepoints_set),
                within=NonNegativeReals
                )
            )

    # Headroom/footroom derate -- this is how much extra footroom or
    # headroom must be available in order to provide 1 unit of up or down
    # reserves respectively
    # For example, if the derate is 0.5, the required headroom for providing
    # upward reserves is 1/0.5=2 -- twice the reserve that can be provided
    # Defaults to 1 if not specified
    # This param is used by the operational_type modules
    setattr(m, reserve_provision_derate_param,
            Param(getattr(m, reserve_projects_set),
                  within=PercentFraction, default=1)
            )

    # Ramp rate reserve limit (response time reserve limit)
    # Some reserve products may require that generators respond within a
    # certain amount of time, e.g. 1 minute, 10 minutes, etc.
    # The maximum amount of reserves that a generator can provide is
    # therefore limited by its ramp rate, e.g. if it can ramp up 60 MW an hour,
    # then it will only be able to provide 10 MW of upward reserve for a
    # reserve product with a 10-minute response requirement \
    # Here, this derate param is specified as a fraction of generator capacity
    # Defaults to 1 if not specified
    setattr(m, reserve_provision_ramp_rate_limit_param,
            Param(getattr(m, reserve_projects_set),
                  within=PercentFraction, default=1)
            )

    def reserve_provision_ramp_rate_limit_rule(mod, p, tmp):
        """
        Don't create constraint if the project can ramp its full capacity in
        the timepoint
        :param mod:
        :param p:
        :param tmp:
        :return:
        """
        if getattr(m, reserve_provision_ramp_rate_limit_param) == 1:
            return Constraint.Skip
        else:
            return getattr(mod, reserve_provision_variable_name)[p, tmp] <= \
                getattr(mod, reserve_provision_ramp_rate_limit_param)[p] \
                * mod.Capacity_MW[p, mod.period[tmp]]
    setattr(m, reserve_provision_ramp_rate_limit_constraint,
            Constraint(
                getattr(m, reserve_project_operational_timepoints_set),
                rule=reserve_provision_ramp_rate_limit_rule
            )
            )

    # Energy adjustment from subhourly reserve provision
    # (e.g. for storage state of charge or how much variable RPS energy is
    # delivered because of subhourly reserve provision)
    # This is an optional param, which will default to 0 if not specified
    # This param is used by the operational_type modules
    setattr(m, reserve_provision_subhourly_adjustment_param,
            Param(getattr(m, reserve_balancing_areas_set),
                  within=PercentFraction, default=0)
            )


def generic_load_model_data(
        m, d, data_portal, scenario_directory, horizon, stage,
        ba_column_name,
        derate_column_name,
        ramp_rate_limit_column_name,
        reserve_balancing_area_param,
        reserve_provision_derate_param,
        reserve_provision_ramp_rate_limit_param,
        reserve_projects_set,
        reserve_provision_subhourly_adjustment_param,
        reserve_balancing_areas_input_file):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :param ba_column_name:
    :param derate_column_name:
    :param ramp_rate_limit_column_name:
    :param reserve_balancing_area_param:
    :param reserve_provision_derate_param:
    :param reserve_provision_ramp_rate_limit_param:
    :param reserve_projects_set:
    :param reserve_provision_subhourly_adjustment_param:
    :param reserve_balancing_areas_input_file:
    :return:
    """

    # Import reserve provision headroom/footroom de-rate parameter only if
    # column is present
    # Otherwise, the de-rate param goes to its default of 1
    # Import reserve provision ramp rate limit parameter only if
    # column is present
    # Otherwise, the ramp rate limit param goes to its default of 1
    columns_to_import = ("project", ba_column_name,)
    params_to_import = (getattr(m, reserve_balancing_area_param),)
    projects_file_header = pd.read_csv(os.path.join(scenario_directory,
                                                    "inputs", "projects.tab"),
                                       sep="\t", header=None, nrows=1
                                       ).values[0]
    if derate_column_name in projects_file_header:
        columns_to_import += (derate_column_name, )
        params_to_import += (getattr(m, reserve_provision_derate_param),)
    else:
        pass

    if ramp_rate_limit_column_name in projects_file_header:
        columns_to_import += (ramp_rate_limit_column_name, )
        params_to_import += (getattr(m,
                                     reserve_provision_ramp_rate_limit_param),)
    else:
        pass

    # Load the needed data
    data_portal.load(filename=os.path.join(scenario_directory,
                                           "inputs", "projects.tab"),
                     select=columns_to_import,
                     param=params_to_import
                     )

    data_portal.data()[reserve_projects_set] = {
        None: data_portal.data()[reserve_balancing_area_param].keys()
    }

    # Load reserve provision subhourly energy adjustment (e.g. for storage
    # state of charge adjustment or delivered variable RPS energy adjustment)
    # if specified; otherwise it will default to 0
    ba_file_header = pd.read_csv(os.path.join(
        scenario_directory, "inputs", reserve_balancing_areas_input_file),
        sep="\t", header=None, nrows=1).values[0]

    if "reserve_provision_subhourly_adjustment" in ba_file_header:
        data_portal.load(filename=os.path.join(
            scenario_directory, "inputs", reserve_balancing_areas_input_file),
            select=("balancing_area",
                    "reserve_provision_subhourly_adjustment"),
            param=reserve_provision_subhourly_adjustment_param
                         )


def generic_export_module_specific_results(
        m, d, scenario_directory, horizon, stage,
        module_name,
        reserve_project_operational_timepoints_set,
        reserve_provision_variable_name):
    """
    Export project-level reserves results
    :param m:
    :param d:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :param module_name:
    :param reserve_project_operational_timepoints_set:
    :param reserve_provision_variable_name:
    :return:
    """
    with open(os.path.join(scenario_directory, horizon, stage, "results",
                           "reserves_provision_" + module_name + ".csv"),
              "wb") as f:
        writer = csv.writer(f)
        writer.writerow(["project", "period", "horizon", "timepoint",
                         "horizon_weight", "number_of_hours_in_timepoint",
                         "reserve_provision_mw"])
        for (p, tmp) in getattr(m, reserve_project_operational_timepoints_set):
            writer.writerow([
                p,
                m.period[tmp],
                m.horizon[tmp],
                tmp,
                m.horizon_weight[m.horizon[tmp]],
                m.number_of_hours_in_timepoint[tmp],
                value(getattr(m, reserve_provision_variable_name)[p, tmp])
            ])

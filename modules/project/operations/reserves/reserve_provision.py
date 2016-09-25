#!/usr/bin/env python

"""
Add variables for downward load-following reserves
"""

from csv import reader
import os.path
from pyomo.environ import Set, Param, Var, NonNegativeReals

from modules.auxiliary.auxiliary import check_list_items_are_unique, \
    find_list_item_position, make_project_time_var_df


def generic_determine_dynamic_components(d, scenario_directory, horizon, stage,
                                         reserve_module,
                                         headroom_or_footroom_dict,
                                         column_name,
                                         reserve_provision_variable_name):
    """

    :param d:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :param reserve_module:
    :param headroom_or_footroom_dict:
    :param column_name:
    :param reserve_provision_variable_name:
    :return:
    """

    d.required_reserve_modules.append(reserve_module)

    with open(os.path.join(scenario_directory, "inputs", "projects.tab"),
              "rb") as projects_file:
        projects_file_reader = reader(projects_file, delimiter="\t")
        headers = projects_file_reader.next()
        # Check that columns are not repeated
        check_list_items_are_unique(headers)
        for row in projects_file_reader:
            # Get generator name; we have checked that columns names are unique
            # so can expect a single-item list here and get 0th element
            generator = row[find_list_item_position(headers, "project")[0]]

            # If we have already added this generator to the footroom variables
            # dictionary, move on; otherwise, create the dictionary item
            if generator not in d.footroom_variables.keys():
                getattr(d, headroom_or_footroom_dict)[generator] = list()
            # In addition, some generators get the variables associated with
            # provision of other services (e.g. reserves) if flagged
            # Figure out which these are here based on whether a reserve zone
            # is specified ("." = no zone specified, so project does not
            # contribute to this reserve requirement)
            # Generators that can provide downward load-following reserves
            if row[find_list_item_position(
                    headers, column_name)[0]] != ".":
                getattr(d, headroom_or_footroom_dict)[generator].append(
                    reserve_provision_variable_name)


def generic_add_model_components(m, d, scenario_directory, horizon, stage,
                                 reserve_projects_set,
                                 reserve_balancing_area_param,
                                 reserve_balancing_areas_set,
                                 reserve_project_operational_timepoints_set,
                                 reserve_provision_variable_name):
    """

    :param m:
    :param d:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :param reserve_projects_set:
    :param reserve_balancing_area_param:
    :param reserve_balancing_areas_set:
    :param reserve_project_operational_timepoints_set:
    :param reserve_provision_variable_name:
    :return:
    """

    # TODO: limit to BA set when implemented
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


def generic_load_model_data(
        m, data_portal, scenario_directory, horizon, stage,
        column_name,
        reserve_balancing_area_param,
        reserve_projects_set):
    """

    :param m:
    :param data_portal:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :param column_name:
    :param reserve_balancing_area_param:
    :param reserve_projects_set:
    :return:
    """

    data_portal.load(filename=os.path.join(scenario_directory,
                                           "inputs", "projects.tab"),
                     select=("project", column_name),
                     param=(getattr(m, reserve_balancing_area_param),)
                     )

    data_portal.data()[reserve_projects_set] = {
        None: data_portal.data()[reserve_balancing_area_param].keys()
    }


def generic_export_module_specific_results(
        m, d,
        reserve_project_operational_timepoints_set,
        reserve_provision_variable_name,
        column_name):
    """
    Export project-level reserves results
    :param m:
    :param d:
    :param reserve_project_operational_timepoints_set:
    :param reserve_provision_variable_name:
    :param column_name:
    :return:
    """
    reserves_dataframe = \
        make_project_time_var_df(
            m,
            reserve_project_operational_timepoints_set,
            reserve_provision_variable_name,
            ["project", "timepoint"],
            column_name
        )
    d.module_specific_df.append(reserves_dataframe)

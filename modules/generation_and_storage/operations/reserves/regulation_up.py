#!/usr/bin/env python

"""
Add variables for upward load-following reserves
"""

from csv import reader
import os.path
from pyomo.environ import Set, Param, Var, NonNegativeReals

from modules.auxiliary.auxiliary import check_list_items_are_unique, \
    find_list_item_position, make_resource_time_var_df


def determine_dynamic_components(d, scenario_directory, horizon, stage):
    """

    :param d:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """

    d.required_reserve_modules.append("regulation_up")

    with open(os.path.join(scenario_directory, "inputs", "resources.tab"),
              "rb") as generation_capacity_file:
        resources_file_reader = reader(generation_capacity_file, delimiter="\t")
        headers = resources_file_reader.next()
        # Check that columns are not repeated
        check_list_items_are_unique(headers)
        for row in resources_file_reader:
            # Get generator name; we have checked that columns names are unique
            # so can expect a single-item list here and get 0th element
            generator = row[find_list_item_position(headers, "RESOURCES")[0]]

            # If we have already added this generator to the headroom variables
            # dictionary, move on; otherwise, create the dictionary item
            if generator not in d.headroom_variables.keys():
                d.headroom_variables[generator] = list()
            # In addition, some generators get the variables associated with
            # provision of other services (e.g. reserves) if flagged
            # Figure out which these are here based on whether a reserve zone
            # is specified ("." = no zone specified, so resource does not
            # contribute to this reserve requirement)
            # Generators that can provide downward load-following reserves
            if row[find_list_item_position(
                    headers, "regulation_up_zone")[0]] != ".":
                d.headroom_variables[generator].append(
                    "Provide_Regulation_Up_MW")


def add_model_components(m, d, scenario_directory, horizon, stage):
    """

    :param m:
    :param d:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """

    m.REGULATION_UP_RESOURCES = Set(within=m.RESOURCES)
    m.regulation_up_zone = Param(m.REGULATION_UP_RESOURCES)

    m.REGULATION_UP_RESOURCE_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.RESOURCE_OPERATIONAL_TIMEPOINTS
                if g in mod.REGULATION_UP_RESOURCES))

    m.Provide_Regulation_Up_MW = Var(
        m.REGULATION_UP_RESOURCE_OPERATIONAL_TIMEPOINTS,
        within=NonNegativeReals)


def load_model_data(m, data_portal, scenario_directory, horizon, stage):
    """

    :param m:
    :param data_portal:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """

    data_portal.load(filename=os.path.join(scenario_directory,
                                           "inputs", "resources.tab"),
                     select=("RESOURCES", "regulation_up_zone"),
                     param=(m.regulation_up_zone,)
                     )

    data_portal.data()['REGULATION_UP_RESOURCES'] = {
        None: data_portal.data()['regulation_up_zone'].keys()
    }


def export_module_specific_results(m, d):
    """
    Export project-level results for upward load-following
    :param m:
    :param d:
    :return:
    """

    regulation_up_df = make_resource_time_var_df(
        m,
        "REGULATION_UP_RESOURCE_OPERATIONAL_TIMEPOINTS",
        "Provide_Regulation_Up_MW",
        ["resource", "timepoint"],
        "regulation_up_mw"
    )

    d.module_specific_df.append(regulation_up_df)

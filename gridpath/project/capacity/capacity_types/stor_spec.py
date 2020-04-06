#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This capacity type describes the power (i.e. charging and discharging
capacity) and energy capacity (i.e. duration) of storage projects that are
available to the optimization without having to incur an investment cost.
For example, it can be applied to existing storage projects or to
storage projects that will be built in the future and whose capital costs we
want to ignore (in the objective function).

It is not required to specify a capacity for all periods, i.e. a project can
be operational in some periods but not in others with no restriction on the
order and combination of periods. The user may specify a fixed O&M cost for
specified-storage projects, but this cost will be a fixed number in the
objective function and will therefore not affect any of the optimization
decisions.

"""

import csv
import os.path
from pyomo.environ import Set, Param, NonNegativeReals

from gridpath.auxiliary.dynamic_components import \
    capacity_type_operational_period_sets, \
    storage_only_capacity_type_operational_period_sets


def add_module_specific_components(m, d):
    """
     The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`STOR_SPEC_OPR_PRDS`                                            |
    |                                                                         |
    | Two-dimensional set of project-period combinations that helps describe  |
    | the project capacity available in a given period. This set is added to  |
    | the list of sets to join to get the final :code:`PRJ_OPR_PRDS` set      |
    | defined in **gridpath.project.capacity.capacity**.                      |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`stor_spec_power_capacity_mw`                                   |
    | | *Defined over*: :code:`STOR_SPEC_OPR_PRDS`                            |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The storage project's specified power capacity (in MW) in each          |
    | operational period.                                                     |
    +-------------------------------------------------------------------------+
    | | :code:`stor_spec_energy_capacity_mwh`                                 |
    | | *Defined over*: :code:`STOR_SPEC_OPR_PRDS`                            |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The storage project's specified energy capacity (in MWh) in each        |
    | operational period.                                                     |
    +-------------------------------------------------------------------------+
    | | :code:`stor_spec_fixed_cost_per_mw_yr`                                |
    | | *Defined over*: :code:`STOR_SPEC_OPR_PRDS`                            |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The storage project's fixed cost for the power components (in $ per     |
    | MW-yr.) in each operational period. This cost will be added to the      |
    | objective function but will not affect optimization decisions.          |
    +-------------------------------------------------------------------------+
    | | :code:`stor_spec_fixed_cost_per_mwh_yr`                               |
    | | *Defined over*: :code:`STOR_SPEC_OPR_PRDS`                            |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The storage project's fixed cost for the energy components (in $ per    |
    | MWh-yr.) in each operational period. This cost will be added to the     |
    | objective function but will not affect optimization decisions.          |
    +-------------------------------------------------------------------------+

    """

    # Sets
    ###########################################################################

    m.STOR_SPEC_OPR_PRDS = Set(dimen=2)

    # Required Params
    ###########################################################################

    m.stor_spec_power_capacity_mw = Param(
        m.STOR_SPEC_OPR_PRDS,
        within=NonNegativeReals
    )

    m.stor_spec_energy_capacity_mwh = Param(
        m.STOR_SPEC_OPR_PRDS,
        within=NonNegativeReals
    )

    m.stor_spec_fixed_cost_per_mw_yr = Param(
        m.STOR_SPEC_OPR_PRDS,
        within=NonNegativeReals
    )

    m.stor_spec_fixed_cost_per_mwh_yr = Param(
        m.STOR_SPEC_OPR_PRDS,
        within=NonNegativeReals
    )

    # Dynamic Components
    ###########################################################################

    # Add to list of sets we'll join to get the final
    # PRJ_OPR_PRDS set
    getattr(d, capacity_type_operational_period_sets).append(
        "STOR_SPEC_OPR_PRDS",
    )

    # Add to list of sets we'll join to get the final
    # STOR_OPR_PRDS set
    getattr(d, storage_only_capacity_type_operational_period_sets).append(
        "STOR_SPEC_OPR_PRDS",
    )


# Capacity Type Methods
###############################################################################

def capacity_rule(mod, g, p):
    """
    The power capacity of projects of the *stor_spec* capacity type is a
    pre-specified number for each of the project's operational periods.
    """
    return mod.stor_spec_power_capacity_mw[g, p]


def energy_capacity_rule(mod, g, p):
    """
    The energy capacity of projects of the *stor_spec* capacity type is a
    pre-specified number for each of the project's operational periods.
    """
    return mod.stor_spec_energy_capacity_mwh[g, p]


def capacity_cost_rule(mod, g, p):
    """
    The capacity cost of projects of the *stor_spec* capacity type is a
    pre-specified number equal to the power capacity times the per-mw fixed
    cost plus the energy capacity times the per-mwh fixed cost for each of
    the project's operational periods.
    """
    return mod.stor_spec_power_capacity_mw[g, p] \
        * mod.stor_spec_fixed_cost_per_mw_yr[g, p] \
        + mod.stor_spec_energy_capacity_mwh[g, p] \
        * mod.stor_spec_fixed_cost_per_mwh_yr[g, p]


# Input-Output
###############################################################################

def load_module_specific_data(
        m, data_portal, scenario_directory, subproblem, stage
):
    data_portal.load(
        filename=os.path.join(scenario_directory, subproblem, stage, "inputs",
                              "storage_specified_capacities.tab"),
        index=m.STOR_SPEC_OPR_PRDS,
        select=("project", "period",
                "storage_specified_power_capacity_mw",
                "storage_specified_energy_capacity_mwh",
                "storage_specified_fixed_cost_per_mw_yr",
                "storage_specified_fixed_cost_per_mwh_yr"),
        param=(m.stor_spec_power_capacity_mw,
               m.stor_spec_energy_capacity_mwh,
               m.stor_spec_fixed_cost_per_mw_yr,
               m.stor_spec_fixed_cost_per_mwh_yr)
    )


# Database
###############################################################################

def get_module_specific_inputs_from_database(
        subscenarios, subproblem, stage, conn
):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    c = conn.cursor()
    stor_capacities = c.execute(
        """SELECT project, period, specified_capacity_mw,
        specified_capacity_mwh,
        annual_fixed_cost_per_mw_year, annual_fixed_cost_per_mwh_year
        FROM inputs_project_portfolios
        CROSS JOIN
        (SELECT period
        FROM inputs_temporal_periods
        WHERE temporal_scenario_id = {}) as relevant_periods
        INNER JOIN
        (SELECT project, period, specified_capacity_mw,
        specified_capacity_mwh
        FROM inputs_project_specified_capacity
        WHERE project_specified_capacity_scenario_id = {}) as capacity
        USING (project, period)
        LEFT OUTER JOIN
        (SELECT project, period,
        annual_fixed_cost_per_kw_year * 1000 AS annual_fixed_cost_per_mw_year,
        annual_fixed_cost_per_kwh_year * 1000 AS annual_fixed_cost_per_mwh_year
        FROM inputs_project_specified_fixed_cost
        WHERE project_specified_fixed_cost_scenario_id = {}) as fixed_om
        USING (project, period)
        WHERE project_portfolio_scenario_id = {}
        AND capacity_type = 
        'stor_spec';""".format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subscenarios.PROJECT_SPECIFIED_CAPACITY_SCENARIO_ID,
            subscenarios.PROJECT_SPECIFIED_FIXED_COST_SCENARIO_ID,
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID
        )
    )
    return stor_capacities


def write_module_specific_model_inputs(
        inputs_directory, subscenarios, subproblem, stage, conn
):
    """
    Get inputs from database and write out the model input
    storage_specified_capacities.tab file
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    stor_capacities = get_module_specific_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    with open(os.path.join(inputs_directory,
                           "storage_specified_capacities.tab"),
              "w", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(
            ["project", "period",
             "storage_specified_power_capacity_mw",
             "storage_specified_energy_capacity_mwh",
             "storage_specified_fixed_cost_per_mw_yr",
             "storage_specified_fixed_cost_per_mwh_yr"]
        )

        for row in stor_capacities:
            writer.writerow(row)


# Validation
###############################################################################

def validate_module_specific_inputs(subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    pass
    # Validation to be added
    # stor_capacities = get_module_specific_inputs_from_database(
    #     subscenarios, subproblem, stage, conn)

    # do validation
    # make sure existing capacity is a postive number
    # make sure annual fixed costs are positive


# Copyright 2016-2023 Blue Marble Analytics LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This capacity type describes fuel production projects that can be built by the
optimization at a cost. Investment decisions are made separately for the
project's fuel production, fuel release, and fuel storage capacity, therefore
endogenously determining the sizing of the facility. The decisions are
linearized.

Like with new-build generation, capacity costs added to the objective
function include the annualized capital cost and the annual fixed O&M cost.
"""

import csv
import os.path
from pathlib import Path

import pandas as pd
from pyomo.environ import (
    Set,
    Param,
    Var,
    Expression,
    NonNegativeReals,
    value,
)

from gridpath.auxiliary.auxiliary import cursor_to_df
from gridpath.auxiliary.dynamic_components import (
    capacity_type_operational_period_sets,
    capacity_type_financial_period_sets,
)
from gridpath.auxiliary.validations import (
    write_validation_to_database,
    validate_values,
    get_expected_dtypes,
    get_projects,
    validate_dtypes,
    validate_idxs,
)
from gridpath.common_functions import create_results_df
from gridpath.project.capacity.capacity_types.common_methods import (
    relevant_periods_by_project_vintage,
    project_relevant_periods,
    project_vintages_relevant_in_period,
    read_results_file_generic,
    write_summary_results_generic,
    get_units,
)


def add_model_components(
    m,
    d,
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`FUEL_PROD_NEW`                                                 |
    |                                                                         |
    | The list of projects of capacity type :code:`fuel_prod_new`.            |
    +-------------------------------------------------------------------------+
    | | :code:`FUEL_PROD_NEW_VNTS`                                            |
    |                                                                         |
    | A two-dimensional set of project-vintage combinations to describe the   |
    | periods in time when storage capacity/energy can be built in the        |
    | optimization.                                                           |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`fuel_prod_new_operational_lifetime_yrs`                        |
    | | *Defined over*: :code:`FUEL_PROD_NEW_VNTS`                            |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's operational lifetime, i.e. how long project               |
    | capacity/energy of a particular vintage remains operational and can be  |
    | used.                                                                   |
    +-------------------------------------------------------------------------+
    | | :code:`fuel_prod_new_prod_fixed_cost_fuelunitperhour_yr`              |
    | | *Defined over*: :code:`FUEL_PROD_NEW_VNTS`                            |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's fixed cost incurred while the fuel production capacity is |
    | operational.
    +-------------------------------------------------------------------------+
    | | :code:`fuel_prod_new_release_fixed_cost_fuelunitperhour_yr`           |
    | | *Defined over*: :code:`FUEL_PROD_NEW_VNTS`                            |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's fixed cost incurred while the fuel release capacity is    |
    | operational.                                                            |
    +-------------------------------------------------------------------------+
    | | :code:`fuel_prod_new_storage_fixed_cost_fuelunit_yr`                  |
    | | *Defined over*: :code:`FUEL_PROD_NEW_VNTS`                            |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's cost to build new fuel storage capacity in annualized     |
    | real dollars per FuelUnit (per FuelUnit-year).                          |
    +-------------------------------------------------------------------------+
    | | :code:`fuel_prod_new_financial_lifetime_yrs`                          |
    | | *Defined over*: :code:`FUEL_PROD_NEW_VNTS`                            |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's financial lifetime, i.e. how the annual payments for the  |
    | project capacity of a particular vintage must be made.                  |
    +-------------------------------------------------------------------------+
    | | :code:`fuel_prod_new_prod_cost_fuelunitperhour_yr`                    |
    | | *Defined over*: :code:`FUEL_PROD_NEW_VNTS`                            |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's cost to build new fuel production capacity in annualized  |
    | real dollars per FuelUnitPerHour (per FuelUnitPerHour-year)             |
    +-------------------------------------------------------------------------+
    | | :code:`fuel_prod_new_release_cost_fuelunitperhour_yr`                 |
    | | *Defined over*: :code:`FUEL_PROD_NEW_VNTS`                            |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's cost to build new fuel release capacity in annualized     |
    | real dollars per FuelUnitPerHour (per FuelUnitPerHour-year).            |
    +-------------------------------------------------------------------------+
    | | :code:`fuel_prod_new_storage_cost_fuelunit_yr`                        |
    | | *Defined over*: :code:`FUEL_PROD_NEW_VNTS`                            |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's cost to build new fuel storage capacity in annualized     |
    | real dollars per FuelUnit (per FuelUnit-year).                          |
    +-------------------------------------------------------------------------+

    .. note:: The cost input to the model is an annualized cost per unit
        capacity. This annualized cost is incurred in each period of the study
        (and multiplied by the number of years the period represents) for
        the duration of the project's "financial" lifetime. It is up to the
        user to ensure that the variousl lifetime and cost parameters are consistent
        with one another and with the period length (projects are operational
        and incur capital costs only if the operational and financial lifetimes last
        through the end of a period respectively.

    |

    +-------------------------------------------------------------------------+
    | Derived Sets                                                            |
    +=========================================================================+
    | | :code:`OPR_PRDS_BY_FUEL_PROD_NEW_VINTAGE`                             |
    | | *Defined over*: :code:`FUEL_PROD_NEW_VNTS`                            |
    |                                                                         |
    | Indexed set that describes the operational periods for each possible    |
    | project-vintage combination, based on the                               |
    | :code:`fuel_prod_new_operational_lifetime_yrs`. For instance, capacity  |
    | of 2020 vintage with lifetime of 30 years will be assumed operational   |
    | starting Jan 1, 2020 and through Dec 31, 2049, but will *not* be        |
    | operational in 2050.                                                    |
    +-------------------------------------------------------------------------+
    | | :code:`FUEL_PROD_NEW_OPR_PRDS`                                        |
    |                                                                         |
    | Two-dimensional set that includes the periods when project capacity of  |
    | any vintage *could* be operational if built. This set is added to the   |
    | list of sets to join to get the final :code:`PRJ_OPR_PRDS` set defined  |
    | in **gridpath.project.capacity.capacity**.                              |
    +-------------------------------------------------------------------------+
    | | :code:`FUEL_PROD_NEW_VNTS_OPR_IN_PRD`                                 |
    | | *Defined over*: :code:`PERIODS`                                       |
    |                                                                         |
    | Indexed set that describes the project-vintages that could be           |
    | operational in each period based on the                                 |
    | :code:`fuel_prod_new_operational_lifetime_yrs`.                         |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Variables                                                               |
    +=========================================================================+
    | | :code:`FuelProdNew_Build_Prod_Cap_FuelUnitPerHour`                    |
    | | *Defined over*: :code:`FUEL_PROD_NEW_VNTS`                            |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | Determines how much fuel production capacity (in FuelUnitPerHour) of    |
    | each possible vintage is built at each fuel_prod_new project.           |
    +-------------------------------------------------------------------------+
    | | :code:`FuelProdNew_Build_Rel_Cap_FuelUnitPerHour`                     |
    | | *Defined over*: :code:`FUEL_PROD_NEW_VNTS`                            |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | Determines how much fuel release capacity (in FuelUnitPerHour) of each  |
    | possible vintage is built at each fuel_prod_new project.                |
    +-------------------------------------------------------------------------+
    | | :code:`FuelProdNew_Build_Stor_Cap_FuelUnit`                    |
    | | *Defined over*: :code:`FUEL_PROD_NEW_VNTS`                            |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | Determines how much fuel storage capacity (in FuelUnits) of each        |
    | possible vintage is built at each fuel_prod_new project.                |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Expressions                                                             |
    +=========================================================================+
    | | :code:`FuelProdNew_Prod_Capacity_FuelUnitPerHour`                     |
    | | *Defined over*: :code:`FUEL_PROD_NEW_OPR_PRDS`                        |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The fuel production capacity of a new project (in FuelUnitPerHour) in a |
    | given operational period is equal to the sum of all capacity-build of   |
    | vintages operational in that period.                                    |
    +-------------------------------------------------------------------------+
    | | :code:`FuelProdNew_Rel_Capacity_FuelUnitPerHour`                      |
    | | *Defined over*: :code:`FUEL_PROD_NEW_OPR_PRDS`                        |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The fuel release capacity of a new project (in FuelUnitPerHour) in a    |
    | given operational period is equal to the sum of all capacity-build of   |
    | vintages operational in that period.                                    |
    +-------------------------------------------------------------------------+
    | | :code:`FuelProdNew_Stor_Capacity_FuelUnitPerHour`                     |
    | | *Defined over*: :code:`FUEL_PROD_NEW_OPR_PRDS`                        |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The fuel storage capacity of a new project (in FuelUnits) in a given    |
    | operational period is equal to the sum of all capacity-build of         |
    | vintages operational in that period.                                    |
    +-------------------------------------------------------------------------+

    """

    # Sets
    ###########################################################################

    m.FUEL_PROD_NEW = Set()

    m.FUEL_PROD_NEW_VNTS = Set(dimen=2, within=m.FUEL_PROD_NEW * m.PERIODS)

    # Required Params
    ###########################################################################

    m.fuel_prod_new_operational_lifetime_yrs = Param(
        m.FUEL_PROD_NEW_VNTS, within=NonNegativeReals
    )

    m.fuel_prod_new_prod_fixed_cost_fuelunitperhour_yr = Param(
        m.FUEL_PROD_NEW_VNTS, within=NonNegativeReals
    )

    m.fuel_prod_new_release_fixed_cost_fuelunitperhour_yr = Param(
        m.FUEL_PROD_NEW_VNTS, within=NonNegativeReals
    )

    m.fuel_prod_new_storage_fixed_cost_fuelunit_yr = Param(
        m.FUEL_PROD_NEW_VNTS, within=NonNegativeReals
    )

    m.fuel_prod_new_financial_lifetime_yrs = Param(
        m.FUEL_PROD_NEW_VNTS, within=NonNegativeReals
    )

    m.fuel_prod_new_prod_cost_fuelunitperhour_yr = Param(
        m.FUEL_PROD_NEW_VNTS, within=NonNegativeReals
    )

    m.fuel_prod_new_release_cost_fuelunitperhour_yr = Param(
        m.FUEL_PROD_NEW_VNTS, within=NonNegativeReals
    )

    m.fuel_prod_new_storage_cost_fuelunit_yr = Param(
        m.FUEL_PROD_NEW_VNTS, within=NonNegativeReals
    )

    # Derived Sets
    ###########################################################################

    m.OPR_PRDS_BY_FUEL_PROD_NEW_VINTAGE = Set(
        m.FUEL_PROD_NEW_VNTS, initialize=operational_periods_by_vintage
    )

    m.FUEL_PROD_NEW_OPR_PRDS = Set(
        dimen=2, initialize=fuel_prod_new_operational_periods
    )

    m.FUEL_PROD_NEW_VNTS_OPR_IN_PRD = Set(
        m.PERIODS, dimen=2, initialize=fuel_prod_new_vintages_operational_in_period
    )

    m.FIN_PRDS_BY_FUEL_PROD_NEW_VINTAGE = Set(
        m.FUEL_PROD_NEW_VNTS, initialize=financial_periods_by_vintage
    )

    m.FUEL_PROD_NEW_FIN_PRDS = Set(dimen=2, initialize=fuel_prod_new_financial_periods)

    m.FUEL_PROD_NEW_VNTS_FIN_IN_PRD = Set(
        m.PERIODS, dimen=2, initialize=fuel_prod_new_vintages_financial_in_period
    )

    # Variable
    ###########################################################################

    m.FuelProdNew_Build_Prod_Cap_FuelUnitPerHour = Var(
        m.FUEL_PROD_NEW_VNTS, within=NonNegativeReals
    )

    m.FuelProdNew_Build_Rel_Cap_FuelUnitPerHour = Var(
        m.FUEL_PROD_NEW_VNTS, within=NonNegativeReals
    )

    m.FuelProdNew_Build_Stor_Cap_FuelUnit = Var(
        m.FUEL_PROD_NEW_VNTS, within=NonNegativeReals
    )

    # Expressions
    ###########################################################################

    m.FuelProdNew_Prod_Capacity_FuelUnitPerHour = Expression(
        m.FUEL_PROD_NEW_OPR_PRDS, rule=prod_cap_rule
    )

    m.FuelProdNew_Rel_Capacity_FuelUnitPerHour = Expression(
        m.FUEL_PROD_NEW_OPR_PRDS, rule=rel_cap_rule
    )

    m.FuelProdNew_Stor_Capacity_FuelUnitPerHour = Expression(
        m.FUEL_PROD_NEW_OPR_PRDS, rule=storage_rule
    )

    # Dynamic Components
    ###########################################################################

    # Add to list of sets we'll join to get the final
    # PRJ_OPR_PRDS set
    getattr(d, capacity_type_operational_period_sets).append(
        "FUEL_PROD_NEW_OPR_PRDS",
    )

    # Add to list of sets we'll join to get the final
    # PRJ_FIN_PRDS set
    getattr(d, capacity_type_financial_period_sets).append(
        "FUEL_PROD_NEW_FIN_PRDS",
    )


# Set Rules
###############################################################################


def operational_periods_by_vintage(mod, prj, v):
    return relevant_periods_by_project_vintage(
        periods=getattr(mod, "PERIODS"),
        period_start_year=getattr(mod, "period_start_year"),
        period_end_year=getattr(mod, "period_end_year"),
        vintage=v,
        lifetime_yrs=mod.fuel_prod_new_operational_lifetime_yrs[prj, v],
    )


def fuel_prod_new_operational_periods(mod):
    return project_relevant_periods(
        project_vintages_set=mod.FUEL_PROD_NEW_VNTS,
        relevant_periods_by_project_vintage_set=mod.OPR_PRDS_BY_FUEL_PROD_NEW_VINTAGE,
    )


def fuel_prod_new_vintages_operational_in_period(mod, p):
    return project_vintages_relevant_in_period(
        project_vintage_set=mod.FUEL_PROD_NEW_VNTS,
        relevant_periods_by_project_vintage_set=mod.OPR_PRDS_BY_FUEL_PROD_NEW_VINTAGE,
        period=p,
    )


def financial_periods_by_vintage(mod, prj, v):
    return relevant_periods_by_project_vintage(
        periods=getattr(mod, "PERIODS"),
        period_start_year=getattr(mod, "period_start_year"),
        period_end_year=getattr(mod, "period_end_year"),
        vintage=v,
        lifetime_yrs=mod.fuel_prod_new_financial_lifetime_yrs[prj, v],
    )


def fuel_prod_new_financial_periods(mod):
    return project_relevant_periods(
        project_vintages_set=mod.FUEL_PROD_NEW_VNTS,
        relevant_periods_by_project_vintage_set=mod.FIN_PRDS_BY_FUEL_PROD_NEW_VINTAGE,
    )


def fuel_prod_new_vintages_financial_in_period(mod, p):
    return project_vintages_relevant_in_period(
        project_vintage_set=mod.FUEL_PROD_NEW_VNTS,
        relevant_periods_by_project_vintage_set=mod.FIN_PRDS_BY_FUEL_PROD_NEW_VINTAGE,
        period=p,
    )


# Expression Rules
###############################################################################


def prod_cap_rule(mod, prj, prd):
    """
    **Expression Name**: FuelProdNew_Prod_Capacity_FuelUnitPerHour
    **Defined Over**: FUEL_PROD_NEW_OPR_PRDS

    The fuel production capacity of a new  project in a given operational
    period for is equal to the sum of all production capacity-build of vintages
    operational in that period.

    This expression is not defined for a new project's non-operational periods. E.g.
    if we were allowed to build capacity in 2020 and 2030, and the project had a 15
    year lifetime, in 2020 we'd take 2020 capacity-build only, in 2030, we'd take the sum
    of 2020 capacity-build and 2030 capacity-build, in 2040, we'd take 2030
    capacity-build only, and in 2050, the capacity would be undefined (i.e.
    0 for the purposes of the objective function).
    """
    return sum(
        mod.FuelProdNew_Build_Prod_Cap_FuelUnitPerHour[prj, v]
        for (project, v) in mod.FUEL_PROD_NEW_VNTS_OPR_IN_PRD[prd]
        if project == prj
    )


def rel_cap_rule(mod, prj, prd):
    """
    **Expression Name**: FuelProdNew_Rel_Capacity_FuelUnitPerHour
    **Defined Over**: FUEL_PROD_NEW_OPR_PRDS

    The fuel release capacity of a new  project in a given operational period
    for is equal to the sum of all release capacity-build of vintages operational in
    that period.

    This expression is not defined for a new project's non-operational periods. E.g.
    if we were allowed to build capacity in 2020 and 2030, and the project had a 15
    year lifetime, in 2020 we'd take 2020 capacity-build only, in 2030, we'd take the sum
    of 2020 capacity-build and 2030 capacity-build, in 2040, we'd take 2030
    capacity-build only, and in 2050, the capacity would be undefined (i.e.
    0 for the purposes of the objective function).
    """
    return sum(
        mod.FuelProdNew_Build_Rel_Cap_FuelUnitPerHour[prj, v]
        for (project, v) in mod.FUEL_PROD_NEW_VNTS_OPR_IN_PRD[prd]
        if project == prj
    )


def storage_rule(mod, prj, prd):
    """
    **Expression Name**: FuelProdNew_Energy_Capacity_MWh
    **Defined Over**: FUEL_PROD_NEW_OPR_PRDS

    The storage capacity of a new  project in a given operational period is equal to
    the sum of all storage capacity-build of vintages operational in that period.

    This expression is not defined for a new project' non-operational periods (i.e.
    it's 0). E.g. if we were allowed to build storage capacity in 2020 and 2030,
    and the project had a 15 year lifetime, in 2020 we'd take 2020 energy-build only,
    in 2030, we'd take the sum of 2020 energy-build and 2030 energy-build, in 2040,
    we'd take 2030 energy-build only, and in 2050, the energy would be undefined (i.e.
    0 for the purposes of the objective function).
    """
    return sum(
        mod.FuelProdNew_Build_Stor_Cap_FuelUnit[project, v]
        for (project, v) in mod.FUEL_PROD_NEW_VNTS_OPR_IN_PRD[prd]
        if project == prj
    )


# Capacity Type Methods
###############################################################################


def fuel_prod_capacity_rule(mod, prj, prd):
    """ """
    return mod.FuelProdNew_Prod_Capacity_FuelUnitPerHour[prj, prd]


def fuel_release_capacity_rule(mod, prj, prd):
    """
    The energy capacity in a period is the sum of the new energy capacity of
    all vintages operational in the that period.
    """
    return mod.FuelProdNew_Rel_Capacity_FuelUnitPerHour[prj, prd]


def fuel_storage_capacity_rule(mod, prj, prd):
    """ """
    return mod.FuelProdNew_Stor_Capacity_FuelUnitPerHour[prj, prd]


def capacity_cost_rule(mod, prj, prd):
    """
    The capacity cost for new storage projects in a given period is the
    capacity-build of a particular vintage times the annualized power cost for
    that vintage plus the energy-build of the same vintages times the
    annualized energy cost for that vintage, summed over all vintages
    operational in the period. Note that power and energy costs are additive.
    """
    return sum(
        (
            mod.FuelProdNew_Build_Prod_Cap_FuelUnitPerHour[prj, v]
            * mod.fuel_prod_new_prod_cost_fuelunitperhour_yr[prj, v]
            + mod.FuelProdNew_Build_Rel_Cap_FuelUnitPerHour[prj, v]
            * mod.fuel_prod_new_release_cost_fuelunitperhour_yr[prj, v]
            + mod.FuelProdNew_Build_Stor_Cap_FuelUnit[prj, v]
            * mod.fuel_prod_new_storage_cost_fuelunit_yr[prj, v]
        )
        for (project, v) in mod.FUEL_PROD_NEW_VNTS_FIN_IN_PRD[prd]
        if project == prj
    )


def fixed_cost_rule(mod, prj, prd):
    """
    The fixed O&M cost for new-build generators in a given period is the
    capacity-build of a particular vintage times the fixed cost for that vintage
    summed over all vintages operational in the period.
    """
    return sum(
        (
            mod.FuelProdNew_Build_Prod_Cap_FuelUnitPerHour[prj, v]
            * mod.fuel_prod_new_prod_fixed_cost_fuelunitperhour_yr[prj, v]
            + mod.FuelProdNew_Build_Rel_Cap_FuelUnitPerHour[prj, v]
            * mod.fuel_prod_new_release_fixed_cost_fuelunitperhour_yr[prj, v]
            + mod.FuelProdNew_Build_Stor_Cap_FuelUnit[prj, v]
            * mod.fuel_prod_new_storage_fixed_cost_fuelunit_yr[prj, v]
        )
        for (project, v) in mod.FUEL_PROD_NEW_VNTS_OPR_IN_PRD[prd]
        if project == prj
    )


# Input-Output
###############################################################################


def load_model_data(
    m,
    d,
    data_portal,
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
):
    """

    :param m:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """
    fuel_prod_new_projects = list()

    _df = pd.read_csv(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "projects.tab",
        ),
        sep="\t",
        usecols=[
            "project",
            "capacity_type",
        ],
    )
    for r in zip(
        _df["project"],
        _df["capacity_type"],
    ):
        if r[1] == "fuel_prod_new":
            fuel_prod_new_projects.append(r[0])

    data_portal.data()["FUEL_PROD_NEW"] = {None: fuel_prod_new_projects}

    data_portal.load(
        filename=os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "fuel_prod_new_vintage_costs.tab",
        ),
        index=m.FUEL_PROD_NEW_VNTS,
        param=(
            m.fuel_prod_new_operational_lifetime_yrs,
            m.fuel_prod_new_prod_fixed_cost_fuelunitperhour_yr,
            m.fuel_prod_new_release_fixed_cost_fuelunitperhour_yr,
            m.fuel_prod_new_storage_fixed_cost_fuelunit_yr,
            m.fuel_prod_new_financial_lifetime_yrs,
            m.fuel_prod_new_prod_cost_fuelunitperhour_yr,
            m.fuel_prod_new_release_cost_fuelunitperhour_yr,
            m.fuel_prod_new_storage_cost_fuelunit_yr,
        ),
    )


def add_to_project_period_results(
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    m,
    d,
):
    """
    Export new build storage results.
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    results_columns = [
        "new_fuel_prod_capacity_fuelunitperhour",
        "new_fuel_rel_capacity_fuelunitperhour",
        "new_fuel_stor_capacity_fuelunit",
    ]
    data = [
        [
            prj,
            prd,
            value(m.FuelProdNew_Build_Prod_Cap_FuelUnitPerHour[prj, prd]),
            value(m.FuelProdNew_Build_Prod_Cap_FuelUnitPerHour[prj, prd]),
            value(m.FuelProdNew_Build_Stor_Cap_FuelUnit[prj, prd]),
        ]
        for (prj, prd) in m.FUEL_PROD_NEW_VNTS
    ]
    captype_df = create_results_df(
        index_columns=["project", "period"],
        results_columns=results_columns,
        data=data,
    )

    return results_columns, captype_df


# TODO: add capacity type to the results file, so that we can filter the
#  consolidated results file for the summaries
def summarize_results(
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    summary_results_file,
):
    """
    Summarize new build storage capacity results.
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param summary_results_file:
    :return:
    """

    # Get the results CSV as dataframe
    capacity_results_agg_df = read_results_file_generic(
        scenario_directory=scenario_directory,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem=subproblem,
        stage=stage,
        capacity_type=Path(__file__).stem,
    )

    # Get all technologies with new build production OR release OR energy capacity
    new_build_df = pd.DataFrame(
        capacity_results_agg_df[
            (capacity_results_agg_df["new_fuel_prod_capacity_fuelunitperhour"] > 0)
            | (capacity_results_agg_df["new_fuel_rel_capacity_fuelunitperhour"] > 0)
            | (capacity_results_agg_df["new_fuel_stor_capacity_fuelunit"] > 0)
        ][
            [
                "new_fuel_prod_capacity_fuelunitperhour",
                "new_fuel_rel_capacity_fuelunitperhour",
                "new_fuel_stor_capacity_fuelunit",
            ]
        ]
    )

    # Get the units from the units.csv file
    power_unit, energy_unit, fuel_unit = get_units(scenario_directory)

    # Rename column header
    columns = [
        "New Fuel Production Capacity ({} per hour)".format(fuel_unit),
        "New Fuel Release Capacity ({} per hour)".format(fuel_unit),
        "New Fuel Storage Capacity ({})".format(fuel_unit),
    ]

    write_summary_results_generic(
        results_df=new_build_df,
        columns=columns,
        summary_results_file=summary_results_file,
        title="New Fuel Production, Release, and Storage Capacity",
        empty_title="No new fuel production was built.",
    )

    with open(summary_results_file, "a") as outfile:
        outfile.write("\n--> New Fuel Production, Release, and Storage Capacity <--\n")
        if new_build_df.empty:
            outfile.write("No new fuel production was built.\n")
        else:
            new_build_df.to_string(outfile, float_format="{:,.2f}".format)
            outfile.write("\n")


# Database
###############################################################################


def get_model_inputs_from_database(
    scenario_id,
    subscenarios,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    conn,
):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    c = conn.cursor()

    costs = c.execute(
        """SELECT project, vintage, operational_lifetime_yrs,
        fuel_production_capacity_fixed_cost_per_fuelunitperhour_yr,
        fuel_release_capacity_fixed_cost_per_fuelunitperhour_yr,
        fuel_storage_capacity_fixed_cost_per_fuelunit_yr,
        financial_lifetime_yrs,
        fuel_production_capacity_cost_per_fuelunitperhour_yr,
        fuel_release_capacity_cost_per_fuelunitperhour_yr,
        fuel_storage_capacity_cost_per_fuelunit_yr
        FROM inputs_project_portfolios
        CROSS JOIN
        (SELECT period AS vintage
        FROM inputs_temporal_periods
        WHERE temporal_scenario_id = {temporal_scenario_id}) as relevant_vintages
        INNER JOIN
        (SELECT project, vintage, operational_lifetime_yrs,
        fuel_production_capacity_fixed_cost_per_fuelunitperhour_yr,
        fuel_release_capacity_fixed_cost_per_fuelunitperhour_yr,
        fuel_storage_capacity_fixed_cost_per_fuelunit_yr,
        financial_lifetime_yrs,
        fuel_production_capacity_cost_per_fuelunitperhour_yr,
        fuel_release_capacity_cost_per_fuelunitperhour_yr,
        fuel_storage_capacity_cost_per_fuelunit_yr
        FROM inputs_project_new_cost
        WHERE project_new_cost_scenario_id = {project_new_cost_scenario_id}) as cost
        USING (project, vintage)
        WHERE project_portfolio_scenario_id = {project_portfolio_scenario_id}
        AND capacity_type = 'fuel_prod_new';""".format(
            temporal_scenario_id=subscenarios.TEMPORAL_SCENARIO_ID,
            project_new_cost_scenario_id=subscenarios.PROJECT_NEW_COST_SCENARIO_ID,
            project_portfolio_scenario_id=subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
        )
    )

    return costs


def write_model_inputs(
    scenario_directory,
    scenario_id,
    subscenarios,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    conn,
):
    """
    Get inputs from database and write out the model input
    new_build_storage_vintage_costs.tab file
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    costs = get_model_inputs_from_database(
        scenario_id,
        subscenarios,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        conn,
    )

    with open(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "fuel_prod_new_vintage_costs.tab",
        ),
        "w",
        newline="",
    ) as tab_file:
        writer = csv.writer(tab_file, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(
            [
                "project",
                "vintage",
                "operational_lifetime_yrs",
                "fuel_production_capacity_fixed_cost_per_fuelunitperhour_yr",
                "fuel_release_capacity_fixed_cost_per_fuelunitperhour_yr",
                "fuel_storage_capacity_fixed_cost_per_fuelunit_yr",
                "financial_lifetime_yrs",
                "fuel_production_capacity_cost_per_fuelunitperhour_yr",
                "fuel_release_capacity_cost_per_fuelunitperhour_yr",
                "fuel_storage_capacity_cost_per_fuelunit_yr",
            ]
        )

        for row in costs:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)


# Validation
###############################################################################


def validate_inputs(
    scenario_id,
    subscenarios,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    conn,
):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    new_stor_costs = get_model_inputs_from_database(
        scenario_id,
        subscenarios,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        conn,
    )

    projects = get_projects(
        conn, scenario_id, subscenarios, "capacity_type", "fuel_prod_new"
    )

    # Convert input data into pandas DataFrame
    cost_df = cursor_to_df(new_stor_costs)
    df_cols = cost_df.columns

    # get the project lists
    cost_projects = cost_df["project"].unique()

    # Get expected dtypes
    expected_dtypes = get_expected_dtypes(
        conn=conn, tables=["inputs_project_new_cost", "inputs_project_new_potential"]
    )

    # Check dtypes
    dtype_errors, error_columns = validate_dtypes(cost_df, expected_dtypes)
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_new_cost",
        severity="High",
        errors=dtype_errors,
    )

    # Check valid numeric columns are non-negative
    numeric_columns = [c for c in cost_df.columns if expected_dtypes[c] == "numeric"]
    valid_numeric_columns = set(numeric_columns) - set(error_columns)
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_new_cost",
        severity="High",
        errors=validate_values(cost_df, valid_numeric_columns, min=0),
    )

    # Check that all binary new build projects are available in >=1 vintage
    msg = "Expected cost data for at least one vintage."
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_project_new_cost",
        severity="Mid",
        errors=validate_idxs(
            actual_idxs=cost_projects, req_idxs=projects, idx_label="project", msg=msg
        ),
    )

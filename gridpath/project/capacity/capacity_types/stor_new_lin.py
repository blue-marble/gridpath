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
This capacity type describes storage projects that can be built by the
optimization at a cost. Investment decisions are made separately for the
project's power capacity and its energy capacity, therefore endogenously
determining the duration sizing of the storage. The decisions are linearized,
i.e. the model decides how much power capacity and how much energy capacity
to build at a project, not whether or not to build a project of pre-defined
capacity. Once built, the capacity remains operational and fixed O&M
costs are incurred for the duration of the project's pre-specified operational lifetime.
Minimum and maximum power capacity and duration constraints can be optionally
implemented.

The capital cost input to the model is an annualized cost per unit of power capacity
(MW) and an annualized cost per unit energy capacity (MWh). The costs are additive.
If the optimization makes the decision to build new power/energy capacity, the total
annualized cost is incurred in each period of the study (and multiplied by the number
of years the period represents) for the duration of the project's financial lifetime.

.. note:: Please note that to calculate the duration of the storage project, i.e.,
    how long it can sustain discharging at its maximum output, you must adjust the
    energy capacity by the discharge efficiency. For example, a 1 MW  with 1 MWh energy
    capacity battery with discharging losses of 5% (discharging_loss_factor = 95%) would
    have a duration of 1 MWh / (1 MW/0.95) or 0.95 hours rather than 1 hour.
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
    Constraint,
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
    validate_row_monotonicity,
    validate_column_monotonicity,
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
    | | :code:`STOR_NEW_LIN`                                                  |
    |                                                                         |
    | The list of projects of capacity type :code:`stor_new_lin`.             |
    +-------------------------------------------------------------------------+
    | | :code:`STOR_NEW_LIN_VNTS`                                             |
    |                                                                         |
    | A two-dimensional set of project-vintage combinations to describe the   |
    | periods in time when storage capacity/energy can be built in the        |
    | optimization.                                                           |
    +-------------------------------------------------------------------------+
    | | :code:`STOR_NEW_LIN_VNTS_W_MIN_CAPACITY_CONSTRAINT`                   |
    |                                                                         |
    | Two-dimensional set of project-vintage combinations to describe all     |
    | possible project-vintage combinations for projects with a cumulative    |
    | minimum build capacity specified.                                       |
    +-------------------------------------------------------------------------+
    | | :code:`STOR_NEW_LIN_VNTS_W_MIN_ENERGY_CONSTRAINT`                     |
    |                                                                         |
    | Two-dimensional set of project-vintage combinations to describe all     |
    | possible project-vintage combinations for projects with a cumulative    |
    | minimum build energy specified.                                         |
    +-------------------------------------------------------------------------+
    | | :code:`STOR_NEW_LIN_VNTS_W_MAX_CAPACITY_CONSTRAINT`                   |
    |                                                                         |
    | Two-dimensional set of project-vintage combinations to describe all     |
    | possible project-vintage combinations for projects with a cumulative    |
    | maximum build capacity specified.                                       |
    +-------------------------------------------------------------------------+
    | | :code:`STOR_NEW_LIN_VNTS_W_MAX_ENERGY_CONSTRAINT`                     |
    |                                                                         |
    | Two-dimensional set of project-vintage combinations to describe all     |
    | possible project-vintage combinations for projects with a cumulative    |
    | maximum build energy specified.                                         |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`stor_new_lin_min_duration_hrs`                                 |
    | | *Defined over*: :code:`STOR_NEW_LIN`                                  |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's minimum duration, i.e. ratio of MWh of energy capacity    |
    | by MW of power capacity, in hours.                                      |
    +-------------------------------------------------------------------------+
    | | :code:`stor_new_lin_max_duration_hrs`                                 |
    | | *Defined over*: :code:`STOR_NEW_LIN`                                  |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's maximum duration, i.e. ratio of MWh of energy capacity    |
    | by MW of power capacity, in hours.                                      |
    +-------------------------------------------------------------------------+
    | | :code:`stor_new_lin_operational_lifetime_yrs`                         |
    | | *Defined over*: :code:`STOR_NEW_LIN_VNTS`                             |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's lifetime, i.e. how long project capacity/energy of a      |
    | particular vintage remains operational.                                 |
    +-------------------------------------------------------------------------+
    | | :code:`stor_new_lin_fixed_cost_per_mw_yr`                             |
    | | *Defined over*: :code:`STOR_NEW_LIN_VNTS`                             |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's power capacity fixed O&M cost incurred in each year in    |
    | which the project is operational.                                       |
    +-------------------------------------------------------------------------+
    | | :code:`stor_new_lin_fixed_cost_per_mwh_yr`                            |
    | | *Defined over*: :code:`STOR_NEW_LIN_VNTS`                             |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's energy capacity fixed O&M cost incurred in each year in   |
    | which the project is operational.                                       |
    +-------------------------------------------------------------------------+
    | | :code:`stor_new_lin_financial_lifetime_yrs_by_vintage`                |
    | | *Defined over*: :code:`STOR_NEW_LIN_VNTS`                             |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's financial lifetime, i.e. how long project capacity of a   |
    | particular vintage incurs annualized capital costs.                     |
    +-------------------------------------------------------------------------+
    | | :code:`stor_new_lin_annualized_real_cost_per_mw_yr`                   |
    | | *Defined over*: :code:`STOR_NEW_LIN_VNTS`                             |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's cost to build new power capacity in annualized real       |
    | dollars in per MW.                                                      |
    +-------------------------------------------------------------------------+
    | | :code:`stor_new_lin_annualized_real_cost_per_mwh_yr`                  |
    | | *Defined over*: :code:`STOR_NEW_LIN_VNTS`                             |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's cost to build new energy capacity in annualized real      |
    | dollars in per MW.                                                      |
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
    | | :code:`OPR_PRDS_BY_STOR_NEW_LIN_VINTAGE`                              |
    | | *Defined over*: :code:`STOR_NEW_LIN_VNTS`                             |
    |                                                                         |
    | Indexed set that describes the operational periods for each possible    |
    | project-vintage combination, based on the                               |
    | :code:`stor_new_lin_operational_lifetime_yrs`. For instance, capacity   |
    | of 2020 vintage with lifetime of 30 years will be assumed operational   |
    | starting Jan 1, 2020 and through Dec 31, 2049, but will *not* be        |
    | operational in 2050.                                                    |
    +-------------------------------------------------------------------------+
    | | :code:`STOR_NEW_LIN_OPR_PRDS`                                         |
    |                                                                         |
    | Two-dimensional set that includes the periods when project capacity of  |
    | any vintage *could* be operational if built. This set is added to the   |
    | list of sets to join to get the final :code:`PRJ_OPR_PRDS` set defined  |
    | in **gridpath.project.capacity.capacity**.                              |
    +-------------------------------------------------------------------------+
    | | :code:`STOR_NEW_LIN_VNTS_OPR_IN_PRD`                                  |
    | | *Defined over*: :code:`PERIODS`                                       |
    |                                                                         |
    | Indexed set that describes the project-vintages that could be           |
    | operational in each period based on the                                 |
    | :code:`stor_new_lin_operational_lifetime_yrs`.                          |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Variables                                                               |
    +=========================================================================+
    | | :code:`StorNewLin_Build_MW`                                           |
    | | *Defined over*: :code:`STOR_NEW_LIN_VNTS`                             |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | Determines how much power capacity (in MW) of each possible vintage is  |
    | built at each stor_new_lin project.                                     |
    +-------------------------------------------------------------------------+
    | | :code:`StorNewLin_Build_MWh`                                          |
    | | *Defined over*: :code:`STOR_NEW_LIN_VNTS`                             |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | Determines how much energy capacity (in MWh) of each possible vintage   |
    | is built at each stor_new_lin project. Note that this is independent    |
    | from :code:`StorNewLin_Build_MW`, making the storage duration sizing    |
    | an endogenous model decision.                                           |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Expressions                                                             |
    +=========================================================================+
    | | :code:`StorNewLin_Power_Capacity_MW`                                  |
    | | *Defined over*: :code:`STOR_NEW_LIN_OPR_PRDS`                         |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The power capacity of a new storage project (in MW) in a given          |
    | operational period is equal to the sum of all capacity-build of         |
    | vintages operational in that period.                                    |
    +-------------------------------------------------------------------------+
    | | :code:`StorNewLin_Energy_Capacity_MWh`                                |
    | | *Defined over*: :code:`STOR_NEW_LIN_OPR_PRDS`                         |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The energy capacity of a new storage project (in MWh) in a given        |
    | operational period is equal to the sum of all energy-build of vintages  |
    | operational in that period.                                             |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Constraints                                                             |
    +=========================================================================+
    | | :code:`StorNewLin_Min_Duration_Constraint`                            |
    | | *Defined over*: :code:`STOR_NEW_LIN_OPR_PRDS`                         |
    |                                                                         |
    | Ensures that the storage duration is above a pre-specified requirement  |
    | when building the project, preventing situations when energy capacity   |
    | is built first with power capacity only following in a subsequent       |
    | vintage.                                                                |
    +-------------------------------------------------------------------------+
    | | :code:`StorNewLin_Max_Duration_Constraint`                            |
    | | *Defined over*: :code:`STOR_NEW_LIN_OPR_PRDS`                         |
    |                                                                         |
    | Ensures that the storage duration in each operational period is above   |
    | a pre-specified requirement.                                            |
    +-------------------------------------------------------------------------+

    """

    # Sets
    ###########################################################################

    m.STOR_NEW_LIN = Set()
    m.STOR_NEW_LIN_VNTS = Set(dimen=2, within=m.STOR_NEW_LIN * m.PERIODS)

    # Required Params
    ###########################################################################

    m.stor_new_lin_min_duration_hrs = Param(m.STOR_NEW_LIN, within=NonNegativeReals)

    m.stor_new_lin_max_duration_hrs = Param(m.STOR_NEW_LIN, within=NonNegativeReals)

    m.stor_new_lin_operational_lifetime_yrs = Param(
        m.STOR_NEW_LIN_VNTS, within=NonNegativeReals
    )

    m.stor_new_lin_fixed_cost_per_mw_yr = Param(
        m.STOR_NEW_LIN_VNTS, within=NonNegativeReals
    )

    m.stor_new_lin_fixed_cost_per_mwh_yr = Param(
        m.STOR_NEW_LIN_VNTS, within=NonNegativeReals
    )

    m.stor_new_lin_financial_lifetime_yrs_by_vintage = Param(
        m.STOR_NEW_LIN_VNTS, within=NonNegativeReals
    )

    m.stor_new_lin_annualized_real_cost_per_mw_yr = Param(
        m.STOR_NEW_LIN_VNTS, within=NonNegativeReals
    )

    m.stor_new_lin_annualized_real_cost_per_mwh_yr = Param(
        m.STOR_NEW_LIN_VNTS, within=NonNegativeReals
    )

    # Derived Sets
    ###########################################################################

    m.OPR_PRDS_BY_STOR_NEW_LIN_VINTAGE = Set(
        m.STOR_NEW_LIN_VNTS, initialize=operational_periods_by_storage_vintage
    )

    m.STOR_NEW_LIN_OPR_PRDS = Set(dimen=2, initialize=stor_new_lin_operational_periods)

    m.STOR_NEW_LIN_VNTS_OPR_IN_PRD = Set(
        m.PERIODS, dimen=2, initialize=stor_new_lin_vintages_operational_in_period
    )

    m.FIN_PRDS_BY_STOR_NEW_LIN_VINTAGE = Set(
        m.STOR_NEW_LIN_VNTS, initialize=financial_periods_by_storage_vintage
    )

    m.STOR_NEW_LIN_FIN_PRDS = Set(dimen=2, initialize=stor_new_lin_financial_periods)

    m.STOR_NEW_LIN_VNTS_FIN_IN_PRD = Set(
        m.PERIODS, dimen=2, initialize=stor_new_lin_vintages_financial_in_period
    )

    # Variable
    ###########################################################################

    m.StorNewLin_Build_MW = Var(m.STOR_NEW_LIN_VNTS, within=NonNegativeReals)

    m.StorNewLin_Build_MWh = Var(m.STOR_NEW_LIN_VNTS, within=NonNegativeReals)

    # Expressions
    ###########################################################################

    m.StorNewLin_Power_Capacity_MW = Expression(
        m.STOR_NEW_LIN_OPR_PRDS, rule=power_rule
    )

    m.StorNewLin_Energy_Capacity_MWh = Expression(
        m.STOR_NEW_LIN_OPR_PRDS, rule=energy_rule
    )

    # Constraints
    ###########################################################################

    m.StorNewLin_Min_Duration_Constraint = Constraint(
        m.STOR_NEW_LIN_OPR_PRDS, rule=min_duration_rule
    )

    m.StorNewLin_Max_Duration_Constraint = Constraint(
        m.STOR_NEW_LIN_OPR_PRDS, rule=max_duration_rule
    )

    # Dynamic Components
    ###########################################################################

    # Add to list of sets we'll join to get the final
    # PRJ_OPR_PRDS set
    getattr(d, capacity_type_operational_period_sets).append(
        "STOR_NEW_LIN_OPR_PRDS",
    )

    # Add to list of sets we'll join to get the final
    # PRJ_FIN_PRDS set
    getattr(d, capacity_type_financial_period_sets).append(
        "STOR_NEW_LIN_FIN_PRDS",
    )


# Set Rules
###############################################################################


def operational_periods_by_storage_vintage(mod, prj, v):
    return relevant_periods_by_project_vintage(
        periods=getattr(mod, "PERIODS"),
        period_start_year=getattr(mod, "period_start_year"),
        period_end_year=getattr(mod, "period_end_year"),
        vintage=v,
        lifetime_yrs=mod.stor_new_lin_operational_lifetime_yrs[prj, v],
    )


def stor_new_lin_operational_periods(mod):
    return project_relevant_periods(
        project_vintages_set=mod.STOR_NEW_LIN_VNTS,
        relevant_periods_by_project_vintage_set=mod.OPR_PRDS_BY_STOR_NEW_LIN_VINTAGE,
    )


def stor_new_lin_vintages_operational_in_period(mod, p):
    return project_vintages_relevant_in_period(
        project_vintage_set=mod.STOR_NEW_LIN_VNTS,
        relevant_periods_by_project_vintage_set=mod.OPR_PRDS_BY_STOR_NEW_LIN_VINTAGE,
        period=p,
    )


def financial_periods_by_storage_vintage(mod, prj, v):
    return relevant_periods_by_project_vintage(
        periods=getattr(mod, "PERIODS"),
        period_start_year=getattr(mod, "period_start_year"),
        period_end_year=getattr(mod, "period_end_year"),
        vintage=v,
        lifetime_yrs=mod.stor_new_lin_financial_lifetime_yrs_by_vintage[prj, v],
    )


def stor_new_lin_financial_periods(mod):
    return project_relevant_periods(
        project_vintages_set=mod.STOR_NEW_LIN_VNTS,
        relevant_periods_by_project_vintage_set=mod.FIN_PRDS_BY_STOR_NEW_LIN_VINTAGE,
    )


def stor_new_lin_vintages_financial_in_period(mod, p):
    return project_vintages_relevant_in_period(
        project_vintage_set=mod.STOR_NEW_LIN_VNTS,
        relevant_periods_by_project_vintage_set=mod.FIN_PRDS_BY_STOR_NEW_LIN_VINTAGE,
        period=p,
    )


# Expression Rules
###############################################################################


def power_rule(mod, g, p):
    """
    **Expression Name**: StorNewLin_Power_Capacity_MW
    **Defined Over**: STOR_NEW_LIN_OPR_PRDS

    The power capacity of a new storage project in a given operational
    period for the storage project is equal to the sum of all power
    capacity-build of vintages operational in that period.

    This expression is not defined for a new storage project's
    non-operational periods (i.e. it's 0). E.g. if we were allowed to build
    capacity in 2020 and 2030, and the project had a 15 year lifetime,
    in 2020 we'd take 2020 capacity-build only, in 2030, we'd take the sum
    of 2020 capacity-build and 2030 capacity-build, in 2040, we'd take 2030
    capacity-build only, and in 2050, the capacity would be undefined (i.e.
    0 for the purposes of the objective function).
    """
    return sum(
        mod.StorNewLin_Build_MW[g, v]
        for (gen, v) in mod.STOR_NEW_LIN_VNTS_OPR_IN_PRD[p]
        if gen == g
    )


def energy_rule(mod, g, p):
    """
    **Expression Name**: StorNewLin_Energy_Capacity_MWh
    **Defined Over**: STOR_NEW_LIN_OPR_PRDS

    The energy capacity of a new storage project in a given operational
    period for the storage project is equal to the sum of all energy
    capacity-build of vintages operational in that period.

    This expression is not defined for a new storage project's
    non-operational periods (i.e. it's 0). E.g. if we were allowed to build
    energy in 2020 and 2030, and the project had a 15 year lifetime,
    in 2020 we'd take 2020 energy-build only, in 2030, we'd take the sum
    of 2020 energy-build and 2030 energy-build, in 2040, we'd take 2030
    energy-build only, and in 2050, the energy would be undefined (i.e.
    0 for the purposes of the objective function).
    """
    return sum(
        mod.StorNewLin_Build_MWh[g, v]
        for (gen, v) in mod.STOR_NEW_LIN_VNTS_OPR_IN_PRD[p]
        if gen == g
    )


# Constraint Formulation Rules
###############################################################################


def min_duration_rule(mod, g, p):
    """
    **Constraint Name**: StorNewLin_Min_Duration_Constraint
    **Enforced Over**: STOR_NEW_LIN_OPR_PRDS

    Storage duration must be above a pre-specified requirement in each
    operational period.
    """
    return (
        mod.StorNewLin_Energy_Capacity_MWh[g, p]
        >= mod.StorNewLin_Power_Capacity_MW[g, p] * mod.stor_new_lin_min_duration_hrs[g]
    )


def max_duration_rule(mod, g, p):
    """
    **Constraint Name**: StorNewLin_Max_Duration_Constraint
    **Enforced Over**: STOR_NEW_LIN_OPR_PRDS

    Storage duration must be below a pre-specified requirement in each
    operational period.
    """
    return (
        mod.StorNewLin_Energy_Capacity_MWh[g, p]
        <= mod.StorNewLin_Power_Capacity_MW[g, p] * mod.stor_new_lin_max_duration_hrs[g]
    )


# Capacity Type Methods
###############################################################################


def capacity_rule(mod, g, p):
    """
    The power capacity in a period is the sum of the new power capacity of all
    vintages operational in the that period.
    """
    return mod.StorNewLin_Power_Capacity_MW[g, p]


def energy_capacity_rule(mod, g, p):
    """
    The energy capacity in a period is the sum of the new energy capacity of
    all vintages operational in the that period.
    """
    return mod.StorNewLin_Energy_Capacity_MWh[g, p]


def capacity_cost_rule(mod, g, p):
    """
    The capital cost for new storage projects in a given period is the
    capacity-build of a particular vintage times the annualized power cost for
    that vintage plus the energy-build of the same vintages times the
    annualized energy cost for that vintage, summed over all vintages
    incurring costs in the period. Note that power and energy costs are additive.
    """
    return sum(
        (
            mod.StorNewLin_Build_MW[g, v]
            * mod.stor_new_lin_annualized_real_cost_per_mw_yr[g, v]
            + mod.StorNewLin_Build_MWh[g, v]
            * mod.stor_new_lin_annualized_real_cost_per_mwh_yr[g, v]
        )
        for (gen, v) in mod.STOR_NEW_LIN_VNTS_FIN_IN_PRD[p]
        if gen == g
    )


def fixed_cost_rule(mod, g, p):
    """
    The fixed O&M cost for new storage projects in a given period is the
    capacity-build of a particular vintage times the fixed power cost for
    that vintage plus the energy-build of the same vintages times the
    fixed energy cost for that vintage, summed over all vintages
    operational in the period. Note that power and energy costs are additive.
    """
    return sum(
        (
            mod.StorNewLin_Build_MW[g, v] * mod.stor_new_lin_fixed_cost_per_mw_yr[g, v]
            + mod.StorNewLin_Build_MWh[g, v]
            * mod.stor_new_lin_fixed_cost_per_mwh_yr[g, v]
        )
        for (gen, v) in mod.STOR_NEW_LIN_VNTS_FIN_IN_PRD[p]
        if gen == g
    )


def new_capacity_rule(mod, g, p):
    """
    New capacity built at project g in period p.
    Returns 0 if we can't build capacity at this project in period p.
    """
    return mod.StorNewLin_Build_MW[g, p] if (g, p) in mod.STOR_NEW_LIN_VNTS else 0


def new_energy_capacity_rule(mod, g, p):
    """
    New capacity built at project g in period p.
    Returns 0 if we can't build capacity at this project in period p.
    """
    return mod.StorNewLin_Build_MWh[g, p] if (g, p) in mod.STOR_NEW_LIN_VNTS else 0


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

    def get_data():
        stor_new_lin_projects = list()
        stor_min_duration = dict()
        stor_max_duration = dict()

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
                "minimum_duration_hours",
                "maximum_duration_hours",
            ],
        )
        for r in zip(
            _df["project"],
            _df["capacity_type"],
            _df["minimum_duration_hours"],
            _df["maximum_duration_hours"],
        ):
            if r[1] == "stor_new_lin":
                stor_new_lin_projects.append(r[0])
                stor_min_duration[r[0]] = float(r[2])
                stor_max_duration[r[0]] = float(r[3])

        return stor_new_lin_projects, stor_min_duration, stor_max_duration

    (
        stor_new_lin_set,
        stor_new_lin_min_duration_hrs,
        stor_new_lin_max_duration_hrs,
    ) = get_data()
    data_portal.data()["STOR_NEW_LIN"] = {None: stor_new_lin_set}
    data_portal.data()["stor_new_lin_min_duration_hrs"] = stor_new_lin_min_duration_hrs
    data_portal.data()["stor_new_lin_max_duration_hrs"] = stor_new_lin_max_duration_hrs

    data_portal.load(
        filename=os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "new_build_storage_vintage_costs.tab",
        ),
        index=m.STOR_NEW_LIN_VNTS,
        select=(
            "project",
            "vintage",
            "operational_lifetime_yrs",
            "fixed_cost_per_mw_yr",
            "fixed_cost_per_mwh_yr",
            "financial_lifetime_yrs",
            "annualized_real_cost_per_mw_yr",
            "annualized_real_cost_per_mwh_yr",
        ),
        param=(
            m.stor_new_lin_operational_lifetime_yrs,
            m.stor_new_lin_fixed_cost_per_mw_yr,
            m.stor_new_lin_fixed_cost_per_mwh_yr,
            m.stor_new_lin_financial_lifetime_yrs_by_vintage,
            m.stor_new_lin_annualized_real_cost_per_mw_yr,
            m.stor_new_lin_annualized_real_cost_per_mwh_yr,
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
        "new_build_mw",
        "new_build_mwh",
    ]
    data = [
        [
            prj,
            prd,
            value(m.StorNewLin_Build_MW[prj, prd]),
            value(m.StorNewLin_Build_MWh[prj, prd]),
        ]
        for (prj, prd) in m.STOR_NEW_LIN_VNTS
    ]
    captype_df = create_results_df(
        index_columns=["project", "period"],
        results_columns=results_columns,
        data=data,
    )

    return results_columns, captype_df


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

    # Get all technologies with new build storage power OR energy capacity
    new_build_df = pd.DataFrame(
        capacity_results_agg_df[
            (capacity_results_agg_df["new_build_mw"] > 0)
            | (capacity_results_agg_df["new_build_mwh"] > 0)
        ][["new_build_mw", "new_build_mwh"]]
    )

    # Get the units from the units.csv file
    power_unit, energy_unit, fuel_unit = get_units(scenario_directory)

    # Rename column header
    columns = [
        "New (Linear) Storage Power Capacity ({})".format(power_unit),
        "New (Linear) Storage Energy Capacity ({})".format(energy_unit),
    ]

    write_summary_results_generic(
        results_df=new_build_df,
        columns=columns,
        summary_results_file=summary_results_file,
        title="New (Linear) Storage Capacity",
        empty_title="No new stor_new_lin storage was built.",
    )


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

    new_stor_costs = c.execute(
        """SELECT project, vintage, operational_lifetime_yrs,
        fixed_cost_per_mw_yr, fixed_cost_per_mwh_yr, financial_lifetime_yrs,
        annualized_real_cost_per_mw_yr,
        annualized_real_cost_per_mwh_yr
        FROM inputs_project_portfolios
        CROSS JOIN
        (SELECT period AS vintage
        FROM inputs_temporal_periods
        WHERE temporal_scenario_id = {temporal}) as relevant_vintages
        INNER JOIN
        (SELECT project, vintage, operational_lifetime_yrs,
        fixed_cost_per_mw_yr, fixed_cost_per_mwh_yr, financial_lifetime_yrs,
        annualized_real_cost_per_mw_yr, annualized_real_cost_per_mwh_yr
        FROM inputs_project_new_cost
        WHERE project_new_cost_scenario_id = {new_cost}) as cost
        USING (project, vintage)
        WHERE project_portfolio_scenario_id = {portfolio}
        AND capacity_type = 'stor_new_lin';""".format(
            temporal=subscenarios.TEMPORAL_SCENARIO_ID,
            new_cost=subscenarios.PROJECT_NEW_COST_SCENARIO_ID,
            portfolio=subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
        )
    )

    return new_stor_costs


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

    with open(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "new_build_storage_vintage_costs.tab",
        ),
        "w",
        newline="",
    ) as new_storage_costs_tab_file:
        writer = csv.writer(
            new_storage_costs_tab_file, delimiter="\t", lineterminator="\n"
        )

        # Write header
        writer.writerow(
            [
                "project",
                "vintage",
                "operational_lifetime_yrs",
                "fixed_cost_per_mw_yr",
                "fixed_cost_per_mwh_yr",
                "financial_lifetime_yrs",
                "annualized_real_cost_per_mw_yr",
                "annualized_real_cost_per_mwh_yr",
            ]
        )

        for row in new_stor_costs:
            writer.writerow(row)


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
        conn, scenario_id, subscenarios, "capacity_type", "stor_new_lin"
    )

    # Convert input data into pandas DataFrame
    cost_df = cursor_to_df(new_stor_costs)

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

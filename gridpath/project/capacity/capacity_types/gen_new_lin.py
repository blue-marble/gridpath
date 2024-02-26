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
This capacity type describes new generation projects that can be built by the
optimization at a cost. These investment decisions are linearized, i.e.
the decision is not whether to build a unit of a specific size (e.g. a
50-MW combustion turbine), but how much capacity to build at a particular
*project*. Once built, the capacity remains operational and fixed O&M costs are incurred
for the duration of the project's pre-specified operational lifetime. Minimum and
maximum capacity constraints can be optionally implemented.

The capital cost input to the model is an annualized cost per unit capacity. If the
optimization makes the decision to build new capacity, the total annualized
cost is incurred in each period of the study (and multiplied by the number
of years the period represents) for the duration of the project's financial
lifetime.
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
    | | :code:`GEN_NEW_LIN_VNTS`                                              |
    |                                                                         |
    | A two-dimensional set of project-vintage combinations to describe the   |
    | periods in time when project capacity can be built in the optimization. |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`gen_new_lin_operational_lifetime_yrs_by_vintage`               |
    | | *Defined over*: :code:`GEN_NEW_LIN_VNTS`                              |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's lifetime, i.e. how long project capacity of a particular  |
    | vintage remains operational.                                            |
    +-------------------------------------------------------------------------+
    | | :code:`gen_new_lin_fixed_cost_per_mw_yr`                              |
    | | *Defined over*: :code:`GEN_NEW_LIN_VNTS`                              |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's fixed O&M cost incurred in each year in which the project |
    | is operational.                                                         |
    +-------------------------------------------------------------------------+
    | | :code:`gen_new_lin_financial_lifetime_yrs_by_vintage`                 |
    | | *Defined over*: :code:`GEN_NEW_LIN_VNTS`                              |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's financial lifetime, i.e. how long project capacity of a   |
    | particular incurs annualized capital costs.                             |
    +-------------------------------------------------------------------------+
    | | :code:`gen_new_lin_annualized_real_cost_per_mw_yr`                    |
    | | *Defined over*: :code:`GEN_NEW_LIN_VNTS`                              |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's cost to build new capacity in annualized real dollars in  |
    | per MW.                                                                 |
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
    | | :code:`OPR_PRDS_BY_GEN_NEW_LIN_VINTAGE`                               |
    | | *Defined over*: :code:`GEN_NEW_LIN_VNTS`                              |
    |                                                                         |
    | Indexed set that describes the operational periods for each possible    |
    | project-vintage combination, based on the                               |
    | :code:`gen_new_lin_operational_lifetime_yrs_by_vintage`. For instance,  |
    | capacity of  the 2020 vintage with lifetime of 30 years will be assumed |
    | operational  starting Jan 1, 2020 and through Dec 31, 2049, but will    |
    | *not* be operational in 2050.                                           |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_NEW_LIN_OPR_PRDS`                                          |
    |                                                                         |
    | Two-dimensional set that includes the periods when project capacity of  |
    | any vintage *could* be operational if built. This set is added to the   |
    | list of sets to join to get the final :code:`PRJ_OPR_PRDS` set defined  |
    | in **gridpath.project.capacity.capacity**.                              |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_NEW_LIN_VNTS_OPR_IN_PERIOD`                                |
    | | *Defined over*: :code:`PERIODS`                                       |
    |                                                                         |
    | Indexed set that describes the project-vintages that could be           |
    | operational in each period based on the                                 |
    | :code:`gen_new_lin_operational_lifetime_yrs_by_vintage`.                |
    +-------------------------------------------------------------------------+
    | | :code:`FIN_PRDS_BY_GEN_NEW_LIN_VINTAGE`                               |
    | | *Defined over*: :code:`GEN_NEW_LIN_VNTS`                              |
    |                                                                         |
    | Indexed set that describes the financial periods for each possible      |
    | project-vintage combination, based on the                               |
    | :code:`gen_new_lin_financial_lifetime_yrs_by_vintage`. For instance,    |
    | capacity of  the 2020 vintage with lifetime of 30 years will be assumed |
    | to incur costs starting Jan 1, 2020 and through Dec 31, 2049, but will  |
    | *not* be operational in 2050.                                           |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_NEW_LIN_FIN_PRDS`                                          |
    |                                                                         |
    | Two-dimensional set that includes the periods when project capacity of  |
    | any vintage *could* be incurring costs if built. This set is added to   |
    | the list of sets to join to get the final :code:`PRJ_FIN_PRDS` set      |
    | defined in **gridpath.project.capacity.capacity**.                      |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_NEW_LIN_VNTS_FIN_IN_PERIOD`                                |
    | | *Defined over*: :code:`PERIODS`                                       |
    |                                                                         |
    | Indexed set that describes the project-vintages that could be incurring |
    | costs in each period based on the                                       |
    | :code:`gen_new_lin_operational_lifetime_yrs_by_vintage`.                |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Variables                                                               |
    +=========================================================================+
    | | :code:`GenNewLin_Build_MW`                                            |
    | | *Defined over*: :code:`GEN_NEW_LIN_VNTS`                              |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | Determines how much capacity of each possible vintage is built at each  |
    | gen_new_lin project.                                                    |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Expressions                                                             |
    +=========================================================================+
    | | :code:`GenNewLin_Capacity_MW`                                         |
    | | *Defined over*: :code:`GEN_NEW_LIN_OPR_PRDS`                          |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The capacity of a new-build generator in a given operational period is  |
    | equal to the sum of all capacity-build of vintages operational in that  |
    | period.                                                                 |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Constraints                                                             |
    +=========================================================================+
    | | :code:`GenNewLin_Min_Cum_Build_Constraint`                            |
    | | *Defined over*: :code:`GEN_NEW_LIN_VNTS_W_MIN_CONSTRAINT`             |
    |                                                                         |
    | Ensures that certain amount of capacity is built by a certain period,   |
    | based on :code:`gen_new_lin_min_cumulative_new_build_mw`.               |
    +-------------------------------------------------------------------------+
    | | :code:`GenNewLin_Max_Cum_Build_Constraint`                            |
    | | *Defined over*: :code:`GEN_NEW_LIN_VNTS_W_MAX_CONSTRAINT`             |
    |                                                                         |
    | Limits the amount of capacity built by a certain period, based on       |
    | :code:`gen_new_lin_max_cumulative_new_build_mw`.                        |
    +-------------------------------------------------------------------------+


    """

    # Sets
    ###########################################################################

    m.GEN_NEW_LIN_VNTS = Set(dimen=2, within=m.PROJECTS * m.PERIODS)

    # Required Params
    ###########################################################################

    m.gen_new_lin_operational_lifetime_yrs_by_vintage = Param(
        m.GEN_NEW_LIN_VNTS, within=NonNegativeReals
    )

    m.gen_new_lin_fixed_cost_per_mw_yr = Param(
        m.GEN_NEW_LIN_VNTS, within=NonNegativeReals
    )

    m.gen_new_lin_financial_lifetime_yrs_by_vintage = Param(
        m.GEN_NEW_LIN_VNTS, within=NonNegativeReals
    )

    m.gen_new_lin_annualized_real_cost_per_mw_yr = Param(
        m.GEN_NEW_LIN_VNTS, within=NonNegativeReals
    )

    # Derived Sets
    ###########################################################################

    m.OPR_PRDS_BY_GEN_NEW_LIN_VINTAGE = Set(
        m.GEN_NEW_LIN_VNTS, initialize=operational_periods_by_generator_vintage
    )

    m.GEN_NEW_LIN_OPR_PRDS = Set(dimen=2, initialize=gen_new_lin_operational_periods)

    m.GEN_NEW_LIN_VNTS_OPR_IN_PERIOD = Set(
        m.PERIODS, dimen=2, initialize=gen_new_lin_vintages_operational_in_period
    )

    m.FIN_PRDS_BY_GEN_NEW_LIN_VINTAGE = Set(
        m.GEN_NEW_LIN_VNTS, initialize=financial_periods_by_generator_vintage
    )

    m.GEN_NEW_LIN_FIN_PRDS = Set(dimen=2, initialize=gen_new_lin_financial_periods)

    m.GEN_NEW_LIN_VNTS_FIN_IN_PERIOD = Set(
        m.PERIODS, dimen=2, initialize=gen_new_lin_vintages_financial_in_period
    )

    # Variables
    ###########################################################################

    m.GenNewLin_Build_MW = Var(m.GEN_NEW_LIN_VNTS, within=NonNegativeReals)

    # Expressions
    ###########################################################################

    m.GenNewLin_Capacity_MW = Expression(
        m.GEN_NEW_LIN_OPR_PRDS, rule=gen_new_lin_capacity_rule
    )

    # Dynamic Components
    ###########################################################################

    # Add to list of sets we'll join to get the final
    # PRJ_OPR_PRDS set
    getattr(d, capacity_type_operational_period_sets).append(
        "GEN_NEW_LIN_OPR_PRDS",
    )

    # Add to list of sets we'll join to get the final
    # PRJ_FIN_PRDS set
    getattr(d, capacity_type_financial_period_sets).append(
        "GEN_NEW_LIN_FIN_PRDS",
    )


# Set Rules
###############################################################################


def operational_periods_by_generator_vintage(mod, prj, v):
    return relevant_periods_by_project_vintage(
        periods=getattr(mod, "PERIODS"),
        period_start_year=getattr(mod, "period_start_year"),
        period_end_year=getattr(mod, "period_end_year"),
        vintage=v,
        lifetime_yrs=mod.gen_new_lin_operational_lifetime_yrs_by_vintage[prj, v],
    )


def gen_new_lin_operational_periods(mod):
    return project_relevant_periods(
        project_vintages_set=mod.GEN_NEW_LIN_VNTS,
        relevant_periods_by_project_vintage_set=mod.OPR_PRDS_BY_GEN_NEW_LIN_VINTAGE,
    )


def gen_new_lin_vintages_operational_in_period(mod, p):
    return project_vintages_relevant_in_period(
        project_vintage_set=mod.GEN_NEW_LIN_VNTS,
        relevant_periods_by_project_vintage_set=mod.OPR_PRDS_BY_GEN_NEW_LIN_VINTAGE,
        period=p,
    )


def financial_periods_by_generator_vintage(mod, prj, v):
    return relevant_periods_by_project_vintage(
        periods=getattr(mod, "PERIODS"),
        period_start_year=getattr(mod, "period_start_year"),
        period_end_year=getattr(mod, "period_end_year"),
        vintage=v,
        lifetime_yrs=mod.gen_new_lin_financial_lifetime_yrs_by_vintage[prj, v],
    )


def gen_new_lin_financial_periods(mod):
    return project_relevant_periods(
        project_vintages_set=mod.GEN_NEW_LIN_VNTS,
        relevant_periods_by_project_vintage_set=mod.FIN_PRDS_BY_GEN_NEW_LIN_VINTAGE,
    )


def gen_new_lin_vintages_financial_in_period(mod, p):
    return project_vintages_relevant_in_period(
        project_vintage_set=mod.GEN_NEW_LIN_VNTS,
        relevant_periods_by_project_vintage_set=mod.FIN_PRDS_BY_GEN_NEW_LIN_VINTAGE,
        period=p,
    )


# Expression Rules
###############################################################################


def gen_new_lin_capacity_rule(mod, g, p):
    """
    **Expression Name**: GenNewLin_Capacity_MW
    **Enforced Over**: GEN_NEW_LIN_OPR_PRDS

    The capacity of a new-build generator in a given operational period is
    equal to the sum of all capacity-build of vintages operational in that
    period.

    This expression is not defined for a new-build generator's non-operational
    periods (i.e. it's 0). E.g. if we were allowed to build capacity in 2020
    and 2030, and the project had a 15 year lifetime, in 2020 we'd take 2020
    capacity-build only, in 2030, we'd take the sum of 2020 capacity-build a
    nd 2030 capacity-build, in 2040, we'd take 2030 capacity-build only, and
    in 2050, the capacity would be undefined (i.e. 0 for the purposes of the
    objective function).
    """
    return sum(
        mod.GenNewLin_Build_MW[g, v]
        for (gen, v) in mod.GEN_NEW_LIN_VNTS_OPR_IN_PERIOD[p]
        if gen == g
    )


# Capacity Type Methods
###############################################################################


def capacity_rule(mod, g, p):
    """
    The capacity in a period is the sum of the new capacity of all
    vintages operational in the that period.
    """
    return mod.GenNewLin_Capacity_MW[g, p]


# TODO: we need to think through where to multiply the annualized costs by
#  number_years_represented[p]; currently, it's done downstream, but maybe
#  the capacity cost rule is a better place?
# TODO: it's inconsistent that the capacity available in a period is
#  calculated in an expression in add_model_components but the cost isn't;
#  that said, we don't really need to carry the extra cost expression
#  around; the capacity expression is used in the min and max cumulative
#  capacity constraints
def capacity_cost_rule(mod, g, p):
    """
    The capital cost for new-build generators in a given period is the
    capacity-build of a particular vintage times the annualized capital cost for
    that vintage summed over all vintages that are incurring costs in the period
    based on their financial lifetimes.
    """
    return sum(
        mod.GenNewLin_Build_MW[g, v]
        * mod.gen_new_lin_annualized_real_cost_per_mw_yr[g, v]
        for (gen, v) in mod.GEN_NEW_LIN_VNTS_FIN_IN_PERIOD[p]
        if gen == g
    )


def fixed_cost_rule(mod, g, p):
    """
    The fixed O&M cost for new-build generators in a given period is the
    capacity-build of a particular vintage times the fixed cost for that vintage
    summed over all vintages operational in the period.
    """
    return sum(
        mod.GenNewLin_Build_MW[g, v] * mod.gen_new_lin_fixed_cost_per_mw_yr[g, v]
        for (gen, v) in mod.GEN_NEW_LIN_VNTS_OPR_IN_PERIOD[p]
        if gen == g
    )


def new_capacity_rule(mod, g, p):
    """
    New capacity built at project g in period p.
    """
    return mod.GenNewLin_Build_MW[g, p] if (g, p) in mod.GEN_NEW_LIN_VNTS else 0


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

    # TODO: throw an error when a generator of the 'gen_new_lin' capacity
    #   type is not found in new_build_option_vintage_costs.tab
    data_portal.load(
        filename=os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "new_build_generator_vintage_costs.tab",
        ),
        index=m.GEN_NEW_LIN_VNTS,
        select=(
            "project",
            "vintage",
            "operational_lifetime_yrs",
            "fixed_cost_per_mw_yr",
            "financial_lifetime_yrs",
            "annualized_real_cost_per_mw_yr",
        ),
        param=(
            m.gen_new_lin_operational_lifetime_yrs_by_vintage,
            m.gen_new_lin_fixed_cost_per_mw_yr,
            m.gen_new_lin_financial_lifetime_yrs_by_vintage,
            m.gen_new_lin_annualized_real_cost_per_mw_yr,
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
    Export new build generation results.
    :param scenario_directory:
    :param stage:
    :param stage:
    :param m:
    :param d:
    :return:
    """
    results_columns = ["new_build_mw"]
    data = [
        [prj, prd, value(m.GenNewLin_Build_MW[prj, prd])]
        for (prj, prd) in m.GEN_NEW_LIN_VNTS
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
    Summarize new build generation capacity results.
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

    # Get all technologies with the new build capacity
    new_build_df = pd.DataFrame(
        capacity_results_agg_df[capacity_results_agg_df["new_build_mw"] > 0][
            "new_build_mw"
        ]
    )

    # Get the units from the units.csv file
    power_unit, energy_unit, fuel_unit = get_units(scenario_directory)

    # Rename column header
    columns = ["New Capacity ({})".format(power_unit)]

    write_summary_results_generic(
        results_df=new_build_df,
        columns=columns,
        summary_results_file=summary_results_file,
        title="New Generation Capacity",
        empty_title="No new gen_new_lin generation was built.",
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

    new_gen_costs = c.execute(
        """SELECT project, vintage, operational_lifetime_yrs, 
        fixed_cost_per_mw_yr, financial_lifetime_yrs,
        annualized_real_cost_per_mw_yr
        FROM inputs_project_portfolios
        CROSS JOIN
        (SELECT period AS vintage
        FROM inputs_temporal_periods
        WHERE temporal_scenario_id = {temporal}) as relevant_vintages
        INNER JOIN
        (SELECT project, vintage, financial_lifetime_yrs, 
        fixed_cost_per_mw_yr, operational_lifetime_yrs,
        annualized_real_cost_per_mw_yr
        FROM inputs_project_new_cost
        WHERE project_new_cost_scenario_id = {new_cost}) as cost
        USING (project, vintage)
        WHERE project_portfolio_scenario_id = {portfolio}
        AND capacity_type = 'gen_new_lin';""".format(
            temporal=subscenarios.TEMPORAL_SCENARIO_ID,
            new_cost=subscenarios.PROJECT_NEW_COST_SCENARIO_ID,
            portfolio=subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
        )
    )

    return new_gen_costs


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
    new_build_generator_vintage_costs.tab file
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    new_gen_costs = get_model_inputs_from_database(
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
            "new_build_generator_vintage_costs.tab",
        ),
        "w",
        newline="",
    ) as new_gen_costs_tab_file:
        writer = csv.writer(new_gen_costs_tab_file, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(
            [
                "project",
                "vintage",
                "operational_lifetime_yrs",
                "fixed_cost_per_mw_yr",
                "financial_lifetime_yrs",
                "annualized_real_cost_per_mw_yr",
            ]
        )

        for row in new_gen_costs:
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

    new_gen_costs = get_model_inputs_from_database(
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
        conn, scenario_id, subscenarios, "capacity_type", "gen_new_lin"
    )

    # Convert input data into pandas DataFrame
    cost_df = cursor_to_df(new_gen_costs)
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

#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This capacity type describes new generation projects that can be built by the
optimization at a cost. These investment decisions are linearized, i.e.
the decision is not whether to build a unit of a specific size (e.g. a
50-MW combustion turbine), but how much capacity to build at a particular
*project*. Once built, the capacity exists for the duration of the generator's
pre-specified lifetime. Minimum and maximum capacity constraints can be
optionally implemented.

The cost input to the model is an annualized cost per unit capacity. If the
optimization makes the decision to build new capacity, the total annualized
cost is incurred in each period of the study (and multiplied by the number
of years the period represents) for the duration of the project's lifetime.
Annual fixed O&M costs are also incurred by linear new-build generation.
"""

from __future__ import print_function

from builtins import next
from builtins import zip

import csv
import os.path
import pandas as pd
from pyomo.environ import Set, Param, Var, Expression, NonNegativeReals, \
    Constraint, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.dynamic_components import \
    capacity_type_operational_period_sets
from gridpath.project.capacity.capacity_types.common_methods import \
    operational_periods_by_project_vintage, project_operational_periods, \
    project_vintages_operational_in_period, update_capacity_results_table


def add_module_specific_components(m, d):
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
    | | :code:`GEN_NEW_LIN_VNTS_W_MIN_CONSTRAINT`                             |
    |                                                                         |
    | Two-dimensional set of project-vintage combinations to describe all     |
    | possible project-vintage combinations for projects with a cumulative    |
    | minimum build capacity specified.                                       |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_NEW_LIN_VNTS_W_MAX_CONSTRAINT`                             |
    |                                                                         |
    | Two-dimensional set of project-vintage combinations to describe all     |
    | possible project-vintage combinations for projects with a cumulative    |
    | maximum build capacity specified.                                       |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`gen_new_lin_lifetime_yrs_by_vintage`                           |
    | | *Defined over*: :code:`GEN_NEW_LIN_VNTS`                              |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's lifetime, i.e. how long project capacity of a particular  |
    | vintage remains operational.                                            |
    +-------------------------------------------------------------------------+
    | | :code:`gen_new_lin_annualized_real_cost_per_mw_yr`                    |
    | | *Defined over*: :code:`GEN_NEW_LIN_VNTS`                              |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The project's cost to build new capacity in annualized real dollars in  |
    | per MW.                                                                 |
    +-------------------------------------------------------------------------+

    .. note:: The cost input to the model is a levelized cost per unit
        capacity. This annualized cost is incurred in each period of the study
        (and multiplied by the number of years the period represents) for
        the duration of the project's lifetime. It is up to the user to
        ensure that the :code:`gen_new_lin_lifetime_yrs_by_vintage` and
        :code:`gen_new_lin_annualized_real_cost_per_mw_yr` parameters are
        consistent.

    +-------------------------------------------------------------------------+
    | Optional Input Params                                                   |
    +=========================================================================+
    | | :code:`gen_new_lin_min_cumulative_new_build_mw`                       |
    | | *Defined over*: :code:`GEN_NEW_LIN_VNTS`                              |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The minimum cumulative amount of capacity (in MW) that must be built    |
    | for a project by a certain period.                                      |
    +-------------------------------------------------------------------------+
    | | :code:`gen_new_lin_max_cumulative_new_build_mw`                       |
    | | *Defined over*: :code:`GEN_NEW_LIN_VNTS`                              |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The maximum cumulative amount of capacity (in MW) that must be built    |
    | for a project by a certain period.                                      |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Derived Sets                                                            |
    +=========================================================================+
    | | :code:`OPR_PRDS_BY_GEN_NEW_LIN_VINTAGE`                               |
    | | *Defined over*: :code:`GEN_NEW_LIN_VNTS`                              |
    |                                                                         |
    | Indexed set that describes the operational periods for each possible    |
    | project-vintage combination, based on the                               |
    | :code:`gen_new_lin_lifetime_yrs_by_vintage`. For instance, capacity of  |
    | the 2020 vintage with lifetime of 30 years will be assumed operational  |
    | starting Jan 1, 2020 and through Dec 31, 2049, but will *not* be        |
    | operational in 2050.                                                    |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_NEW_LIN_OPR_PRDS`                                          |
    |                                                                         |
    | Two-dimensional set that includes the periods when project capacity of  |
    | any vintage *could* be operational if built. This set is added to the   |
    | list of sets to join to get the final                                   |
    | :code:`PRJ_OPR_PRDS` set defined in                      |
    | **gridpath.project.capacity.capacity**.                                 |
    +-------------------------------------------------------------------------+
    | | :code:`GEN_NEW_LIN_VNTS_OPR_IN_PERIOD`                                |
    | | *Defined over*: :code:`PERIODS`                                       |
    |                                                                         |
    | Indexed set that describes the project-vintages that could be           |
    | operational in each period based on the                                 |
    | :code:`gen_new_lin_lifetime_yrs_by_vintage`.                            |
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

    m.GEN_NEW_LIN_VNTS = Set(
        dimen=2, within=m.PROJECTS*m.PERIODS
    )

    m.GEN_NEW_LIN_VNTS_W_MIN_CONSTRAINT = Set(
        dimen=2, within=m.GEN_NEW_LIN_VNTS
    )

    m.GEN_NEW_LIN_VNTS_W_MAX_CONSTRAINT = Set(
        dimen=2, within=m.GEN_NEW_LIN_VNTS
    )

    # Required Params
    ###########################################################################

    m.gen_new_lin_lifetime_yrs_by_vintage = Param(
        m.GEN_NEW_LIN_VNTS,
        within=NonNegativeReals
    )

    m.gen_new_lin_annualized_real_cost_per_mw_yr = Param(
        m.GEN_NEW_LIN_VNTS,
        within=NonNegativeReals
    )

    # Optional Params
    ###########################################################################

    m.gen_new_lin_min_cumulative_new_build_mw = Param(
        m.GEN_NEW_LIN_VNTS_W_MIN_CONSTRAINT,
        within=NonNegativeReals
    )

    m.gen_new_lin_max_cumulative_new_build_mw = Param(
        m.GEN_NEW_LIN_VNTS_W_MAX_CONSTRAINT,
        within=NonNegativeReals
    )

    # Derived Sets
    ###########################################################################

    m.OPR_PRDS_BY_GEN_NEW_LIN_VINTAGE = Set(
        m.GEN_NEW_LIN_VNTS,
        initialize=operational_periods_by_generator_vintage
    )

    m.GEN_NEW_LIN_OPR_PRDS = Set(
        dimen=2,
        initialize=gen_new_lin_operational_periods
    )

    m.GEN_NEW_LIN_VNTS_OPR_IN_PERIOD = Set(
        m.PERIODS, dimen=2,
        initialize=gen_new_lin_vintages_operational_in_period
    )

    # Variables
    ###########################################################################

    m.GenNewLin_Build_MW = Var(
        m.GEN_NEW_LIN_VNTS,
        within=NonNegativeReals
    )

    # Expressions
    ###########################################################################

    m.GenNewLin_Capacity_MW = Expression(
        m.GEN_NEW_LIN_OPR_PRDS,
        rule=gen_new_lin_capacity_rule
    )

    # Constraints
    ###########################################################################

    m.GenNewLin_Min_Cum_Build_Constraint = Constraint(
        m.GEN_NEW_LIN_VNTS_W_MIN_CONSTRAINT,
        rule=min_cum_build_rule
    )

    m.GenNewLin_Max_Cum_Build_Constraint = Constraint(
        m.GEN_NEW_LIN_VNTS_W_MAX_CONSTRAINT,
        rule=max_cum_build_rule
    )

    # Dynamic Components
    ###########################################################################

    # Add to list of sets we'll join to get the final
    # PRJ_OPR_PRDS set
    getattr(d, capacity_type_operational_period_sets).append(
        "GEN_NEW_LIN_OPR_PRDS",
    )


# Set Rules
###############################################################################

def operational_periods_by_generator_vintage(mod, prj, v):
    return operational_periods_by_project_vintage(
        periods=getattr(mod, "PERIODS"), vintage=v,
        lifetime=mod.gen_new_lin_lifetime_yrs_by_vintage[prj, v]
    )


def gen_new_lin_operational_periods(mod):
    return project_operational_periods(
        project_vintages_set=mod.GEN_NEW_LIN_VNTS,
        operational_periods_by_project_vintage_set=
        mod.OPR_PRDS_BY_GEN_NEW_LIN_VINTAGE
    )


def gen_new_lin_vintages_operational_in_period(mod, p):
    return project_vintages_operational_in_period(
        project_vintage_set=mod.GEN_NEW_LIN_VNTS,
        operational_periods_by_project_vintage_set=
        mod.OPR_PRDS_BY_GEN_NEW_LIN_VINTAGE,
        period=p
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
    return sum(mod.GenNewLin_Build_MW[g, v] for (gen, v)
               in mod.GEN_NEW_LIN_VNTS_OPR_IN_PERIOD[p]
               if gen == g)


# Constraint Formulation Rules
###############################################################################

def min_cum_build_rule(mod, g, p):
    """
    **Constraint Name**: GenNewLin_Min_Cum_Build_Constraint
    **Enforced Over**: GEN_NEW_LIN_VNTS_W_MIN_CONSTRAINT

    Must build a certain amount of capacity by period p.
    """
    if mod.gen_new_lin_min_cumulative_new_build_mw == 0:
        return Constraint.Skip
    else:
        return mod.GenNewLin_Capacity_MW[g, p] \
            >= mod.gen_new_lin_min_cumulative_new_build_mw[g, p]


def max_cum_build_rule(mod, g, p):
    """
    **Constraint Name**: GenNewLin_Max_Cum_Build_Constraint
    **Enforced Over**: GEN_NEW_LIN_VNTS_W_MAX_CONSTRAINT

    Can't build more than certain amount of capacity by period p.
    """
    return mod.GenNewLin_Capacity_MW[g, p] \
        <= mod.gen_new_lin_max_cumulative_new_build_mw[g, p]


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
    The capacity cost for new-build generators in a given period is the
    capacity-build of a particular vintage times the annualized cost for
    that vintage summed over all vintages operational in the period.
    """
    return sum(mod.GenNewLin_Build_MW[g, v]
               * mod.gen_new_lin_annualized_real_cost_per_mw_yr[g, v]
               for (gen, v)
               in mod.GEN_NEW_LIN_VNTS_OPR_IN_PERIOD[p]
               if gen == g)


# Input-Output
###############################################################################

def load_module_specific_data(
        m, data_portal, scenario_directory, subproblem, stage
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
    data_portal.load(filename=
                     os.path.join(scenario_directory, subproblem, stage,
                                  "inputs",
                                  "new_build_generator_vintage_costs.tab"),
                     index=m.GEN_NEW_LIN_VNTS,
                     select=("project", "vintage",
                             "lifetime_yrs", "annualized_real_cost_per_mw_yr"),
                     param=(m.gen_new_lin_lifetime_yrs_by_vintage,
                            m.gen_new_lin_annualized_real_cost_per_mw_yr)
                     )

    # Min and max cumulative capacity
    project_vintages_with_min = list()
    project_vintages_with_max = list()
    min_cumulative_mw = dict()
    max_cumulative_mw = dict()

    header = pd.read_csv(
        os.path.join(scenario_directory, subproblem, stage, "inputs",
                     "new_build_generator_vintage_costs.tab"),
        sep="\t", header=None, nrows=1
    ).values[0]

    optional_columns = ["min_cumulative_new_build_mw",
                        "max_cumulative_new_build_mw"]
    used_columns = [c for c in optional_columns if c in header]

    df = pd.read_csv(
        os.path.join(scenario_directory, subproblem, stage, "inputs",
                     "new_build_generator_vintage_costs.tab"),
        sep="\t", usecols=["project", "vintage"] + used_columns
    )

    # min_cumulative_new_build_mw is optional,
    # so GEN_NEW_LIN_VNTS_W_MIN_CONSTRAINT
    # and min_cumulative_new_build_mw simply won't be initialized if
    # min_cumulative_new_build_mw does not exist in the input file
    if "min_cumulative_new_build_mw" in df.columns:
        for row in zip(df["project"],
                       df["vintage"],
                       df["min_cumulative_new_build_mw"]):
            if row[2] != ".":
                project_vintages_with_min.append((row[0], row[1]))
                min_cumulative_mw[(row[0], row[1])] = float(row[2])
            else:
                pass
    else:
        pass

    # max_cumulative_new_build_mw is optional,
    # so GEN_NEW_LIN_VNTS_W_MAX_CONSTRAINT
    # and max_cumulative_new_build_mw simply won't be initialized if
    # max_cumulative_new_build_mw does not exist in the input file
    if "max_cumulative_new_build_mw" in df.columns:
        for row in zip(df["project"],
                       df["vintage"],
                       df["max_cumulative_new_build_mw"]):
            if row[2] != ".":
                project_vintages_with_max.append((row[0], row[1]))
                max_cumulative_mw[(row[0], row[1])] = float(row[2])
            else:
                pass
    else:
        pass

    # Load min and max cumulative capacity data
    if not project_vintages_with_min:
        pass  # if the list is empty, don't initialize the set
    else:
        data_portal.data()["GEN_NEW_LIN_VNTS_W_MIN_CONSTRAINT"] = \
            {None: project_vintages_with_min}
    data_portal.data()["gen_new_lin_min_cumulative_new_build_mw"] = \
        min_cumulative_mw

    if not project_vintages_with_max:
        pass  # if the list is empty, don't initialize the set
    else:
        data_portal.data()["GEN_NEW_LIN_VNTS_W_MAX_CONSTRAINT"] = \
            {None: project_vintages_with_max}
    data_portal.data()["gen_new_lin_max_cumulative_new_build_mw"] = \
        max_cumulative_mw


def export_module_specific_results(
        scenario_directory, subproblem, stage, m, d
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
    with open(os.path.join(scenario_directory, subproblem, stage, "results",
                           "capacity_gen_new_lin.csv"), "w", newline="") as f:

        writer = csv.writer(f)
        writer.writerow(["project", "period", "technology", "load_zone",
                         "new_build_mw"])
        for (prj, p) in m.GEN_NEW_LIN_VNTS:
            writer.writerow([
                prj,
                p,
                m.technology[prj],
                m.load_zone[prj],
                value(m.GenNewLin_Build_MW[prj, p])
            ])


def summarize_module_specific_results(
    scenario_directory, subproblem, stage, summary_results_file
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
    capacity_results_df = pd.read_csv(
        os.path.join(scenario_directory, subproblem, stage,
                     "results", "capacity_gen_new_lin.csv")
    )

    capacity_results_agg_df = \
        capacity_results_df.groupby(by=["load_zone", "technology",
                                        'period'],
                                    as_index=True
                                    ).sum()

    # Set the formatting of float to be readable
    pd.options.display.float_format = "{:,.0f}".format

    # Get all technologies with the new build capacity
    new_build_df = pd.DataFrame(
        capacity_results_agg_df[
            capacity_results_agg_df["new_build_mw"] > 0
        ]["new_build_mw"]
    )

    new_build_df.columns = ["New Capacity (MW)"]

    with open(summary_results_file, "a") as outfile:
        outfile.write("\n--> New Generation Capacity <--\n")
        if new_build_df.empty:
            outfile.write("No new generation was built.\n")
        else:
            new_build_df.to_string(outfile)
            outfile.write("\n")


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

    get_potentials = \
        (" ", " ") if subscenarios.PROJECT_NEW_POTENTIAL_SCENARIO_ID is None \
        else (
            """, minimum_cumulative_new_build_mw, 
            maximum_cumulative_new_build_mw """,
            """LEFT OUTER JOIN
            (SELECT project, period, minimum_cumulative_new_build_mw,
            maximum_cumulative_new_build_mw
            FROM inputs_project_new_potential
            WHERE project_new_potential_scenario_id = {}) as potential
            USING (project, period) """.format(
                subscenarios.PROJECT_NEW_POTENTIAL_SCENARIO_ID
            )
        )

    new_gen_costs = c.execute(
        """SELECT project, period, lifetime_yrs,
        annualized_real_cost_per_kw_yr * 1000"""
        + get_potentials[0] +
        """FROM inputs_project_portfolios
        CROSS JOIN
        (SELECT period
        FROM inputs_temporal_periods
        WHERE temporal_scenario_id = {}) as relevant_periods
        INNER JOIN
        (SELECT project, period, lifetime_yrs,
        annualized_real_cost_per_kw_yr
        FROM inputs_project_new_cost
        WHERE project_new_cost_scenario_id = {}) as cost
        USING (project, period)""".format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subscenarios.PROJECT_NEW_COST_SCENARIO_ID,
        )
        + get_potentials[1] +
        """WHERE project_portfolio_scenario_id = {}
        AND capacity_type = 'gen_new_lin';""".format(
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID
        )
    )

    return new_gen_costs


def write_module_specific_model_inputs(
        inputs_directory, subscenarios, subproblem, stage, conn
):
    """
    Get inputs from database and write out the model input
    new_build_generator_vintage_costs.tab file
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    new_gen_costs = get_module_specific_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    with open(os.path.join(inputs_directory,
                           "new_build_generator_vintage_costs.tab"), "w", newline="") as \
            new_gen_costs_tab_file:
        writer = csv.writer(new_gen_costs_tab_file, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(
            ["project", "vintage", "lifetime_yrs",
             "annualized_real_cost_per_mw_yr"] +
            ([] if subscenarios.PROJECT_NEW_POTENTIAL_SCENARIO_ID is None
             else ["min_cumulative_new_build_mw", "max_cumulative_new_build_mw"]
             )
        )

        for row in new_gen_costs:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)


def import_module_specific_results_into_database(
        scenario_id, subproblem, stage, c, db, results_directory, quiet
):
    """

    :param scenario_id:
    :param subproblem:
    :param stage:
    :param c:
    :param db:
    :param results_directory:
    :param quiet:
    :return:
    """
    # New build capacity results
    if not quiet:
        print("project new build generator")

    update_capacity_results_table(
        db=db, c=c, results_directory=results_directory,
        scenario_id=scenario_id, subproblem=subproblem, stage=stage,
        results_file="capacity_gen_new_lin.csv"
    )

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
    # new_gen_costs = get_module_specific_inputs_from_database(
    #     subscenarios, subproblem, stage, conn)

    # validate inputs
    # check that annualize real cost is positive
    # check that maximum new build doesn't decrease
    # ...

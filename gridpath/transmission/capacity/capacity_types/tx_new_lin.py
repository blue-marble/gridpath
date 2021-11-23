# Copyright 2016-2020 Blue Marble Analytics LLC.
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
This capacity type describes transmission lines that can be built by the
optimization at a cost. These investment decisions are linearized, i.e.
the decision is not whether to build a specific transmission line, but how
much capacity to build at a particular transmission corridor. Once built, the
capacity remains available for the duration of the line's pre-specified
lifetime. The line flow limits are assumed to be the same in each direction,
e.g. a 500 MW line from Zone 1 to Zone 2 will allow flows of 500 MW from
Zone 1 to Zone 2 and vice versa.

The cost input to the model is an annualized cost per unit capacity.
If the optimization makes the decision to build new capacity, the total
annualized cost is incurred in each period of the study (and multiplied by
the number of years the period represents) for the duration of the
transmission line's lifetime.

"""

import csv
import os.path
import pandas as pd
from pyomo.environ import (
    Set,
    Param,
    Var,
    Expression,
    NonNegativeReals,
    value,
    Constraint,
)

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import cursor_to_df
from gridpath.auxiliary.db_interface import setup_results_import
from gridpath.auxiliary.dynamic_components import (
    tx_capacity_type_operational_period_sets,
)
from gridpath.auxiliary.validations import (
    write_validation_to_database,
    get_expected_dtypes,
    get_tx_lines,
    validate_dtypes,
    validate_values,
    validate_idxs,
    validate_row_monotonicity,
    validate_column_monotonicity,
)


# TODO: can we have different capacities depending on the direction
# TODO: add fixed O&M costs similar to gen_new_lin
def add_model_components(m, d, scenario_directory, subproblem, stage):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`TX_NEW_LIN_VNTS`                                               |
    |                                                                         |
    | A two-dimensional set of line-vintage combinations to help describe     |
    | the periods in time when transmission line capacity can be built in the |
    | optimization.                                                           |
    +-------------------------------------------------------------------------+
    | | :code:`TX_NEW_LIN_VNTS_W_MIN_CONSTRAINT`                              |
    |                                                                         |
    | Two-dimensional set of transmission-vintage combinations to describe all|
    | possible transmission-vintage combinations for transmission lines with  |
    | a cumulative minimum build capacity specified.                          |
    +-------------------------------------------------------------------------+
    | | :code:`TX_NEW_LIN_VNTS_W_MAX_CONSTRAINT`                              |
    |                                                                         |
    | Two-dimensional set of transmission-vintage combinations to describe all|
    | possible transmission-vintage combinations for transmission lines with  |
    | a cumulative maximum build capacity specified.                          |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`tx_new_lin_lifetime_yrs`                                       |
    | | *Defined over*: :code:`TX_NEW_LIN_VNTS`                               |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The transmission line's lifetime, i.e. how long line capacity of a      |
    | particular vintage remains operational.                                 |
    +-------------------------------------------------------------------------+
    | | :code:`tx_new_lin_annualized_real_cost_per_mw_yr`                     |
    | | *Defined over*: :code:`TX_NEW_LIN_VNTS`                               |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The transmission line's cost to build new capacity in annualized        |
    | real dollars per MW.                                                    |
    +-------------------------------------------------------------------------+

    .. note:: The cost input to the model is a levelized cost per unit
        capacity. This annualized cost is incurred in each period of the study
        (and multiplied by the number of years the period represents) for
        the duration of the project's lifetime. It is up to the user to
        ensure that the :code:`tx_new_lin_lifetime_yrs` and
        :code:`tx_new_lin_annualized_real_cost_per_mw_yr` parameters are
        consistent.

    +-------------------------------------------------------------------------+
    | Optional Input Params                                                   |
    +=========================================================================+
    | | :code:`tx_new_lin_min_cumulative_new_build_mw`                        |
    | | *Defined over*: :code:`TX_NEW_LIN_VNTS`                               |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The minimum cumulative amount of capacity (in MW) that must be built    |
    | for a transmission line by a certain period.                            |
    +-------------------------------------------------------------------------+
    | | :code:`tx_new_lin_max_cumulative_new_build_mw`                        |
    | | *Defined over*: :code:`TX_NEW_LIN_VNTS`                               |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The maximum cumulative amount of capacity (in MW) that must be built    |
    | for a transmission line by a certain period.                            |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Derived Sets                                                            |
    +=========================================================================+
    | | :code:`OPR_PRDS_BY_TX_NEW_LIN_VINTAGE`                                |
    | | *Defined over*: :code:`TX_NEW_LIN_VNTS`                               |
    |                                                                         |
    | Indexed set that describes the operational periods for each possible    |
    | transmission line-vintage combination, based on the                     |
    | :code:`tx_new_lin_lifetime_yrs`. For instance, transmission capacity    |
    | of the 2020 vintage with lifetime of 30 years will be assumed           |
    | operational starting Jan 1, 2020 and through Dec 31, 2049, but will     |
    | *not* be operational in 2050.                                           |
    +-------------------------------------------------------------------------+
    | | :code:`TX_NEW_LIN_OPR_PRDS`                                           |
    |                                                                         |
    | Two-dimensional set that includes the periods when transmission         |
    | capacity of any vintage *could* be operational if built. This set is    |
    | added to the list of sets to join to get the final                      |
    | :code:`TRANMISSION_OPERATIONAL_PERIODS` set defined in                  |
    | **gridpath.transmission.capacity.capacity**.                            |
    +-------------------------------------------------------------------------+
    | | :code:`TX_NEW_LIN_VNTS_OPR_IN_PRD`                                    |
    | | *Defined over*: :code:`PERIODS`                                       |
    |                                                                         |
    | Indexed set that describes the transmission line-vintages that could    |
    | be operational in each period based on the                              |
    | :code:`tx_new_lin_lifetime_yrs`.                                        |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Variables                                                               |
    +=========================================================================+
    | | :code:`TxNewLin_Build_MW`                                             |
    | | *Defined over*: :code:`TX_NEW_LIN_VNTS`                               |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | Determines how much transmission capacity of each possible vintage is   |
    | built at each :code:`tx_new_lin transmission line`.                     |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Expressions                                                             |
    +=========================================================================+
    | | :code:`TxNewLin_Capacity_MW`                                          |
    | | *Defined over*: :code:`TX_NEW_LIN_OPR_PRDS`                           |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The transmission capacity of a line in a given operational period is    |
    | equal to the sum of all capacity-build of vintages operational in that  |
    | period.                                                                 |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Constraints                                                             |
    +=========================================================================+
    | | :code:`TxNewLin_Min_Cum_Build_Constraint`                             |
    | | *Defined over*: :code:`TX_NEW_LIN_VNTS_W_MIN_CONSTRAINT`              |
    |                                                                         |
    | Ensures that certain amount of capacity is built by a certain period,   |
    | based on :code:`tx_new_lin_min_cumulative_new_build_mw`.                |
    +-------------------------------------------------------------------------+
    | | :code:`TxNewLin_Max_Cum_Build_Constraint`                             |
    | | *Defined over*: :code:`TX_NEW_LIN_VNTS_W_MAX_CONSTRAINT`              |
    |                                                                         |
    | Limits the amount of capacity built by a certain period, based on       |
    | :code:`tx_new_lin_max_cumulative_new_build_mw`.                         |
    +-------------------------------------------------------------------------+


    """

    # Sets
    ###########################################################################

    m.TX_NEW_LIN_VNTS = Set(dimen=2)

    m.TX_NEW_LIN_VNTS_W_MIN_CONSTRAINT = Set(dimen=2, within=m.TX_NEW_LIN_VNTS)

    m.TX_NEW_LIN_VNTS_W_MAX_CONSTRAINT = Set(dimen=2, within=m.TX_NEW_LIN_VNTS)

    # Required Params
    ###########################################################################

    m.tx_new_lin_lifetime_yrs = Param(m.TX_NEW_LIN_VNTS, within=NonNegativeReals)

    m.tx_new_lin_annualized_real_cost_per_mw_yr = Param(
        m.TX_NEW_LIN_VNTS, within=NonNegativeReals
    )

    # Optional Params
    ###########################################################################

    m.tx_new_lin_min_cumulative_new_build_mw = Param(
        m.TX_NEW_LIN_VNTS_W_MIN_CONSTRAINT, within=NonNegativeReals
    )

    m.tx_new_lin_max_cumulative_new_build_mw = Param(
        m.TX_NEW_LIN_VNTS_W_MAX_CONSTRAINT, within=NonNegativeReals
    )

    # Derived Sets
    ###########################################################################

    m.OPR_PRDS_BY_TX_NEW_LIN_VINTAGE = Set(
        m.TX_NEW_LIN_VNTS,
        initialize=operational_periods_by_new_build_transmission_vintage,
    )

    m.TX_NEW_LIN_OPR_PRDS = Set(
        dimen=2, initialize=new_build_transmission_operational_periods
    )

    m.TX_NEW_LIN_VNTS_OPR_IN_PRD = Set(
        m.PERIODS,
        dimen=2,
        initialize=new_build_transmission_vintages_operational_in_period,
    )

    # Variables
    ###########################################################################

    m.TxNewLin_Build_MW = Var(m.TX_NEW_LIN_VNTS, within=NonNegativeReals)

    # Expressions
    ###########################################################################

    m.TxNewLin_Capacity_MW = Expression(
        m.TX_NEW_LIN_OPR_PRDS, rule=tx_new_lin_capacity_rule
    )

    # Constraints
    ###########################################################################

    m.TxNewLin_Min_Cum_Build_Constraint = Constraint(
        m.TX_NEW_LIN_VNTS_W_MIN_CONSTRAINT, rule=min_cum_build_rule
    )

    m.TxNewLin_Max_Cum_Build_Constraint = Constraint(
        m.TX_NEW_LIN_VNTS_W_MAX_CONSTRAINT, rule=max_cum_build_rule
    )

    # Dynamic Components
    ###########################################################################

    getattr(d, tx_capacity_type_operational_period_sets).append(
        "TX_NEW_LIN_OPR_PRDS",
    )


# Set Rules
###############################################################################


def operational_periods_by_new_build_transmission_vintage(mod, g, v):
    operational_periods = list()
    for p in mod.PERIODS:
        if v <= p < v + mod.tx_new_lin_lifetime_yrs[g, v]:
            operational_periods.append(p)
        else:
            pass
    return operational_periods


def new_build_transmission_operational_periods(mod):
    return list(
        set(
            (g, p)
            for (g, v) in mod.TX_NEW_LIN_VNTS
            for p in mod.OPR_PRDS_BY_TX_NEW_LIN_VINTAGE[g, v]
        )
    )


def new_build_transmission_vintages_operational_in_period(mod, p):
    build_vintages_by_period = list()
    for (g, v) in mod.TX_NEW_LIN_VNTS:
        if p in mod.OPR_PRDS_BY_TX_NEW_LIN_VINTAGE[g, v]:
            build_vintages_by_period.append((g, v))
        else:
            pass
    return build_vintages_by_period


# Expression Rules
###############################################################################


def tx_new_lin_capacity_rule(mod, g, p):
    """
    **Expression Name**: TxNewLin_Capacity_MW
    **Defined Over**: TX_NEW_LIN_OPR_PRDS

    The transmission capacity of a new line in a given operational period is
    equal to the sum of all capacity-build of vintages operational in that
    period.

    This expression is not defined for a new transmission line's non-
    operational periods (i.e. it's 0). E.g. if we were allowed to build
    capacity in 2020 and 2030, and the line had a 15 year lifetime,
    in 2020 we'd take 2020 capacity-build only, in 2030, we'd take the sum
    of 2020 capacity-build and 2030 capacity-build, in 2040, we'd take 2030
    capacity-build only, and in 2050, the capacity would be undefined (i.e.
    0 for the purposes of the objective function).
    """
    return sum(
        mod.TxNewLin_Build_MW[g, v]
        for (gen, v) in mod.TX_NEW_LIN_VNTS_OPR_IN_PRD[p]
        if gen == g
    )


# Constraint Formulation Rules
###############################################################################


def min_cum_build_rule(mod, g, p):
    """
    **Constraint Name**: TxNewLin_Min_Cum_Build_Constraint
    **Enforced Over**: TX_NEW_LIN_VNTS_W_MIN_CONSTRAINT

    Must build a certain amount of transmission capacity by period p.
    """
    if mod.tx_new_lin_min_cumulative_new_build_mw == 0:
        return Constraint.Skip
    else:
        return (
            mod.TxNewLin_Capacity_MW[g, p]
            >= mod.tx_new_lin_min_cumulative_new_build_mw[g, p]
        )


def max_cum_build_rule(mod, g, p):
    """
    **Constraint Name**: TxNewLin_Max_Cum_Build_Constraint
    **Enforced Over**: TX_NEW_LIN_VNTS_W_MAX_CONSTRAINT

    Can't build more than certain amount of transmission capacity by period p.
    """
    return (
        mod.TxNewLin_Capacity_MW[g, p]
        <= mod.tx_new_lin_max_cumulative_new_build_mw[g, p]
    )


# Tx Capacity Type Methods
###############################################################################


def min_transmission_capacity_rule(mod, g, p):
    """ """
    return -mod.TxNewLin_Capacity_MW[g, p]


def max_transmission_capacity_rule(mod, g, p):
    """ """
    return mod.TxNewLin_Capacity_MW[g, p]


def tx_capacity_cost_rule(mod, g, p):
    """
    Capacity cost for new builds in each period (sum over all vintages
    operational in current period).
    """
    return sum(
        mod.TxNewLin_Build_MW[g, v]
        * mod.tx_new_lin_annualized_real_cost_per_mw_yr[g, v]
        for (gen, v) in mod.TX_NEW_LIN_VNTS_OPR_IN_PRD[p]
        if gen == g
    )


# Input-Output
###############################################################################


def load_model_data(m, d, data_portal, scenario_directory, subproblem, stage):

    # TODO: throw an error when a line of the 'tx_new_lin' capacity
    #   type is not found in new_build_transmission_vintage_costs.tab
    data_portal.load(
        filename=os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "inputs",
            "new_build_transmission_vintage_costs.tab",
        ),
        index=m.TX_NEW_LIN_VNTS,
        select=(
            "transmission_line",
            "vintage",
            "tx_lifetime_yrs",
            "tx_annualized_real_cost_per_mw_yr",
        ),
        param=(m.tx_new_lin_lifetime_yrs, m.tx_new_lin_annualized_real_cost_per_mw_yr),
    )

    # Min and max cumulative capacity
    transmission_vintages_with_min = list()
    transmission_vintages_with_max = list()
    min_cumulative_mw = dict()
    max_cumulative_mw = dict()

    header = pd.read_csv(
        os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "inputs",
            "new_build_transmission_vintage_costs.tab",
        ),
        sep="\t",
        header=None,
        nrows=1,
    ).values[0]

    optional_columns = ["min_cumulative_new_build_mw", "max_cumulative_new_build_mw"]
    used_columns = [c for c in optional_columns if c in header]

    df = pd.read_csv(
        os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "inputs",
            "new_build_transmission_vintage_costs.tab",
        ),
        sep="\t",
        usecols=["transmission_line", "vintage"] + used_columns,
    )

    # min_cumulative_new_build_mw is optional,
    # so TX_NEW_LIN_VNTS_W_MIN_CONSTRAINT
    # and min_cumulative_new_build_mw simply won't be initialized if
    # min_cumulative_new_build_mw does not exist in the input file
    if "min_cumulative_new_build_mw" in df.columns:
        for row in zip(
            df["transmission_line"], df["vintage"], df["min_cumulative_new_build_mw"]
        ):
            if row[2] != ".":
                transmission_vintages_with_min.append((row[0], row[1]))
                min_cumulative_mw[(row[0], row[1])] = float(row[2])
            else:
                pass
    else:
        pass

    # max_cumulative_new_build_mw is optional,
    # so TX_NEW_LIN_VNTS_W_MAX_CONSTRAINT
    # and max_cumulative_new_build_mw simply won't be initialized if
    # max_cumulative_new_build_mw does not exist in the input file
    if "max_cumulative_new_build_mw" in df.columns:
        for row in zip(
            df["transmission_line"], df["vintage"], df["max_cumulative_new_build_mw"]
        ):
            if row[2] != ".":
                transmission_vintages_with_max.append((row[0], row[1]))
                max_cumulative_mw[(row[0], row[1])] = float(row[2])
            else:
                pass
    else:
        pass

    # Load min and max cumulative capacity data
    if not transmission_vintages_with_min:
        pass  # if the list is empty, don't initialize the set
    else:
        data_portal.data()["TX_NEW_LIN_VNTS_W_MIN_CONSTRAINT"] = {
            None: transmission_vintages_with_min
        }
    data_portal.data()["tx_new_lin_min_cumulative_new_build_mw"] = min_cumulative_mw

    if not transmission_vintages_with_max:
        pass  # if the list is empty, don't initialize the set
    else:
        data_portal.data()["TX_NEW_LIN_VNTS_W_MAX_CONSTRAINT"] = {
            None: transmission_vintages_with_max
        }
    data_portal.data()["tx_new_lin_max_cumulative_new_build_mw"] = max_cumulative_mw


# TODO: untested
def export_results(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """

    # Export transmission capacity
    with open(
        os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "results",
            "transmission_new_capacity.csv",
        ),
        "w",
        newline="",
    ) as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "transmission_line",
                "period",
                "load_zone_from",
                "load_zone_to",
                "new_build_transmission_capacity_mw",
            ]
        )
        for (transmission_line, v) in m.TX_NEW_LIN_VNTS:
            writer.writerow(
                [
                    transmission_line,
                    v,
                    m.load_zone_from[transmission_line],
                    m.load_zone_to[transmission_line],
                    value(m.TxNewLin_Build_MW[transmission_line, v]),
                ]
            )


# Database
###############################################################################


def get_model_inputs_from_database(scenario_id, subscenarios, subproblem, stage, conn):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """
    c = conn.cursor()

    get_potentials = (
        (" ", " ")
        if subscenarios.TRANSMISSION_NEW_POTENTIAL_SCENARIO_ID is None
        else (
            """, min_cumulative_new_build_mw, 
            max_cumulative_new_build_mw """,
            """LEFT OUTER JOIN
            (SELECT transmission_line, period AS vintage, 
            min_cumulative_new_build_mw, max_cumulative_new_build_mw
            FROM inputs_transmission_new_potential
            WHERE transmission_new_potential_scenario_id = {}) as potential
            USING (transmission_line, vintage) """.format(
                subscenarios.TRANSMISSION_NEW_POTENTIAL_SCENARIO_ID
            ),
        )
    )

    tx_cost = c.execute(
        """SELECT transmission_line, vintage, tx_lifetime_yrs, 
        tx_annualized_real_cost_per_mw_yr"""
        + get_potentials[0]
        + """FROM inputs_transmission_portfolios
        CROSS JOIN
        (SELECT period as vintage
        FROM inputs_temporal_periods
        WHERE temporal_scenario_id = {}) as relevant_vintages
        INNER JOIN
        (SELECT transmission_line, vintage, tx_lifetime_yrs, 
        tx_annualized_real_cost_per_mw_yr
        FROM inputs_transmission_new_cost
        WHERE transmission_new_cost_scenario_id = {} ) as cost
        USING (transmission_line, vintage)""".format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subscenarios.TRANSMISSION_NEW_COST_SCENARIO_ID,
        )
        + get_potentials[1]
        + """WHERE transmission_portfolio_scenario_id = {}
        AND capacity_type = 'tx_new_lin';""".format(
            subscenarios.TRANSMISSION_PORTFOLIO_SCENARIO_ID
        )
    )

    return tx_cost


def write_model_inputs(
    scenario_directory, scenario_id, subscenarios, subproblem, stage, conn
):
    """
    Get inputs from database and write out the model input .tab file.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    tx_cost = get_model_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn
    )

    with open(
        os.path.join(
            scenario_directory,
            str(subproblem),
            str(stage),
            "inputs",
            "new_build_transmission_vintage_costs.tab",
        ),
        "w",
        newline="",
    ) as existing_tx_capacity_tab_file:
        writer = csv.writer(
            existing_tx_capacity_tab_file, delimiter="\t", lineterminator="\n"
        )

        # Write header
        writer.writerow(
            [
                "transmission_line",
                "vintage",
                "tx_lifetime_yrs",
                "tx_annualized_real_cost_per_mw_yr",
            ]
            + (
                []
                if subscenarios.TRANSMISSION_NEW_POTENTIAL_SCENARIO_ID is None
                else ["min_cumulative_new_build_mw", "max_cumulative_new_build_mw"]
            )
        )

        for row in tx_cost:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)


def import_results_into_database(
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
        print("transmission new build")
    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db,
        cursor=c,
        table="results_transmission_capacity_new_build",
        scenario_id=scenario_id,
        subproblem=subproblem,
        stage=stage,
    )

    # Load results into the temporary table
    results = []
    with open(
        os.path.join(results_directory, "transmission_new_capacity.csv"), "r"
    ) as capacity_file:
        reader = csv.reader(capacity_file)

        next(reader)  # skip header
        for row in reader:
            transmission_line = row[0]
            period = row[1]
            load_zone_from = row[2]
            load_zone_to = row[3]
            new_build_transmission_capacity_mw = row[4]

            results.append(
                (
                    scenario_id,
                    transmission_line,
                    period,
                    subproblem,
                    stage,
                    load_zone_from,
                    load_zone_to,
                    new_build_transmission_capacity_mw,
                )
            )

    insert_temp_sql = """
        INSERT INTO 
        temp_results_transmission_capacity_new_build{}
        (scenario_id, transmission_line, period, subproblem_id, stage_id, 
        load_zone_from, load_zone_to, 
        new_build_transmission_capacity_mw)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """.format(
        scenario_id
    )
    spin_on_database_lock(conn=db, cursor=c, sql=insert_temp_sql, data=results)

    # Insert sorted results into permanent results table
    insert_sql = """
        INSERT INTO results_transmission_capacity_new_build
        (scenario_id, transmission_line, period, subproblem_id, stage_id,
        load_zone_from, load_zone_to, new_build_transmission_capacity_mw)
        SELECT
        scenario_id, transmission_line, period, subproblem_id, stage_id, 
        load_zone_from, load_zone_to, new_build_transmission_capacity_mw
        FROM temp_results_transmission_capacity_new_build{}
        ORDER BY scenario_id, transmission_line, period, subproblem_id, 
        stage_id;
        """.format(
        scenario_id
    )
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(), many=False)


# Validation
###############################################################################


def validate_inputs(scenario_id, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and validate the inputs
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    tx_cost = get_model_inputs_from_database(
        scenario_id, subscenarios, subproblem, stage, conn
    )

    tx_lines = get_tx_lines(
        conn, scenario_id, subscenarios, "capacity_type", "tx_new_lin"
    )

    # Convert input data into pandas DataFrame
    df = cursor_to_df(tx_cost)
    df_cols = df.columns

    # get the tx lines lists
    tx_lines_w_cost = df["transmission_line"].unique()

    # Get expected dtypes
    expected_dtypes = get_expected_dtypes(
        conn=conn,
        tables=["inputs_transmission_new_cost", "inputs_transmission_new_potential"],
    )

    # Check dtypes
    dtype_errors, error_columns = validate_dtypes(df, expected_dtypes)
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_transmission_new_cost",
        severity="High",
        errors=dtype_errors,
    )

    # Check valid numeric columns are non-negative
    numeric_columns = [c for c in df.columns if expected_dtypes[c] == "numeric"]
    valid_numeric_columns = set(numeric_columns) - set(error_columns)
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_transmission_new_cost",
        severity="High",
        errors=validate_values(df, valid_numeric_columns, "transmission_line", min=0),
    )

    # Check that all binary new build tx lines are available in >=1 vintage
    msg = "Expected cost data for at least one vintage."
    write_validation_to_database(
        conn=conn,
        scenario_id=scenario_id,
        subproblem_id=subproblem,
        stage_id=stage,
        gridpath_module=__name__,
        db_table="inputs_transmission_new_cost",
        severity="Mid",
        errors=validate_idxs(
            actual_idxs=tx_lines_w_cost,
            req_idxs=tx_lines,
            idx_label="transmission_line",
            msg=msg,
        ),
    )

    cols = ["min_cumulative_new_build_mw", "max_cumulative_new_build_mw"]
    # Check that maximum new build doesn't decrease
    if cols[1] in df_cols:
        write_validation_to_database(
            conn=conn,
            scenario_id=scenario_id,
            subproblem_id=subproblem,
            stage_id=stage,
            gridpath_module=__name__,
            db_table="inputs_transmission_new_potential",
            severity="Mid",
            errors=validate_row_monotonicity(
                df=df, col=cols[1], idx_col="transmission_line", rank_col="vintage"
            ),
        )

    # check that min build <= max build
    if set(cols).issubset(set(df_cols)):
        write_validation_to_database(
            conn=conn,
            scenario_id=scenario_id,
            subproblem_id=subproblem,
            stage_id=stage,
            gridpath_module=__name__,
            db_table="inputs_transmission_new_potential",
            severity="High",
            errors=validate_column_monotonicity(
                df=df, cols=cols, idx_col=["transmission_line", "vintage"]
            ),
        )

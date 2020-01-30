#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
This transmission capacity type describes new transmission projects that
can be built by the optimization at a cost. These investment decisions are
linearized, i.e. the decision is not whether to build a project of a specific
size (e.g. a 500-MW line), but how much capacity to build at a particular
*transmission project*. Once built, the capacity exists for the duration of
the project's pre-specified lifetime. The line flow limits are assumed to be
the same in each direction, e.g. a 500 MW line from Zone 1 to Zone 2 will
allow flows of 500 MW from Zone 1 to Zone 2 and vice versa.

The cost input to the model is an annualized cost per unit capacity. If the
optimization makes the decision to build new capacity, the total annualized
cost is incurred in each period of the study (and multiplied by the number
of years the period represents) for the duration of the project's lifetime.
Annual fixed O&M costs are also incurred by linear new-build generation.
"""


import csv
import os.path
from pyomo.environ import Set, Param, Var, Expression, NonNegativeReals, value

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.auxiliary import setup_results_import


# TODO: can we have different capacities depending on the direction
def add_module_specific_components(m, d):
    """
    The following Pyomo model components are defined in this module:

    +-------------------------------------------------------------------------+
    | Sets                                                                    |
    +=========================================================================+
    | | :code:`TX_NEW_LIN_VNTS`                                               |
    |                                                                         |
    | A two-dimensional set of project-vintage combinations to help describe  |
    | the periods in time when transmission capacity can be built in the      |
    | optimization.                                                           |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Required Input Params                                                   |
    +=========================================================================+
    | | :code:`tx_new_lin_lifetime_yrs`                                       |
    | | *Defined over*: :code:`TX_NEW_LIN_VNTS`                               |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The transmission project's lifetime, i.e. how long project capacity of  |
    | a particular vintage remains operational.                               |
    +-------------------------------------------------------------------------+
    | | :code:`tx_new_lin_annualized_real_cost_per_mw_yr`                     |
    | | *Defined over*: :code:`TX_NEW_LIN_VNTS`                               |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The transmission project's cost to build new capacity in annualized     |
    | real dollars per MW.                                                    |
    +-------------------------------------------------------------------------+

    .. note:: The cost input to the model is a levelized cost per unit
        capacity. This annualized cost is incurred in each period of the study
        (and multiplied by the number of years the period represents) for
        the duration of the project's lifetime. It is up to the user to
        ensure that the :code:`tx_new_lin_lifetime_yrs` and
        :code:`tx_new_lin_annualized_real_cost_per_mw_yr` parameters are
        consistent.

    |

    +-------------------------------------------------------------------------+
    | Derived Sets                                                            |
    +=========================================================================+
    | | :code:`OPR_PRDS_BY_TX_NEW_LIN_VINTAGE`                                |
    | | *Defined over*: :code:`TX_NEW_LIN_VNTS`                               |
    |                                                                         |
    | Indexed set that describes the operational periods for each possible    |
    | transmission project-vintage combination, based on the                  |
    | :code:`gen_new_lin_lifetime_yrs`. For instance, transmission capacity   |
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
    | Indexed set that describes the transmission project-vintages that could |
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
    | built at each :code:`tx_new_lin transmission project`.                  |
    +-------------------------------------------------------------------------+

    |

    +-------------------------------------------------------------------------+
    | Expressions                                                             |
    +=========================================================================+
    | | :code:`TxNewLin_Capacity_MW`                                          |
    | | *Defined over*: :code:`TX_NEW_LIN_OPR_PRDS`                           |
    | | *Within*: :code:`NonNegativeReals`                                    |
    |                                                                         |
    | The transmission capacity of a project in a given operational period is |
    | equal to the sum of all capacity-build of vintages operational in that  |
    | period.                                                                 |
    +-------------------------------------------------------------------------+


    """

    # Sets
    ###########################################################################

    m.TX_NEW_LIN_VNTS = Set(dimen=2)

    # Required Params
    ###########################################################################

    m.tx_new_lin_lifetime_yrs = Param(
        m.TX_NEW_LIN_VNTS,
        within=NonNegativeReals
    )

    m.tx_new_lin_annualized_real_cost_per_mw_yr = Param(
        m.TX_NEW_LIN_VNTS,
        within=NonNegativeReals
    )

    # Derived Sets
    ###########################################################################

    m.OPR_PRDS_BY_TX_NEW_LIN_VINTAGE = Set(
        m.TX_NEW_LIN_VNTS,
        initialize=operational_periods_by_new_build_transmission_vintage
    )

    m.TX_NEW_LIN_OPR_PRDS = Set(
        dimen=2,
        initialize=new_build_transmission_operational_periods
    )

    m.TX_NEW_LIN_VNTS_OPR_IN_PRD = Set(
        m.PERIODS, dimen=2,
        initialize=new_build_transmission_vintages_operational_in_period
    )

    # Variables
    ###########################################################################

    m.TxNewLin_Build_MW = Var(
        m.TX_NEW_LIN_VNTS,
        within=NonNegativeReals
    )

    # Expressions
    ###########################################################################

    m.TxNewLin_Capacity_MW = Expression(
        m.TX_NEW_LIN_OPR_PRDS,
        rule=tx_new_lin_capacity_rule
    )

    # Dynamic Components
    ###########################################################################

    m.tx_capacity_type_operational_period_sets.append(
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
    return set(
        (g, p) for (g, v) in mod.TX_NEW_LIN_VNTS
        for p in mod.OPR_PRDS_BY_TX_NEW_LIN_VINTAGE[g, v]
    )


def new_build_transmission_vintages_operational_in_period(mod, p):
    build_vintages_by_period = list()
    for (g, v) in mod.TX_NEW_LIN_VNTS:
        if p in mod.\
                OPR_PRDS_BY_TX_NEW_LIN_VINTAGE[g, v]:
            build_vintages_by_period.append((g, v))
        else:
            pass
    return build_vintages_by_period


# Expression Rules
###############################################################################

def tx_new_lin_capacity_rule(mod, g, p):
    """
    The transmission capacity of a new project in a given operational period is
    equal to the sum of all capacity-build of vintages operational in that
    period.

    This expression is not defined for a new transmission project's non-
    operational periods (i.e. it's 0). E.g. if we were allowed to build
    capacity in 2020 and 2030, and the project had a 15 year lifetime,
    in 2020 we'd take 2020 capacity-build only, in 2030, we'd take the sum
    of 2020 capacity-build and 2030 capacity-build, in 2040, we'd take 2030
    capacity-build only, and in 2050, the capacity would be undefined (i.e.
    0 for the purposes of the objective function).
    """
    return sum(
        mod.TxNewLin_Build_MW[g, v] for (gen, v)
        in mod.TX_NEW_LIN_VNTS_OPR_IN_PRD[p]
        if gen == g
    )


# Tx Capacity Type Methods
###############################################################################

def min_transmission_capacity_rule(mod, g, p):
    """
    """
    return -mod.TxNewLin_Capacity_MW[g, p]


def max_transmission_capacity_rule(mod, g, p):
    """
    """
    return mod.TxNewLin_Capacity_MW[g, p]


def tx_capacity_cost_rule(mod, g, p):
    """
    Capacity cost for new builds in each period (sum over all vintages
    operational in current period).
    """
    return sum(mod.TxNewLin_Build_MW[g, v]
               * mod.tx_new_lin_annualized_real_cost_per_mw_yr[g, v]
               for (gen, v) in mod.TX_NEW_LIN_VNTS_OPR_IN_PRD[p]
               if gen == g)


# Input-Output
###############################################################################

def load_module_specific_data(
    m, data_portal, scenario_directory, subproblem, stage
):

    # TODO: throw an error when a line of the 'tx_new_lin' capacity
    #   type is not found in new_build_transmission_vintage_costs.tab
    data_portal.load(
        filename=os.path.join(scenario_directory, subproblem, stage, "inputs",
                              "new_build_transmission_vintage_costs.tab"),
        index=m.TX_NEW_LIN_VNTS,
        select=("transmission_line", "vintage",
                "tx_lifetime_yrs",
                "tx_annualized_real_cost_per_mw_yr"),
        param=(m.tx_new_lin_lifetime_yrs,
               m.tx_new_lin_annualized_real_cost_per_mw_yr)
    )


# TODO: untested
def export_module_specific_results(
        m, d, scenario_directory, subproblem, stage
):
    """

    :param m:
    :param d:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """

    # Export transmission capacity
    with open(os.path.join(scenario_directory, subproblem, stage, "results",
                           "transmission_new_capacity.csv"),
              "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["transmission_line", "period",
                         "load_zone_from", "load_zone_to",
                         "new_build_transmission_capacity_mw"])
        for (transmission_line, p) in m.TRANSMISSION_OPERATIONAL_PERIODS:
            writer.writerow([
                transmission_line,
                p,
                m.load_zone_from[transmission_line],
                m.load_zone_to[transmission_line],
                value(m.TxNewLin_Build_MW[transmission_line, p])
            ])


# Database
###############################################################################

# TODO: untested
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
    # TODO: add inputs_transmission_new_cost and
    #  subscenarios_transmission_new_cost tables to testing database
    tx_cost = c.execute(
        """SELECT transmission_line, vintage, tx_lifetime_yrs, 
        tx_annualized_real_cost_per_mw_yr
        FROM inputs_transmission_portfolios
        CROSS JOIN
        (SELECT period
        FROM inputs_temporal_periods
        WHERE temporal_scenario_id = {}) as relevant_periods
        INNER JOIN
        (SELECT transmission_line, vintage, tx_lifetime_yrs, 
        tx_annualized_real_cost_per_mw_yr
        FROM inputs_transmission_new_cost
        WHERE transmission_new_cost_scenario_id = {} ) as cost
        USING (transmission_line, vintage   )
        WHERE transmission_portfolio_scenario_id = {};""".format(
            subscenarios.TEMPORAL_SCENARIO_ID,
            subscenarios.TRANSMISSION_EXISTING_CAPACITY_SCENARIO_ID,
            subscenarios.TRANSMISSION_PORTFOLIO_SCENARIO_ID
        )
    )

    return tx_cost


# TODO: untested
def write_module_specific_model_inputs(
        inputs_directory, subscenarios, subproblem, stage, conn):
    """
    Get inputs from database and write out the model input .tab file.
    :param inputs_directory: local directory where .tab files will be saved
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    tx_cost = get_module_specific_inputs_from_database(
        subscenarios, subproblem, stage, conn)

    with open(os.path.join(inputs_directory,
                           "new_build_transmission_vintage_costs.tab"),
              "w", newline="") as existing_tx_capacity_tab_file:
        writer = csv.writer(existing_tx_capacity_tab_file,
                            delimiter="\t")

        # Write header
        writer.writerow(
            ["transmission_line", "vintage",
             "tx_lifetime_yrs", "tx_annualized_real_cost_per_mw_yr"]
        )

        for row in tx_cost:
            writer.writerow(row)


# TODO: untested
def import_module_specific_results_into_database(
        scenario_id, subproblem, stage, c, db, results_directory
):
    """

    :param scenario_id:
    :param subproblem:
    :param stage:
    :param c:
    :param db:
    :param results_directory:
    :return:
    """
    # New build capacity results
    print("transmission new build")
    # Delete prior results and create temporary import table for ordering
    setup_results_import(
        conn=db, cursor=c,
        table="results_transmission_capacity_new_build",
        scenario_id=scenario_id, subproblem=subproblem, stage=stage
    )

    # Load results into the temporary table
    results = []
    with open(os.path.join(results_directory,
                           "transmission_new_capacity.csv"),
              "r") as capacity_file:
        reader = csv.reader(capacity_file)

        next(reader)  # skip header
        for row in reader:
            transmission_line = row[0]
            period = row[1]
            load_zone_from = row[2]
            load_zone_to = row[3]
            new_build_transmission_capacity_mw = row[4]

            results.append(
                (scenario_id, transmission_line, period, subproblem, stage,
                 load_zone_from, load_zone_to,
                 new_build_transmission_capacity_mw)
            )

    insert_temp_sql = """
        INSERT INTO 
        temp_results_transmission_capacity_new_build{}
        (scenario_id, transmission_line, period, subproblem_id, stage_id, 
        load_zone_from, load_zone_to, 
        new_build_transmission_capacity_mw)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """.format(scenario_id)
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
        """.format(scenario_id)
    spin_on_database_lock(conn=db, cursor=c, sql=insert_sql, data=(),
                          many=False)


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
    # tx_cost = get_module_specific_inputs_from_database(
    #     subscenarios, subproblem, stage, conn)

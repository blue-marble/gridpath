# Copyright 2016-2025 Blue Marble Analytics LLC.
# Copyright 2026 Sylvan Energy Analytics LLC.
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

import csv
import warnings

import numpy as np
import os.path
import pandas as pd
from pyomo.environ import Set

from db.common_functions import spin_on_database_lock
from gridpath.auxiliary.period_wildcards import (
    period_wildcard_rows_sql,
    subproblem_periods_sql,
)
from gridpath.auxiliary.validations import (
    get_projects,
    validate_idxs,
    write_validation_to_database,
)
from gridpath.project.common_functions import get_column_row_value

# The capacity columns of inputs_project_specified_capacity; a row with all
# of them NULL carries no capacity of any kind and is a validation error (a
# project is made absent in a period by omitting its row, never by blanking
# it, so that a NULL has one meaning across the capacity tables)
SPEC_CAPACITY_COLUMNS = [
    "specified_capacity_mw",
    "specified_energy_mwh",
    "shaping_capacity_mw",
    "hyb_gen_specified_capacity_mw",
    "hyb_stor_specified_capacity_mw",
    "specified_stor_capacity_mwh",
    "fuel_production_capacity_fuelunitperhour",
    "fuel_release_capacity_fuelunitperhour",
    "fuel_storage_capacity_fuelunit",
]
SPEC_CAPACITY_BLANK_SQL = "COALESCE({}) IS NULL".format(
    ", ".join(SPEC_CAPACITY_COLUMNS)
)

# The specified capacity and fixed cost tables, which support period wildcard
# rows (see gridpath.auxiliary.period_wildcards), with their subscenario ID
# columns
SPEC_PERIOD_WILDCARD_TABLES = [
    ("inputs_project_specified_capacity", "project_specified_capacity_scenario_id"),
    (
        "inputs_project_specified_fixed_cost",
        "project_specified_fixed_cost_scenario_id",
    ),
]


def spec_period_wildcard_row_filter(subscenarios, scenario_id_column):
    """
    :return: SQL condition selecting the rows of the portfolio's projects in
        the scenario's *scenario_id_column* subscenario
    """
    return f"""{scenario_id_column} =
            {getattr(subscenarios, scenario_id_column.upper())}
            AND project IN (
                SELECT project FROM inputs_project_portfolios
                WHERE project_portfolio_scenario_id =
                {subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID}
            )"""


def relevant_periods_by_project_vintage(
    future_trajectory_periods,
    period_start_year,
    period_end_year,
    vintage,
    lifetime_yrs,
    quiet=False,
):
    """
    :param future_trajectory_periods: the study periods in a list
    :param period_start_year: dictionary of the start year of a period
        by period
    :param period_end_year: dictionary of the end year of a period
        by period
    :param vintage: the project vintage
    :param lifetime_yrs: the project-vintage lifetime
    :param quiet: silence warnings if set to True
    :return: the operational or financial periods given the study periods and
        the project vintage and lifetime

    Note that this function relies on the correct future_trajectory_periods being
    passed to it. We need to pass all the periods that are "connected to"
    (on the same future trajectory) as the project vintage.

    Given the list of periods on the same future trajectory as the project's
    vintage and the project's lifetime (either the operational lifetime or the
    financial lifetime), this function returns the list of periods in which a
    project with this vintage and lifetime will be operational (based on the
    operational lifetime) or incurring an annualized capital cost (based on
    the financial lifetime) respectively. When a project is operational,
    it incurs annual fixed O&M costs.

    Two conditions must be met for a period to be operational / incurring costs for a
    project of a certain vintage:
    1) project vintage (i.e. first operational year) must be before or equal
    to the start year of the period
    2) project last lifetime year must be **after** the period end year.

    The end year of the period is exclusive (i.e. the last day of a period
    with end year 2030 is actually 2020-12-29). With the current
    formulation, a project with a 10 year lifetime of the 2020 vintage is
    assumed to be operational / incurring costs on 2020-01-01 and remain operational
    / incurring costs through 2029-12-31 (vintage 2020, last lifetime year 2030
    exclusive). It will be operational / incurring costs in a period with a start
    year of 2020 and end year of 2030.

    If either the vintage or the last lifetime year is within the period,
    the period is assumed to not be operational / incurring capital costs for the
    project.
    """
    # No relevant periods if vintage does not belong to the vintage's future
    # trajectory periods;
    # this shouldn't happen.
    relevant_periods = list()
    if vintage not in future_trajectory_periods:
        if not quiet:
            warnings.warn(
                f"Vintage {vintage} is not in the future trajectory periods. "
                f"This shouldn't happen."
            )
    else:
        first_lifetime_year = period_start_year[vintage]
        last_lifetime_year = period_start_year[vintage] + lifetime_yrs
        for p in future_trajectory_periods:
            if (
                first_lifetime_year <= period_start_year[p]
                and last_lifetime_year >= period_end_year[p]
            ):
                relevant_periods.append(p)

    return relevant_periods


def project_relevant_periods(
    project_vintages_set, relevant_periods_by_project_vintage_set
):
    """
    :param project_vintages_set: the possible project-vintages when capacity
        can be built
    :param relevant_periods_by_project_vintage_set: the project operational
        periods based on vintage
    :return: all study periods when the project could be operational

    Get the periods in which each project COULD be operational (or incurring
    capital costs) given all project-vintages and relevant periods by
    project-vintage (the lifetime is allowed to differ by vintage).
    """
    return sorted(
        list(
            set(
                (g, p)
                for (g, v) in project_vintages_set
                for p in relevant_periods_by_project_vintage_set[g, v]
            )
        )
    )


def project_vintages_relevant_in_period(
    project_vintage_set, relevant_periods_by_project_vintage_set, period
):
    """
    :param project_vintage_set: possible project-vintages when capacity
        could be built
    :param relevant_periods_by_project_vintage_set: the periods when
        project capacity of a particular vintage could be operational (or incurring
        capital costs)
    :param period: the period we're in
    :return: all vintages that could be operational (or incurring capital costs) in a
        period

    Get the project vintages that COULD be operational (or incurring capital costs) in
    each period.
    """
    project_vintages = list()
    for prj, v in project_vintage_set:
        if period in relevant_periods_by_project_vintage_set[prj, v]:
            project_vintages.append((prj, v))

    return project_vintages


# New-build projects common functions
def add_vintage_period_sets(
    m, prefix, operational_lifetime, financial_lifetime, in_period_suffix
):
    """
    :param m: the Pyomo abstract model
    :param prefix: the prefix of the capacity type's set names, e.g.
        GEN_NEW_LIN; the project-vintages set is :code:`{prefix}_VNTS`
    :param operational_lifetime: the name of the capacity type's operational
        lifetime param, indexed by project-vintage
    :param financial_lifetime: the name of the capacity type's financial
        lifetime param, indexed by project-vintage
    :param in_period_suffix: the suffix of the names of the period-indexed
        sets of vintages (PERIOD or PRD)

    Add the derived operational and financial period sets of a new-build
    capacity type: by project-vintage (:code:`OPR_PRDS_BY_{prefix}_VINTAGE`,
    :code:`FIN_PRDS_BY_{prefix}_VINTAGE`), by project
    (:code:`{prefix}_OPR_PRDS`, :code:`{prefix}_FIN_PRDS`), and the
    project-vintages operational (incurring capital costs) in each period
    (:code:`{prefix}_VNTS_OPR_IN_{in_period_suffix}`,
    :code:`{prefix}_VNTS_FIN_IN_{in_period_suffix}`). The periods of a
    vintage are determined by :code:`relevant_periods_by_project_vintage`
    with the operational and the financial lifetime respectively.
    """
    add_relevant_period_sets(m, prefix, "OPR", operational_lifetime, in_period_suffix)
    add_relevant_period_sets(m, prefix, "FIN", financial_lifetime, in_period_suffix)


def add_relevant_period_sets(m, prefix, kind, lifetime, in_period_suffix):
    """
    Add the operational (*kind* OPR) or financial (*kind* FIN) period sets
    of a new-build capacity type, determined with the *lifetime* param; see
    :code:`add_vintage_period_sets`.
    """
    vintages = f"{prefix}_VNTS"
    by_vintage = f"{kind}_PRDS_BY_{prefix}_VINTAGE"

    def periods_by_vintage(mod, prj, v):
        return relevant_periods_by_project_vintage(
            future_trajectory_periods=mod.PERIOD_FUTURE_TRAJECTORY[v],
            period_start_year=mod.period_start_year,
            period_end_year=mod.period_end_year,
            vintage=v,
            lifetime_yrs=getattr(mod, lifetime)[prj, v],
        )

    def periods_by_project(mod):
        return project_relevant_periods(
            project_vintages_set=getattr(mod, vintages),
            relevant_periods_by_project_vintage_set=getattr(mod, by_vintage),
        )

    def vintages_in_period(mod, p):
        return project_vintages_relevant_in_period(
            project_vintage_set=getattr(mod, vintages),
            relevant_periods_by_project_vintage_set=getattr(mod, by_vintage),
            period=p,
        )

    m.add_component(
        by_vintage, Set(getattr(m, vintages), initialize=periods_by_vintage)
    )
    m.add_component(
        f"{prefix}_{kind}_PRDS", Set(dimen=2, initialize=periods_by_project)
    )
    m.add_component(
        f"{prefix}_VNTS_{kind}_IN_{in_period_suffix}",
        Set(m.PERIODS, dimen=2, initialize=vintages_in_period),
    )


def new_build_vintage_rows_sql(subscenarios, capacity_types, columns):
    """
    :param subscenarios: SubScenarios object with all subscenario info
    :param capacity_types: the new-build capacity types
    :param columns: the columns of inputs_project_new_cost to select, in
        order, after project and vintage
    :return: SQL selecting project, vintage and *columns* of the
        inputs_project_new_cost rows of the portfolio's projects of
        *capacity_types*, for the vintages that are periods of the
        temporal scenario
    """
    column_list = ",\n        ".join(columns)
    capacity_type_list = ", ".join(f"'{c}'" for c in capacity_types)
    return f"""SELECT project, vintage, {column_list}
        FROM inputs_project_portfolios
        CROSS JOIN
        (SELECT period AS vintage
        FROM inputs_temporal_periods
        WHERE temporal_scenario_id = {subscenarios.TEMPORAL_SCENARIO_ID}
        ) as relevant_vintages
        INNER JOIN
        (SELECT project, vintage, {column_list}
        FROM inputs_project_new_cost
        WHERE project_new_cost_scenario_id =
        {subscenarios.PROJECT_NEW_COST_SCENARIO_ID}) as cost
        USING (project, vintage)
        WHERE project_portfolio_scenario_id =
        {subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID}
        AND capacity_type IN ({capacity_type_list})"""


# Specified projects common functions
SPEC_FIXED_COST_COLUMNS = [
    "fixed_cost_per_mw_yr",
    "fixed_cost_per_energy_mwh_yr",
    "fixed_cost_per_shaping_mw_yr",
    "hyb_gen_fixed_cost_per_mw_yr",
    "hyb_stor_fixed_cost_per_mw_yr",
    "fixed_cost_per_stor_mwh_yr",
    "fuel_release_capacity_fixed_cost_per_fuelunitperhour_yr",
    "fuel_production_capacity_fixed_cost_per_fuelunitperhour_yr",
    "fuel_storage_capacity_fixed_cost_per_fuelunit_yr",
]


# The capacity types whose capacity is given in the specified capacity
# inputs (see spec_get_inputs_from_database); a project of these types is
# operational only in the periods with a specified capacity row
SPEC_CAPACITY_TYPES = [
    "energy_spec",
    "fuel_prod_spec",
    "gen_ret_bin",
    "gen_ret_lin",
    "gen_spec",
    "gen_stor_hyb_spec",
    "stor_spec",
]


def spec_capacity_rows_sql(subscenarios, subproblem, capacity_types):
    """
    :param subproblem: the subproblem ID in the database
    :param capacity_types: the specified capacity types to select
    :return: SQL selecting the project, period, and capacity columns
        (:code:`SPEC_CAPACITY_COLUMNS`) of the portfolio projects of
        *capacity_types* in the subproblem's periods, with period = 0 rows
        applying to every period. These rows are the projects' operational
        periods in the model, so the operational characteristics inputs are
        written for these periods only (see
        :code:`spec_non_operational_periods_sql`).
    """
    capacity_sql = period_wildcard_rows_sql(
        table="inputs_project_specified_capacity",
        columns=["project", "period"] + SPEC_CAPACITY_COLUMNS,
        key_columns=["project", "project_specified_capacity_scenario_id"],
        row_filter=f"project_specified_capacity_scenario_id = "
        f"{subscenarios.PROJECT_SPECIFIED_CAPACITY_SCENARIO_ID}",
        periods_sql=subproblem_periods_sql(
            subscenarios.TEMPORAL_SCENARIO_ID, subproblem
        ),
    )
    capacity_types_sql = ", ".join(f"'{t}'" for t in capacity_types)
    return f"""
        SELECT project, period, {", ".join(SPEC_CAPACITY_COLUMNS)}
        FROM inputs_project_portfolios
        CROSS JOIN
        (SELECT period
        FROM inputs_temporal_periods
        WHERE temporal_scenario_id = {subscenarios.TEMPORAL_SCENARIO_ID}) as relevant_periods
        INNER JOIN
        ({capacity_sql}) as capacity
        USING (project, period)
        WHERE project_portfolio_scenario_id = {subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID}
        AND capacity_type IN ({capacity_types_sql})
        AND period in (
                  SELECT DISTINCT period
                  FROM inputs_temporal
                  WHERE temporal_scenario_id = {subscenarios.TEMPORAL_SCENARIO_ID}
                  AND subproblem_id = {subproblem}
               )
        """


def spec_non_operational_periods_sql(subscenarios, subproblem):
    """
    :param subproblem: the subproblem ID in the database
    :return: SQL selecting the (project, period)s of the subproblem's
        periods in which a portfolio project of a specified capacity type is
        not operational, i.e. has no row in :code:`spec_capacity_rows_sql`
    """
    capacity_types_sql = ", ".join(f"'{t}'" for t in SPEC_CAPACITY_TYPES)
    periods_sql = subproblem_periods_sql(subscenarios.TEMPORAL_SCENARIO_ID, subproblem)
    capacity_sql = spec_capacity_rows_sql(
        subscenarios=subscenarios,
        subproblem=subproblem,
        capacity_types=SPEC_CAPACITY_TYPES,
    )
    return f"""
        SELECT project, period
        FROM inputs_project_portfolios
        CROSS JOIN ({periods_sql}) AS subproblem_periods
        WHERE project_portfolio_scenario_id = {subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID}
        AND capacity_type IN ({capacity_types_sql})
        EXCEPT
        SELECT project, period
        FROM ({capacity_sql})
        """


def spec_projects_not_operational_sql(subscenarios, subproblem):
    """
    :param subproblem: the subproblem ID in the database
    :return: SQL selecting the portfolio projects of the specified capacity
        types that aren't operational in any of the subproblem's periods,
        i.e. have no row in :code:`spec_capacity_rows_sql`
    """
    capacity_types_sql = ", ".join(f"'{t}'" for t in SPEC_CAPACITY_TYPES)
    capacity_sql = spec_capacity_rows_sql(
        subscenarios=subscenarios,
        subproblem=subproblem,
        capacity_types=SPEC_CAPACITY_TYPES,
    )
    return f"""
        SELECT project
        FROM inputs_project_portfolios
        WHERE project_portfolio_scenario_id = {subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID}
        AND capacity_type IN ({capacity_types_sql})
        EXCEPT
        SELECT project FROM ({capacity_sql})
        """


def spec_get_inputs_from_database(conn, subscenarios, subproblem, capacity_type):
    """
    Get the various capacity and fixed cost parameters for projects with
    "specified" capacity types.
    """
    db_subproblem = subproblem if subproblem != "" else 1

    # Capacity rows (see spec_capacity_rows_sql), which define the projects'
    # operational periods, and fixed costs with period = 0 rows applying to
    # every period
    capacity_sql = spec_capacity_rows_sql(
        subscenarios=subscenarios,
        subproblem=db_subproblem,
        capacity_types=[capacity_type],
    )
    fixed_cost_sql = period_wildcard_rows_sql(
        table="inputs_project_specified_fixed_cost",
        columns=["project", "period"] + SPEC_FIXED_COST_COLUMNS,
        key_columns=["project", "project_specified_fixed_cost_scenario_id"],
        row_filter=f"project_specified_fixed_cost_scenario_id = "
        f"{subscenarios.PROJECT_SPECIFIED_FIXED_COST_SCENARIO_ID}",
        periods_sql=subproblem_periods_sql(
            subscenarios.TEMPORAL_SCENARIO_ID, db_subproblem
        ),
    )

    c = conn.cursor()
    spec_project_params = c.execute(f"""
        SELECT project,
        period,
        specified_capacity_mw,
        specified_energy_mwh,
        shaping_capacity_mw,
        hyb_gen_specified_capacity_mw,
        hyb_stor_specified_capacity_mw,
        specified_stor_capacity_mwh,
        fuel_production_capacity_fuelunitperhour,
        fuel_release_capacity_fuelunitperhour,
        fuel_storage_capacity_fuelunit,
        fixed_cost_per_mw_yr,
        fixed_cost_per_energy_mwh_yr,
        fixed_cost_per_shaping_mw_yr,
        hyb_gen_fixed_cost_per_mw_yr,
        hyb_stor_fixed_cost_per_mw_yr,
        fixed_cost_per_stor_mwh_yr,
        fuel_release_capacity_fixed_cost_per_fuelunitperhour_yr,
        fuel_production_capacity_fixed_cost_per_fuelunitperhour_yr,
        fuel_storage_capacity_fixed_cost_per_fuelunit_yr
        FROM ({capacity_sql}) as capacity
        LEFT JOIN -- operational periods are based on capacity; fixed costs are optional
        ({fixed_cost_sql}) as fixed_om
        USING (project, period)
        ;""")

    return spec_project_params


def validate_spec_capacity_coverage(
    conn,
    scenario_id,
    subscenarios,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    gridpath_module,
    capacity_type,
):
    """
    Check the period coverage of the specified-capacity rows of the
    portfolio's projects of this capacity type and write the findings to the
    validation table.

    A project is operational in exactly the periods for which it has a row in
    ``inputs_project_specified_capacity``, or in every period if its row is
    for period 0. Leaving periods out is the intended way to model a project
    that retires, or comes online, within the study horizon, and a project
    may have no row at all in the periods of a given subproblem, so that one
    specified-capacity subscenario can serve runs over different horizons.
    Two High-severity errors: a project with no row in any period of the
    subscenario, as that is most likely a naming mismatch between the
    portfolio and the capacity inputs, and a row with every capacity column
    NULL, which carries no capacity of any kind; a blank row is not how a
    project is made absent (omit the row instead), and a NULL would otherwise
    mean "absent" here and "no limit" in the transmission capacity table.
    Two Low-severity notes flag the cases worth a second look: a project
    with capacity in none of this subproblem's periods, which will not be
    in the model at all, and a project whose coverage of this subproblem's
    periods has a gap between two covered periods.

    :param conn: database connection
    :param scenario_id:
    :param subscenarios: SubScenarios object with all subscenario info
    :param weather_iteration:
    :param hydro_iteration:
    :param availability_iteration:
    :param subproblem:
    :param stage:
    :param gridpath_module: the name of the module running the validation
    :param capacity_type: the capacity type whose projects to check
    :return:
    """
    db_subproblem = subproblem if subproblem != "" else 1

    projects = get_projects(
        conn, scenario_id, subscenarios, "capacity_type", capacity_type
    )

    c = conn.cursor()
    capacity_periods_sql = f"""
        SELECT project, period
        FROM inputs_project_specified_capacity
        WHERE project_specified_capacity_scenario_id =
        {subscenarios.PROJECT_SPECIFIED_CAPACITY_SCENARIO_ID}
        ;"""
    periods_by_project = dict()
    for project, period in c.execute(capacity_periods_sql).fetchall():
        periods_by_project.setdefault(project, set()).add(period)

    blank_rows = [
        (project, period) for project, period in c.execute(f"""SELECT project, period
            FROM inputs_project_specified_capacity
            WHERE project_specified_capacity_scenario_id =
            {subscenarios.PROJECT_SPECIFIED_CAPACITY_SCENARIO_ID}
            AND {SPEC_CAPACITY_BLANK_SQL}
            ORDER BY project, period;""").fetchall() if project in projects
    ]

    # The same period scoping as spec_get_inputs_from_database
    subproblem_periods = sorted(
        period
        for (period,) in c.execute(
            subproblem_periods_sql(subscenarios.TEMPORAL_SCENARIO_ID, db_subproblem)
        ).fetchall()
    )

    def write(severity, errors):
        write_validation_to_database(
            conn=conn,
            scenario_id=scenario_id,
            weather_iteration=weather_iteration,
            hydro_iteration=hydro_iteration,
            availability_iteration=availability_iteration,
            subproblem_id=subproblem,
            stage_id=stage,
            gridpath_module=gridpath_module,
            db_table="inputs_project_specified_capacity",
            severity=severity,
            errors=errors,
        )

    # A project with no capacity row in any period is most likely a naming
    # mismatch between the portfolio and the capacity inputs
    write(
        severity="High",
        errors=validate_idxs(
            actual_idxs=list(periods_by_project.keys()),
            req_idxs=projects,
            idx_label="project",
            msg="Expected specified capacity in at least one period.",
        ),
    )

    # A blank row carries no capacity of any kind; the project is made absent
    # in a period by omitting the row, not by blanking it
    write(
        severity="High",
        errors=(
            [
                "Specified capacity row(s) with every capacity column blank for "
                "(project, period): {}. A blank row is not allowed: omit the row "
                "to make the project absent in that period, or give it a "
                "capacity (zero keeps it in the model at zero capacity).".format(
                    blank_rows
                )
            ]
            if blank_rows
            else []
        ),
    )

    not_operational = list()
    gaps = dict()
    for project in sorted(projects):
        if project not in periods_by_project:
            continue
        # A period 0 row covers every period
        project_periods = periods_by_project[project]
        if 0 in project_periods:
            continue
        covered = [p for p in subproblem_periods if p in project_periods]
        if not covered:
            not_operational.append(project)
            continue
        uncovered_between = [
            p
            for p in subproblem_periods
            if covered[0] < p < covered[-1] and p not in project_periods
        ]
        if uncovered_between:
            gaps[project] = uncovered_between

    errors = list()
    if not_operational:
        errors.append(
            "No specified capacity in any period of this subproblem for "
            "project: {}. These projects will not be operational (i.e., "
            "they will not be in the model) in this subproblem.".format(not_operational)
        )
    if gaps:
        errors.append(
            "Non-contiguous specified capacity for project: {}. The periods "
            "listed have no capacity row but fall between periods that do; "
            "the project will not be operational in them.".format(gaps)
        )
    write(severity="Low", errors=errors)


def spec_write_tab_file(
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    spec_project_params,
):
    spec_params_filepath = os.path.join(
        scenario_directory,
        weather_iteration,
        hydro_iteration,
        availability_iteration,
        subproblem,
        stage,
        "inputs",
        "spec_capacity_period_params.tab",
    )
    # If spec_capacity_period_params.tab file already exists, append
    # rows to it
    if os.path.isfile(spec_params_filepath):
        with open(spec_params_filepath, "a") as f:
            writer_a = csv.writer(f, delimiter="\t", lineterminator="\n")
            write_from_query(spec_project_params=spec_project_params, writer=writer_a)
    # If spec_capacity_period_params.tab file does not exist,
    # write header first, then add input data
    else:
        with open(spec_params_filepath, "w", newline="") as f:
            writer_w = csv.writer(f, delimiter="\t", lineterminator="\n")
            # Write header
            writer_w.writerow(
                [
                    "project",
                    "period",
                    "specified_capacity_mw",
                    "specified_energy_mwh",
                    "shaping_capacity_mw",
                    "hyb_gen_specified_capacity_mw",
                    "hyb_stor_specified_capacity_mw",
                    "specified_stor_capacity_mwh",
                    "fuel_production_capacity_fuelunitperhour",
                    "fuel_release_capacity_fuelunitperhour",
                    "fuel_storage_capacity_fuelunit",
                    "fixed_cost_per_mw_yr",
                    "fixed_cost_per_energy_mwh_yr",
                    "fixed_cost_per_shaping_mw_yr",
                    "hyb_gen_fixed_cost_per_mw_yr",
                    "hyb_stor_fixed_cost_per_mw_yr",
                    "fixed_cost_per_stor_mwh_yr",
                    "fuel_production_capacity_fixed_cost_per_fuelunitperhour_yr",
                    "fuel_release_capacity_fixed_cost_per_fuelunitperhour_yr",
                    "fuel_storage_capacity_fixed_cost_per_fuelunit_yr",
                ]
            )

            # Write input data
            write_from_query(spec_project_params=spec_project_params, writer=writer_w)


def write_from_query(spec_project_params, writer):
    """
    Helper function for writing the spec project param inputs to avoid
    redundant code in spec_write_tab_file().
    """
    for row in spec_project_params:
        [
            project,
            period,
            specified_capacity_mw,
            specified_energy_mwh,
            shaping_capacity_mw,
            hyb_gen_specified_capacity_mw,
            hyb_stor_specified_capacity_mw,
            specified_stor_capacity_mwh,
            fuel_prod_cap,
            fuel_rel_cap,
            fuel_stor_cap,
            fixed_cost_per_mw_yr,
            fixed_cost_per_energy_mwh_yr,
            fixed_cost_per_shaping_mw_yr,
            hyb_gen_fixed_cost_per_mw_yr,
            hyb_stor_fixed_cost_per_mw_yr,
            fixed_cost_per_stor_mwh_yr,
            fuel_prod_fom,
            fuel_rel_fom,
            fuel_stor_fom,
        ] = row
        writer.writerow(
            [
                project,
                period,
                specified_capacity_mw,
                specified_energy_mwh,
                shaping_capacity_mw,
                hyb_gen_specified_capacity_mw,
                hyb_stor_specified_capacity_mw,
                specified_stor_capacity_mwh,
                fuel_prod_cap,
                fuel_rel_cap,
                fuel_stor_cap,
                fixed_cost_per_mw_yr,
                fixed_cost_per_energy_mwh_yr,
                fixed_cost_per_shaping_mw_yr,
                hyb_gen_fixed_cost_per_mw_yr,
                hyb_stor_fixed_cost_per_mw_yr,
                fixed_cost_per_stor_mwh_yr,
                fuel_prod_fom,
                fuel_rel_fom,
                fuel_stor_fom,
            ]
        )


def spec_determine_inputs(
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    capacity_type,
):
    # Determine the relevant projects
    project_list = list()

    df = pd.read_csv(
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
        usecols=["project", "capacity_type"],
    )

    for row in zip(df["project"], df["capacity_type"]):
        if row[1] == capacity_type:
            project_list.append(row[0])

    # Determine the operational periods & params for each project/period
    project_period_list = list()
    spec_capacity_mw_dict = dict()
    specified_energy_mwh_dict = dict()
    shaping_capacity_mw_dict = dict()
    hyb_gen_spec_capacity_mw_dict = dict()
    hyb_stor_spec_capacity_mw_dict = dict()
    spec_capacity_mwh_dict = dict()
    spec_fuel_prod_cap_dict = dict()
    spec_fuel_rel_cap_dict = dict()
    spec_fuel_stor_cap_dict = dict()
    spec_fixed_cost_per_mw_yr_dict = dict()
    fixed_cost_per_energy_mwh_yr_dict = dict()
    fixed_cost_per_shaping_mw_yr_dict = dict()
    hyb_gen_spec_fixed_cost_per_mw_yr_dict = dict()
    hyb_stor_spec_fixed_cost_per_mw_yr_dict = dict()
    spec_fixed_cost_per_stor_mwh_yr_dict = dict()
    spec_fuel_prod_fixed_cost_dict = dict()
    spec_fuel_rel_fixed_cost_dict = dict()
    spec_fuel_stor_fixed_cost_dict = dict()

    df = pd.read_csv(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "spec_capacity_period_params.tab",
        ),
        sep="\t",
    )

    for row in zip(
        df["project"],
        df["period"],
        df["specified_capacity_mw"],
        df["specified_energy_mwh"],
        df["shaping_capacity_mw"],
        df["hyb_gen_specified_capacity_mw"],
        df["hyb_stor_specified_capacity_mw"],
        df["specified_stor_capacity_mwh"],
        df["fuel_production_capacity_fuelunitperhour"],
        df["fuel_release_capacity_fuelunitperhour"],
        df["fuel_storage_capacity_fuelunit"],
        df["fixed_cost_per_mw_yr"],
        df["fixed_cost_per_energy_mwh_yr"],
        df["fixed_cost_per_shaping_mw_yr"],
        df["hyb_gen_fixed_cost_per_mw_yr"],
        df["hyb_stor_fixed_cost_per_mw_yr"],
        df["fixed_cost_per_stor_mwh_yr"],
        df["fuel_production_capacity_fixed_cost_per_fuelunitperhour_yr"],
        df["fuel_release_capacity_fixed_cost_per_fuelunitperhour_yr"],
        df["fuel_storage_capacity_fixed_cost_per_fuelunit_yr"],
    ):
        if row[0] in project_list:
            project_period_list.append((row[0], row[1]))
            spec_capacity_mw_dict[(row[0], row[1])] = row[2]
            specified_energy_mwh_dict[(row[0], row[1])] = row[3]
            shaping_capacity_mw_dict[(row[0], row[1])] = row[4]
            hyb_gen_spec_capacity_mw_dict[(row[0], row[1])] = row[5]
            hyb_stor_spec_capacity_mw_dict[(row[0], row[1])] = row[6]
            spec_capacity_mwh_dict[(row[0], row[1])] = row[7]
            spec_fuel_prod_cap_dict[(row[0], row[1])] = row[8]
            spec_fuel_rel_cap_dict[(row[0], row[1])] = row[9]
            spec_fuel_stor_cap_dict[(row[0], row[1])] = row[10]
            spec_fixed_cost_per_mw_yr_dict[(row[0], row[1])] = row[11]
            fixed_cost_per_energy_mwh_yr_dict[(row[0], row[1])] = row[12]
            fixed_cost_per_shaping_mw_yr_dict[(row[0], row[1])] = row[13]
            hyb_gen_spec_fixed_cost_per_mw_yr_dict[(row[0], row[1])] = row[14]
            hyb_stor_spec_fixed_cost_per_mw_yr_dict[(row[0], row[1])] = row[15]
            spec_fixed_cost_per_stor_mwh_yr_dict[(row[0], row[1])] = row[16]
            spec_fuel_prod_fixed_cost_dict[(row[0], row[1])] = row[17]
            spec_fuel_rel_fixed_cost_dict[(row[0], row[1])] = row[18]
            spec_fuel_stor_fixed_cost_dict[(row[0], row[1])] = row[19]

    # A project with no rows here (none in the subproblem's periods, or only
    # rows with every capacity column blank) is simply not operational in
    # this subproblem, e.g. it retires before, or comes online after, the
    # subproblem's periods; validate_spec_capacity_coverage reports it

    # For fixed costs, remove the NAs (set to "."); these default to zero in
    # the model formulation
    def remove_nan_values_from_dict(d):
        return {k: v for k, v in d.items() if not np.isnan(v)}

    main_dict = dict()
    main_dict["specified_capacity_mw"] = spec_capacity_mw_dict
    main_dict["specified_energy_mwh"] = specified_energy_mwh_dict
    main_dict["shaping_capacity_mw"] = remove_nan_values_from_dict(
        shaping_capacity_mw_dict
    )
    main_dict["hyb_gen_specified_capacity_mw"] = hyb_gen_spec_capacity_mw_dict
    main_dict["hyb_stor_specified_capacity_mw"] = hyb_stor_spec_capacity_mw_dict
    main_dict["specified_stor_capacity_mwh"] = spec_capacity_mwh_dict
    main_dict["fuel_production_capacity_fuelunitperhour"] = spec_fuel_prod_cap_dict
    main_dict["fuel_release_capacity_fuelunitperhour"] = spec_fuel_rel_cap_dict
    main_dict["fuel_storage_capacity_fuelunit"] = spec_fuel_stor_cap_dict

    main_dict["fixed_cost_per_mw_yr"] = remove_nan_values_from_dict(
        spec_fixed_cost_per_mw_yr_dict
    )
    main_dict["fixed_cost_per_energy_mwh_yr"] = remove_nan_values_from_dict(
        fixed_cost_per_energy_mwh_yr_dict
    )
    main_dict["fixed_cost_per_shaping_mw_yr"] = remove_nan_values_from_dict(
        fixed_cost_per_shaping_mw_yr_dict
    )
    main_dict["hyb_gen_fixed_cost_per_mw_yr"] = remove_nan_values_from_dict(
        hyb_gen_spec_fixed_cost_per_mw_yr_dict
    )
    main_dict["hyb_stor_fixed_cost_per_mw_yr"] = remove_nan_values_from_dict(
        hyb_stor_spec_fixed_cost_per_mw_yr_dict
    )
    main_dict["fixed_cost_per_stor_mwh_yr"] = remove_nan_values_from_dict(
        spec_fixed_cost_per_stor_mwh_yr_dict
    )
    main_dict["fuel_production_capacity_fixed_cost_per_fuelunitperhour_yr"] = (
        remove_nan_values_from_dict(spec_fuel_prod_fixed_cost_dict)
    )

    main_dict["fuel_release_capacity_fixed_cost_per_fuelunitperhour_yr"] = (
        remove_nan_values_from_dict(spec_fuel_rel_fixed_cost_dict)
    )

    main_dict["fuel_storage_capacity_fixed_cost_per_fuelunit_yr"] = (
        remove_nan_values_from_dict(spec_fuel_stor_fixed_cost_dict)
    )

    return project_period_list, main_dict


def read_results_file_generic(
    scenario_directory,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    capacity_type,
):
    """
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param capacity_type:
    :return:
    """

    # Get the results CSV as dataframe
    df = pd.read_csv(
        os.path.join(
            scenario_directory,
            weather_iteration,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "results",
            "project_period.csv",
        )
    )

    # Filter by capacity type and aggregate by technology
    capacity_results_agg_df = (
        df.loc[df["capacity_type"] == capacity_type]
        .groupby(by=["load_zone", "technology", "period"], as_index=True)
        .sum(numeric_only=True)
    )

    return capacity_results_agg_df


def write_summary_results_generic(
    results_df, columns, summary_results_file, title, empty_title
):
    # Rename column header
    results_df.columns = columns

    with open(summary_results_file, "a") as outfile:
        outfile.write(f"\n--> {title} <--\n")
        if results_df.empty:
            outfile.write(f"{empty_title}\n")
        else:
            results_df.to_string(outfile, float_format="{:,.2f}".format)
            outfile.write("\n")


def get_units(scenario_directory):
    units_df = pd.read_csv(
        os.path.join(scenario_directory, "units.csv"), index_col="metric"
    )
    power_unit = units_df.loc["power", "unit"]
    energy_unit = units_df.loc["energy", "unit"]
    fuel_unit = units_df.loc["fuel_energy", "unit"]

    return power_unit, energy_unit, fuel_unit

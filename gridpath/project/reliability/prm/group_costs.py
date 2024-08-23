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
Building "transmission" capacity to allow for project capacity to count as
deliverable for PRM purposes OR for energy-only purposes even if the PRM "deliverable"
capacity is not increased. Note that this is  not transmission for the purposes of
power flow in the model, so we will also call it "deliverability" capacity. There is
currently no distinction between the operational and financial lifetime of this
"deliverability" capacity (like we have for projects).
"""

import csv
import os.path
from pyomo.environ import (
    Set,
    Var,
    Expression,
    Param,
    Constraint,
    NonNegativeReals,
    Reals,
    value,
)

from gridpath.auxiliary.db_interface import import_csv
from gridpath.project.capacity.capacity_types.common_methods import (
    project_vintages_relevant_in_period,
    relevant_periods_by_project_vintage,
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

    :param m:
    :param d:
    :return:
    """
    # Costs for having fully deliverable capacity by project group
    # We'll need to figure out how much capacity is built in groups of
    # projects, not by individual project
    # These are the periods when ca
    m.DELIVERABILITY_GROUP_VINTAGES = Set(dimen=2)

    m.DELIVERABILITY_GROUPS = Set(
        initialize=lambda mod: list(
            set([g for (g, v) in mod.DELIVERABILITY_GROUP_VINTAGES])
        )
    )

    # How long the "deliverability" capacity remains operational AND incurs annual costs
    # Defaults to infinity, i.e., the full study period.
    m.deliverability_lifetime_yrs = Param(
        m.DELIVERABILITY_GROUP_VINTAGES, within=NonNegativeReals, default=float("inf")
    )
    # Cost for building "deliverability" capacity of each vintage
    m.deliverability_cost_per_mw_yr = Param(
        m.DELIVERABILITY_GROUP_VINTAGES, within=NonNegativeReals
    )

    # We'll also constrain how much deliverability can be built in each group
    # This is a cumulative capacity limit for each vintage
    m.deliverable_capacity_limit_mw = Param(
        m.DELIVERABILITY_GROUPS,
        m.PERIODS,
        within=NonNegativeReals,
        default=float("inf"),
    )

    # ### Derived sets for capacity and cost tracking ###
    def operational_periods_by_group_vintage(mod, g, v):
        return relevant_periods_by_project_vintage(
            periods=getattr(mod, "PERIODS"),
            period_start_year=getattr(mod, "period_start_year"),
            period_end_year=getattr(mod, "period_end_year"),
            vintage=v,
            lifetime_yrs=mod.deliverability_lifetime_yrs[g, v],
        )

    m.OPR_PRDS_BY_GROUP_VINTAGE = Set(
        m.DELIVERABILITY_GROUP_VINTAGES, initialize=operational_periods_by_group_vintage
    )

    def deliverability_vintages_operational_in_period(mod, p):
        return project_vintages_relevant_in_period(
            project_vintage_set=mod.DELIVERABILITY_GROUP_VINTAGES,
            relevant_periods_by_project_vintage_set=mod.OPR_PRDS_BY_GROUP_VINTAGE,
            period=p,
        )

    m.GROUP_VNTS_OPR_IN_PERIOD = Set(
        m.PERIODS, dimen=2, initialize=deliverability_vintages_operational_in_period
    )

    # GROUP PROJECTS #
    # Limit this to EOA_PRM_PROJECTS; if another project is
    # included, we need to throw an error
    m.DELIVERABILITY_GROUP_PROJECTS = Set(
        dimen=2, within=m.DELIVERABILITY_GROUPS * m.EOA_PRM_PROJECTS
    )

    m.PROJECTS_BY_DELIVERABILITY_GROUP = Set(
        m.DELIVERABILITY_GROUPS,
        within=m.EOA_PRM_PROJECTS,
        initialize=lambda mod, g: [
            p for (group, p) in mod.DELIVERABILITY_GROUP_PROJECTS if group == g
        ],
    )

    # Multipliers for the constraint types and peak designations
    m.PROJECT_CONSTRAINT_TYPE_PEAK_DESIGNATIONS = Set(dimen=3)
    m.peak_designation_multiplier = Param(
        m.PROJECT_CONSTRAINT_TYPE_PEAK_DESIGNATIONS, within=Reals
    )
    # Constraints can be applied on the total project capacity, the deliverable (for
    # PRM purposes) capacity or the energy-only (for PRM purposes) capacity.
    m.CONSTRAINT_TYPES = Set(
        initialize=lambda mod: list(
            set([t for (prj, t, _d) in mod.PROJECT_CONSTRAINT_TYPE_PEAK_DESIGNATIONS])
        ),
        within=["total", "deliverable", "energy_only"],
    )
    # Depending on load conditions, we can expect different capacity factors from the
    # deliverable capacity (i.e., different transmission needs) and we can apply
    # several constraints with different cap factors (multipliers), as we may not
    # know which one will bind ahead of time
    m.PEAK_DESIGNATIONS = Set(
        initialize=lambda mod: list(
            set([_d for (prj, t, _d) in mod.PROJECT_CONSTRAINT_TYPE_PEAK_DESIGNATIONS])
        )
    )

    # Existing deliverability
    m.existing_deliverability_mw = Param(
        m.DELIVERABILITY_GROUPS,
        m.PERIODS,
        m.CONSTRAINT_TYPES,
        m.PEAK_DESIGNATIONS,
        within=NonNegativeReals,
        default=0,
    )

    # Expressions to use in constraints by type and peak designation
    def total_project_capacity_in_group_init(
        mod, g, period, constraint_type, peak_designation
    ):
        """
        :param mod:
        :param g:
        :param period:
        :param constraint_type:
        :param peak_designation:
        :return:
        """
        if constraint_type == "total":
            return sum(
                mod.Capacity_MW[prj, p]
                * mod.peak_designation_multiplier[
                    prj, constraint_type, peak_designation
                ]
                for (prj, p) in mod.EOA_PRM_PRJ_OPR_PRDS
                if p == period
                and prj in mod.PROJECTS_BY_DELIVERABILITY_GROUP[g]
                and (prj, constraint_type, peak_designation)
                in mod.PROJECT_CONSTRAINT_TYPE_PEAK_DESIGNATIONS
            )

    m.Group_Total_Project_Capacity_MW = Expression(
        m.DELIVERABILITY_GROUPS,
        m.PERIODS,
        m.CONSTRAINT_TYPES,
        m.PEAK_DESIGNATIONS,
        initialize=total_project_capacity_in_group_init,
    )

    def deliverable_project_capacity_in_group_init(
        mod, g, period, constraint_type, peak_designation
    ):
        """
        :param mod:
        :param g:
        :param period:
        :param constraint_type:
        :param peak_designation:
        :return:
        """
        if constraint_type == "deliverable":
            return sum(
                mod.Deliverable_Capacity_MW[prj, p]
                * mod.peak_designation_multiplier[
                    prj, constraint_type, peak_designation
                ]
                for (prj, p) in mod.EOA_PRM_PRJ_OPR_PRDS
                if p == period
                and prj in mod.PROJECTS_BY_DELIVERABILITY_GROUP[g]
                and (prj, constraint_type, peak_designation)
                in mod.PROJECT_CONSTRAINT_TYPE_PEAK_DESIGNATIONS
            )

    m.Group_Deliverable_Project_Capacity_MW = Expression(
        m.DELIVERABILITY_GROUPS,
        m.PERIODS,
        m.CONSTRAINT_TYPES,
        m.PEAK_DESIGNATIONS,
        initialize=deliverable_project_capacity_in_group_init,
    )

    def energy_only_project_capacity_in_group_init(
        mod, g, period, constraint_type, peak_designation
    ):
        """
        Energy-only capacity of projects in each deliverability group
        :param mod:
        :param g:
        :param period:
        :return:
        """
        if constraint_type == "energy_only":
            return sum(
                mod.Energy_Only_Capacity_MW[prj, p]
                * mod.peak_designation_multiplier[
                    prj, constraint_type, peak_designation
                ]
                for (prj, p) in mod.EOA_PRM_PRJ_OPR_PRDS
                if p == period
                and prj in mod.PROJECTS_BY_DELIVERABILITY_GROUP[g]
                and (prj, constraint_type, peak_designation)
                in mod.PROJECT_CONSTRAINT_TYPE_PEAK_DESIGNATIONS
            )

    m.Group_Energy_Only_Project_Capacity_MW = Expression(
        m.DELIVERABILITY_GROUPS,
        m.PERIODS,
        m.CONSTRAINT_TYPES,
        m.PEAK_DESIGNATIONS,
        initialize=energy_only_project_capacity_in_group_init,
    )

    # Variables
    m.Deliverability_Group_Build_MW = Var(
        m.DELIVERABILITY_GROUP_VINTAGES, within=NonNegativeReals
    )

    def group_capacity_rule(mod, g, p):
        """
        **Expression Name**: Cumulative_Added_Deliverability_Capacity_MW
        **Enforced Over**: (m.DELIVERABILITY_GROUPS, m.PERIODS(
        **Defaults to**: 0

        The capacity for group deliverability in a given operational period is
        equal to the sum of all capacity-build of vintages operational in that
        period.

        This expression is not defined for a group's non-operational deliverability
        periods (i.e. it's 0). E.g. if we were allowed to build
        deliverability capacity in 2020 and 2030, and the transmission had a 15 year
        lifetime, in 2020 we'd take 2020 capacity-build only, in 2030, we'd take the
        sum of 2020 capacity-build and 2030 capacity-build, in 2040, we'd take 2030
        capacity-build only, and in 2050, the capacity would be undefined (i.e. 0 for
        the purposes of the objective function).
        """
        return sum(
            mod.Deliverability_Group_Build_MW[g, v]
            for (gen, v) in mod.GROUP_VNTS_OPR_IN_PERIOD[p]
            if gen == g
        )

    m.Cumulative_Added_Deliverability_Capacity_MW = Expression(
        m.DELIVERABILITY_GROUPS,
        m.PERIODS,
        initialize=group_capacity_rule,
    )

    # Limit deliverable capacity based on added deliverabilty
    def prj_deliverable_capacity_less_than_build_constraint_rule(
        mod, g, p, constraint_type, peak_designation
    ):
        if constraint_type == "deliverable":
            return (
                mod.Group_Deliverable_Project_Capacity_MW[
                    g, p, constraint_type, peak_designation
                ]
                <= mod.existing_deliverability_mw[
                    g, p, constraint_type, peak_designation
                ]
                + mod.Cumulative_Added_Deliverability_Capacity_MW[g, p]
            )
        else:
            return Constraint.Skip

    m.Prj_Deliv_Capacity_Constraint = Constraint(
        m.DELIVERABILITY_GROUPS,
        m.PERIODS,
        m.CONSTRAINT_TYPES,
        m.PEAK_DESIGNATIONS,
        rule=prj_deliverable_capacity_less_than_build_constraint_rule,
    )

    # Limit total capacity based on added deliverabilty
    def prj_total_capacity_less_than_build_constraint_rule(
        mod, g, p, constraint_type, peak_designation
    ):
        if constraint_type == "total":
            return (
                mod.Group_Total_Project_Capacity_MW[
                    g, p, constraint_type, peak_designation
                ]
                <= mod.existing_deliverability_mw[
                    g, p, constraint_type, peak_designation
                ]
                + mod.Cumulative_Added_Deliverability_Capacity_MW[g, p]
            )
        else:
            return Constraint.Skip

    m.Prj_Total_Capacity_Constraint = Constraint(
        m.DELIVERABILITY_GROUPS,
        m.PERIODS,
        m.CONSTRAINT_TYPES,
        m.PEAK_DESIGNATIONS,
        rule=prj_total_capacity_less_than_build_constraint_rule,
    )

    # Limit energy-only capacity based on added deliverabilty
    def prj_energy_only_capacity_less_than_build_constraint_rule(
        mod, g, p, constraint_type, peak_designation
    ):
        if constraint_type == "energy_only":
            return (
                mod.Deliverability_Group_Energy_Only_Project_Capacity_MW[
                    g, p, constraint_type, peak_designation
                ]
                <= mod.existing_deliverability_mw[
                    g, p, constraint_type, peak_designation
                ]
                + mod.Cumulative_Added_Deliverability_Capacity_MW[g, p]
            )
        else:
            return Constraint.Skip

    m.Prj_Energy_Only_Capacity_Constraint = Constraint(
        m.DELIVERABILITY_GROUPS,
        m.PERIODS,
        m.CONSTRAINT_TYPES,
        m.PEAK_DESIGNATIONS,
        rule=prj_energy_only_capacity_less_than_build_constraint_rule,
    )

    def capacity_cost_rule(mod, g, p):
        """
        The capital cost for building "deliverability" is the capacity-build of a
        particular vintage times the annualized capital cost for that vintage summed
        over all vintages that are incurring costs in the period based on their
        financial lifetimes.
        """
        return sum(
            mod.Deliverability_Group_Build_MW[g, v]
            * mod.deliverability_cost_per_mw_yr[g, v]
            for (gen, v) in mod.GROUP_VNTS_OPR_IN_PERIOD[p]
            if gen == g
        )

    # Calculate costs for ELCC-eligibility
    m.Deliverability_Group_Deliverable_Capacity_Cost = Expression(
        m.DELIVERABILITY_GROUPS,
        m.PERIODS,
        rule=capacity_cost_rule,
    )

    def deliverable_capacity_limit_rule(mod, g, p):
        """
        Maximum deliverable capacity that can be built
        :param mod:
        :param g:
        :param p:
        :return:
        """
        return (
            mod.Cumulative_Added_Deliverability_Capacity_MW[g, p]
            <= mod.deliverable_capacity_limit_mw[g, p]
        )

    m.Group_Deliverable_Capacity_Limit_Constraint = Constraint(
        m.DELIVERABILITY_GROUPS, m.PERIODS, rule=deliverable_capacity_limit_rule
    )


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
    Optionally load data for costs incurred only when a capacity threshold
    is reached; if file is not found, sets in this modules will be empty and
    params will have default values of 0
    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """

    group_costs_file = os.path.join(
        scenario_directory,
        subproblem,
        stage,
        "inputs",
        "deliverability_group_costs.tab",
    )
    data_portal.load(
        filename=group_costs_file,
        index=m.DELIVERABILITY_GROUP_VINTAGES,
        param=(
            m.deliverability_lifetime_yrs,
            m.deliverability_cost_per_mw_yr,
        ),
    )

    # Existing deliverability: optional
    existing_deliverability_file = os.path.join(
        scenario_directory,
        subproblem,
        stage,
        "inputs",
        "deliverability_existing.tab",
    )
    if os.path.exists(existing_deliverability_file):
        data_portal.load(
            filename=existing_deliverability_file,
            param=m.existing_deliverability_mw,
        )

    # Potentials: optional
    group_potentials_file = os.path.join(
        scenario_directory,
        subproblem,
        stage,
        "inputs",
        "deliverability_group_potential.tab",
    )
    if os.path.exists(group_potentials_file):
        data_portal.load(
            filename=group_potentials_file,
            param=m.deliverable_capacity_limit_mw,
        )

    group_projects_file = os.path.join(
        scenario_directory,
        subproblem,
        stage,
        "inputs",
        "deliverability_group_projects.tab",
    )

    data_portal.load(filename=group_projects_file, set=m.DELIVERABILITY_GROUP_PROJECTS)

    multipliers_file = os.path.join(
        scenario_directory,
        subproblem,
        stage,
        "inputs",
        "deliverability_project_multipliers.tab",
    )
    data_portal.load(
        filename=multipliers_file,
        index=m.PROJECT_CONSTRAINT_TYPE_PEAK_DESIGNATIONS,
        param=m.peak_designation_multiplier,
    )


def export_results(
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

    :param m:
    :param d:
    :param scenario_directory:
    :param subproblem:
    :param stage:
    :return:
    """

    # Total capacity for all projects in group
    with open(
        os.path.join(
            scenario_directory,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "results",
            "project_deliverability_groups.csv",
        ),
        "w",
        newline="",
    ) as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "deliverability_group",
                "period",
                "deliverable_capacity_built_in_period_mw",
                "cumulative_added_deliverable_capacity_mw",
                "deliverability_annual_cost_in_period",
            ]
        )
        # TODO: add limits to results
        for g in sorted(m.DELIVERABILITY_GROUPS):
            for p in sorted(m.PERIODS):
                writer.writerow(
                    [
                        g,
                        p,
                        (
                            value(m.Deliverability_Group_Build_MW[g, p])
                            if (g, p) in m.DELIVERABILITY_GROUP_VINTAGES
                            else None
                        ),
                        value(m.Cumulative_Added_Deliverability_Capacity_MW[g, p]),
                        value(m.Deliverability_Group_Deliverable_Capacity_Cost[g, p]),
                    ]
                )


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
    if subscenarios.PRM_DELIVERABILITY_COST_SCENARIO_ID is None:
        # If we call this module, it's because we specified the feature, so we can
        # raise an error if an energy_only_scenario_id is not specified.
        raise ValueError(
            "You must specify a prm_deliverability_cost_scenario_id for this "
            "scenario to use the 'deliverability' feature."
        )
    else:
        c1 = conn.cursor()
        # Groups with cost for building Tx capacity for deliverability
        group_costs = c1.execute(
            """SELECT deliverability_group,
            vintage,
            lifetime_yrs,
            deliverability_cost_per_mw_yr
            FROM inputs_project_prm_deliverability_costs
            WHERe prm_deliverability_cost_scenario_id = {}""".format(
                subscenarios.PRM_DELIVERABILITY_COST_SCENARIO_ID
            )
        )

        c2 = conn.cursor()
        if subscenarios.PRM_DELIVERABILITY_EXISTING_SCENARIO_ID is None:
            existing = []
        else:
            existing = c2.execute(
                """SELECT deliverability_group, period, constraint_type, 
                peak_designation, existing_deliverability_mw
            FROM inputs_project_prm_deliverability_existing
            WHERE prm_deliverability_existing_scenario_id = {}""".format(
                    subscenarios.PRM_DELIVERABILITY_EXISTING_SCENARIO_ID
                )
            )

        c3 = conn.cursor()
        if subscenarios.PRM_DELIVERABILITY_POTENTIAL_SCENARIO_ID is None:
            group_potential = []
        else:
            group_potential = c3.execute(
                """SELECT deliverability_group, period,
            deliverable_capacity_limit_cumulative_mw
            FROM inputs_project_prm_deliverability_potential
            WHERE prm_deliverability_potential_scenario_id = {}""".format(
                    subscenarios.PRM_DELIVERABILITY_POTENTIAL_SCENARIO_ID
                )
            )

        c4 = conn.cursor()
        # Projects by group
        group_projects = c4.execute(
            """SELECT deliverability_group, project 
            FROM (
                SELECT project
                FROM inputs_project_portfolios
                WHERE project_portfolio_scenario_id = {portfolio}
             ) as portfolio  -- portfolio projects only
             LEFT OUTER JOIN (
                SELECT project
                FROM inputs_project_prm_zones
                WHERE project_prm_zone_scenario_id = {prm_zone}
            ) as proj_tbl  --  prm contributing projects only
            USING (project)
            LEFT OUTER JOIN (
                SELECT project, project_deliverability_scenario_id
                FROM inputs_project_elcc_chars
                WHERE project_elcc_chars_scenario_id = {prj_elcc} 
            )
            USING (project)
            LEFT OUTER JOIN (
                SELECT project, project_deliverability_scenario_id, deliverability_group
                FROM inputs_project_deliverability
            ORDER BY deliverability_group, project
            ) as grp_tbl
            USING (project, project_deliverability_scenario_id)
            WHERE deliverability_group IS NOT NULL
            ;""".format(
                portfolio=subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
                prm_zone=subscenarios.PROJECT_PRM_ZONE_SCENARIO_ID,
                prj_elcc=subscenarios.PROJECT_ELCC_CHARS_SCENARIO_ID,
            )
        )

        c5 = conn.cursor()
        # Project multipliers by constraint type and peak designation
        project_multipliers = c5.execute(
            """
            SELECT project, constraint_type, peak_designation, multiplier
            FROM inputs_project_prm_deliverability_multipliers
            WHERE project_prm_deliverability_multipliers_scenario_id = {multipliers}
            """.format(
                multipliers=subscenarios.PROJECT_PRM_DELIVERABILITY_MULTIPLIERS_SCENARIO_ID,
            )
        )

    return group_costs, existing, group_potential, group_projects, project_multipliers


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
    pass
    # Validation to be added
    # group_costs, existing, group_potential, group_projects, project_multipliers = \
    #   get_model_inputs_from_database(
    #       scenario_id, subscenarios, subproblem, stage, conn)


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
    deliverability_group_costs.tab and
    deliverability_group_projects.tab files.
    :param scenario_directory: string, the scenario directory
    :param subscenarios: SubScenarios object with all subscenario info
    :param subproblem:
    :param stage:
    :param conn: database connection
    :return:
    """

    (
        group_costs,
        existing,
        group_potential,
        group_projects,
        project_multipliers,
    ) = get_model_inputs_from_database(
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
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "deliverability_group_costs.tab",
        ),
        "w",
        newline="",
    ) as costs_file:
        writer = csv.writer(costs_file, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(
            [
                "deliverability_group",
                "vintage",
                "lifetime_yrs",
                "deliverability_cost_per_mw_yr",
            ]
        )

        # Input data
        for row in group_costs:
            replace_nulls = ["." if i is None else i for i in row]
            writer.writerow(replace_nulls)

    existing = existing.fetchall()
    if existing:
        with open(
            os.path.join(
                scenario_directory,
                subproblem,
                stage,
                "inputs",
                "deliverability_existing.tab",
            ),
            "w",
            newline="",
        ) as potentials_file:
            writer = csv.writer(potentials_file, delimiter="\t", lineterminator="\n")

            # Write header
            writer.writerow(
                [
                    "deliverability_group",
                    "period",
                    "constraint_type",
                    "peak_designation",
                    "existing_deliverability_mw",
                ]
            )

            # Input data
            for row in existing:
                writer.writerow(row)

    group_potential = group_potential.fetchall()
    if group_potential:
        with open(
            os.path.join(
                scenario_directory,
                subproblem,
                stage,
                "inputs",
                "deliverability_group_potential.tab",
            ),
            "w",
            newline="",
        ) as potentials_file:
            writer = csv.writer(potentials_file, delimiter="\t", lineterminator="\n")

            # Write header
            writer.writerow(
                [
                    "deliverability_group",
                    "period",
                    "deliverable_capacity_limit_cumulative_mw",
                ]
            )

            # Input data
            for row in group_potential:
                writer.writerow(row)

    with open(
        os.path.join(
            scenario_directory,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "deliverability_group_projects.tab",
        ),
        "w",
    ) as group_projects_file:
        writer = csv.writer(group_projects_file, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(["deliverability_group", "project"])

        # Input data
        for row in group_projects:
            writer.writerow(row)

    with open(
        os.path.join(
            scenario_directory,
            hydro_iteration,
            availability_iteration,
            subproblem,
            stage,
            "inputs",
            "deliverability_project_multipliers.tab",
        ),
        "w",
    ) as multipliers_file:
        writer = csv.writer(multipliers_file, delimiter="\t", lineterminator="\n")

        # Write header
        writer.writerow(
            ["project", "constraint_type", "peak_designation", "multiplier"]
        )

        # Input data
        for row in project_multipliers:
            writer.writerow(row)


def import_results_into_database(
    scenario_id,
    weather_iteration,
    hydro_iteration,
    availability_iteration,
    subproblem,
    stage,
    c,
    db,
    results_directory,
    quiet,
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

    import_csv(
        conn=db,
        cursor=c,
        scenario_id=scenario_id,
        weather_iteration=weather_iteration,
        hydro_iteration=hydro_iteration,
        availability_iteration=availability_iteration,
        subproblem=subproblem,
        stage=stage,
        quiet=quiet,
        results_directory=results_directory,
        which_results="project_deliverability_groups",
    )

#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Scenario characteristics in database
"""

from builtins import object

FEATURES = [
    "transmission",
    "transmission_hurdle_rates",
    "simultaneous_flow_limits",
    "lf_reserves_up",
    "lf_reserves_down",
    "regulation_up",
    "regulation_down",
    "frequency_response",
    "spinning_reserves",
    "rps",
    "carbon_cap",
    "track_carbon_imports",
    "prm",
    "elcc_surface",
    "local_capacity",
    "tuning"
]

SUBSCENARIO_IDS = [
    "temporal_scenario_id",
    "load_zone_scenario_id",
    "lf_reserves_up_ba_scenario_id",
    "lf_reserves_up_ba_scenario_id",
    "lf_reserves_down_ba_scenario_id",
    "regulation_up_ba_scenario_id",
    "regulation_down_ba_scenario_id",
    "frequency_response_ba_scenario_id",
    "spinning_reserves_ba_scenario_id",
    "rps_zone_scenario_id",
    "carbon_cap_zone_scenario_id",
    "prm_zone_scenario_id",
    "local_capacity_zone_scenario_id",
    "project_portfolio_scenario_id",
    "project_load_zone_scenario_id",
    "project_lf_reserves_up_ba_scenario_id",
    "project_lf_reserves_down_ba_scenario_id",
    "project_regulation_up_ba_scenario_id",
    "project_regulation_down_ba_scenario_id",
    "project_frequency_response_ba_scenario_id",
    "project_spinning_reserves_ba_scenario_id",
    "project_rps_zone_scenario_id",
    "project_carbon_cap_zone_scenario_id",
    "project_prm_zone_scenario_id",
    "project_elcc_chars_scenario_id",
    "project_local_capacity_zone_scenario_id",
    "project_local_capacity_chars_scenario_id",
    "project_specified_capacity_scenario_id",
    "project_specified_fixed_cost_scenario_id",
    "project_new_cost_scenario_id",
    "project_new_potential_scenario_id",
    "project_new_binary_build_size_scenario_id",
    "project_capacity_group_scenario_id",
    "project_capacity_group_requirement_scenario_id",
    "prm_energy_only_scenario_id",
    "project_operational_chars_scenario_id",
    "project_availability_scenario_id",
    "fuel_scenario_id",
    "fuel_price_scenario_id",
    "transmission_portfolio_scenario_id",
    "transmission_load_zone_scenario_id",
    "transmission_specified_capacity_scenario_id",
    "transmission_new_cost_scenario_id",
    "transmission_operational_chars_scenario_id",
    "transmission_hurdle_rate_scenario_id",
    "transmission_carbon_cap_zone_scenario_id",
    "transmission_simultaneous_flow_limit_scenario_id",
    "transmission_simultaneous_flow_limit_line_group_scenario_id",
    "load_scenario_id",
    "lf_reserves_up_scenario_id",
    "lf_reserves_down_scenario_id",
    "regulation_up_scenario_id",
    "regulation_down_scenario_id",
    "frequency_response_scenario_id",
    "spinning_reserves_scenario_id",
    "rps_target_scenario_id",
    "carbon_cap_target_scenario_id",
    "prm_requirement_scenario_id",
    "elcc_surface_scenario_id",
    "local_capacity_requirement_scenario_id",
    "tuning_scenario_id"
]


class Scenario(object):
    def __init__(self, conn, scenario_id):
        self.conn = conn
        self.SCENARIO_ID = scenario_id

        self.feature_dict, self.feature_list = self.get_features()
        self.subscenarios_ids = self.get_subscenario_ids()
        self.subscenario_ids_by_feature = self.determine_subscenarios_by_feature()

        self.SUBPROBLEM_STAGE_DICT = self.get_subproblems_stages()
        self.SUBPROBLEMS = list(sorted(self.SUBPROBLEM_STAGE_DICT.keys()))

        self.SOLVER_OPTIONS_ID = self.get_solver_options_id()
        self.SOLVER = self.get_solver()
        self.SOLVER_OPTIONS = self.get_solver_options()

    def get_features(self):
        feature_dict = {}
        feature_list = []
        c = self.conn.cursor()
        for f in FEATURES:
            feature = c.execute(
                """SELECT of_{}
                FROM scenarios
                WHERE scenario_id = {};""".format(f, self.SCENARIO_ID)
            ).fetchone()[0]

            feature_dict["OPTIONAL_FEATURE_{}".format(f.upper())] = feature

            if feature:
                feature_list.append(f)
        c.close()

        return feature_dict, feature_list

    def get_subscenario_ids(self):
        """
        The subscenario IDs will be used to format SQL queries, so we set
        them to "NULL" (not None) if an ID is not specified for the
        scenario.
        :return: dictionary {subscenario_id_name, id_value}
        """
        c = self.conn.cursor()
        sc_dict = {}
        for sc_id in SUBSCENARIO_IDS:
            temp_id = c.execute(
                """SELECT {}
                   FROM scenarios
                   WHERE scenario_id = {};""".format(sc_id, self.SCENARIO_ID)
            ).fetchone()[0]

            sc_dict[sc_id.upper()] = "NULL" if temp_id is None else temp_id
        c.close()

        return sc_dict

    def determine_subscenarios_by_feature(self):
        c = self.conn.cursor()
        feature_sc = c.execute(
            """SELECT feature, subscenario_id
            FROM mod_feature_subscenarios"""
        ).fetchall()
        feature_sc_dict = {}
        for f, sc in feature_sc:
            if f in feature_sc_dict:
                feature_sc_dict[f].append(sc.upper())
            else:
                feature_sc_dict[f] = [sc.upper()]
        c.close()

        return feature_sc_dict

    def get_subproblems_stages(self):
        c = self.conn.cursor()
        subproblems = c.execute(
            """SELECT subproblem_id
               FROM inputs_temporal_subproblems
               INNER JOIN scenarios
               USING (temporal_scenario_id)
               WHERE scenario_id = {};""".format(self.SCENARIO_ID)
        ).fetchall()

        # SQL returns a list of tuples [(1,), (2,)] so convert to simple list
        subproblems = [subproblem[0] for subproblem in subproblems]

        # store subproblems and stages in dict {subproblem: [stages]}
        subproblem_stage_dict = {}
        for s in subproblems:
            stages = c.execute(
                """SELECT stage_id
                   FROM inputs_temporal_subproblems_stages
                   INNER JOIN scenarios
                   USING (temporal_scenario_id)
                   WHERE scenario_id = {}
                   AND subproblem_id = {};""".format(self.SCENARIO_ID, s)
            ).fetchall()
            stages = [stage[0] for stage in stages]  # convert to simple list
            subproblem_stage_dict[s] = stages
        c.close()

        return subproblem_stage_dict

    def get_solver_options_id(self):
        c = self.conn.cursor()
        solver_options_id = c.execute(
            """SELECT solver_options_id 
            FROM scenarios 
            WHERE scenario_id = {}
            """.format(self.SCENARIO_ID)
        ).fetchone()[0]
        c.close()

        return solver_options_id

    def get_solver(self):
        solver_options_id = self.get_solver_options_id()

        if solver_options_id is None:
            solver = None
        else:
            c = self.conn.cursor()
            distinct_solvers = c.execute(
                """SELECT DISTINCT solver 
                FROM inputs_options_solver 
                WHERE solver_options_id = {};
                """.format(self.SOLVER_OPTIONS_ID)
            ).fetchall()

            if len(distinct_solvers) > 1:
                raise ValueError("""
                ERROR: Solver options include more than one solver! Only a 
                single solver must be specified for solver_options_id in the 
                inputs_options_solver table. See solver_options_id {}. 
                """.format(solver_options_id))
            else:
                solver = distinct_solvers[0][0]
            c.close()

        return solver

    def get_solver_options(self):
        solver_options_id = self.get_solver_options_id()

        if solver_options_id is None:
            solver_options = None
        else:
            c = self.conn.cursor()
            solver_options = {
                row[0]: row[1]
                for row in c.execute(
                    """SELECT solver_option_name, solver_option_value
                    FROM inputs_options_solver
                    WHERE solver_options_id = {};
                    """.format(solver_options_id)
                ).fetchall() if row[0] is not None and row[0] is not ""
            }
            c.close()

        return solver_options

    # TODO: refactor this in capacity_types/__init__? (similar functions are
    #   used in prm_types/operational_types etc.
    def get_required_capacity_type_modules(self):
        """
        Get the required capacity type submodules based for the Scenario object
        Required modules are the unique set of generator capacity types in
        the scenario's portfolio.

        This list will be used to know for which capacity type submodules we
        should validate inputs, get inputs from database , or save results to
        database. It is also used to figure out which suscenario_ids are
        required inputs (e.g. cost inputs are required when there are new
        build resources).

        Note: once we have determined the dynamic components, this information
        will also be stored in the DynamicComponents class object.

        :return: List of the required capacity type submodules
        """
        c = self.conn.cursor()
        cap_types = c.execute(
            """SELECT DISTINCT capacity_type 
            FROM inputs_project_portfolios
            WHERE project_portfolio_scenario_id = {}
            """.format(self.subscenarios_ids["PROJECT_PORTFOLIO_SCENARIO_ID"])
        )
        cap_types = [c[0] for c in cap_types]  # convert to list
        c.close()
        return cap_types

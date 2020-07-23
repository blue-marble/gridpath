# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

from flask_restful import Resource
import importlib

from db.common_functions import connect_to_database
from ui.server.api.view_data import get_table_data


class ScenarioResultsOptions(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """
        conn = connect_to_database(db_path=self.db_path)
        c = conn.cursor()

        options_api = dict()

        load_zone_options = [z[0] for z in c.execute(
            """SELECT load_zone FROM inputs_geography_load_zones
            WHERE load_zone_scenario_id = (
            SELECT load_zone_scenario_id
            FROM scenarios
            WHERE scenario_id = {});""".format(scenario_id)
          ).fetchall()]
        options_api["loadZoneOptions"] = ['Select Zone'] + load_zone_options

        rps_zone_options = [z[0] for z in c.execute(
            """SELECT rps_zone FROM inputs_geography_rps_zones
            WHERE rps_zone_scenario_id = (
            SELECT rps_zone_scenario_id
            FROM scenarios
            WHERE scenario_id = {});""".format(scenario_id)
          ).fetchall()]
        options_api["rpsZoneOptions"] = ['Select RPS Area'] + rps_zone_options

        carbon_cap_zone_options = [z[0] for z in c.execute(
            """SELECT carbon_cap_zone FROM inputs_geography_carbon_cap_zones
            WHERE carbon_cap_zone_scenario_id = (
            SELECT carbon_cap_zone_scenario_id
            FROM scenarios
            WHERE scenario_id = {});""".format(scenario_id)
          ).fetchall()]
        options_api["carbonCapZoneOptions"] = \
          ['Select Carbon Cap Area'] + carbon_cap_zone_options

        period_options = [p[0] for p in c.execute(
            """SELECT period FROM inputs_temporal_periods
            WHERE temporal_scenario_id = (
            SELECT temporal_scenario_id
            FROM scenarios
            WHERE scenario_id = {});""".format(scenario_id)
          ).fetchall()]
        options_api["periodOptions"] = ['Select Period'] + period_options

        # TODO: are these unique or do we need to separate by period; in fact,
        #  is separating by period a better user experience regardless
        horizon_options = [h[0] for h in c.execute(
          """SELECT horizon FROM inputs_temporal_horizons
          WHERE temporal_scenario_id = (
          SELECT temporal_scenario_id
          FROM scenarios
          WHERE scenario_id = {});""".format(scenario_id)
        ).fetchall()]
        options_api["horizonOptions"] = ['Select Horizon'] + horizon_options

        timepoint_options = [t[0] for t in c.execute(
            """SELECT timepoint FROM inputs_temporal
            WHERE temporal_scenario_id = (
            SELECT temporal_scenario_id
            FROM scenarios
            WHERE scenario_id = {});""".format(scenario_id)
          ).fetchall()]
        options_api["startTimepointOptions"] = ['Select Starting Timepoint']\
                                                + timepoint_options
        # TODO: keep track of start timepoint since end has to be >= start
        #  timepoint options also depend on stage
        options_api["endTimepointOptions"] = ['Select Ending Timepoint'] \
                                                + timepoint_options

        subproblem_options = [h[0] for h in c.execute(
            """SELECT DISTINCT subproblem_id
            FROM inputs_temporal_subproblems
            WHERE temporal_scenario_id = (
            SELECT temporal_scenario_id
            FROM scenarios
            WHERE scenario_id = {});""".format(scenario_id)
          ).fetchall()]

        options_api["subproblemOptions"] = ['Select Subproblem'] + \
                                           subproblem_options
        # TODO: we need to keep track of subproblems, as stages can differ
        #  by subproblem
        stage_options = [h[0] for h in c.execute(
            """SELECT DISTINCT stage_id
            FROM inputs_temporal_subproblems_stages
            WHERE temporal_scenario_id = (
            SELECT temporal_scenario_id
            FROM scenarios
            WHERE scenario_id = {});""".format(scenario_id)
          ).fetchall()]

        options_api["stageOptions"] = ['Select Stage'] + stage_options

        commit_project_options = [h[0] for h in c.execute("""
            SELECT project
            FROM inputs_project_portfolios
            JOIN inputs_project_operational_chars
            USING (project)
            WHERE project_portfolio_scenario_id = (
            SELECT project_portfolio_scenario_id
            FROM scenarios
            WHERE scenario_id = {})
            AND project_operational_chars_scenario_id = (
            SELECT project_operational_chars_scenario_id
            FROM scenarios
            WHERE scenario_id = {})
            AND operational_type in ('gen_commit_bin', 'gen_commit_lin',
            'gen_commit_cap');
            """.format(scenario_id, scenario_id)
          ).fetchall()]
        options_api["commitProjectOptions"] = \
            ['Select Generator'] + commit_project_options

        project_options = [h[0] for h in c.execute(
            """SELECT project FROM inputs_project_portfolios
            WHERE project_portfolio_scenario_id = (
            SELECT project_portfolio_scenario_id
            FROM scenarios
            WHERE scenario_id = {});""".format(scenario_id)
          ).fetchall()]
        options_api["projectOptions"] = \
            ['Select Project'] + project_options

        return options_api


class ScenarioResultsPlot(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, plot, scenario_id, load_zone, rps_zone, carbon_cap_zone,
            period, horizon, start_timepoint, end_timepoint, subproblem, stage,
            project, commit_project, ymax):
        """

        :return:
        """

        plot_module = importlib.import_module("viz." + plot.replace("-", "_"))
        plot_api = dict()

        base_arguments = [
            "--return_json",
            "--database", self.db_path,
            "--scenario_id", scenario_id,
            "--scenario_name_in_title"
        ]

        filter_arguments = []
        if load_zone == 'default':
            pass
        else:
            filter_arguments.append("--load_zone")
            filter_arguments.append(load_zone)

        if rps_zone == 'default':
            pass
        else:
            filter_arguments.append("--rps_zone")
            filter_arguments.append(rps_zone)

        if carbon_cap_zone == 'default':
            pass
        else:
            filter_arguments.append("--carbon_cap_zone")
            filter_arguments.append(carbon_cap_zone)

        if period == 'default':
            pass
        else:
            filter_arguments.append("--period")
            filter_arguments.append(period)

        if horizon == 'default':
            pass
        else:
            filter_arguments.append("--horizon")
            filter_arguments.append(horizon)

        if start_timepoint == 'default':
            pass
        else:
            filter_arguments.append("--starting_tmp")
            filter_arguments.append(start_timepoint)

        if end_timepoint == 'default':
            pass
        else:
            filter_arguments.append("--ending_tmp")
            filter_arguments.append(end_timepoint)

        if subproblem == 'default':
            pass
        else:
            filter_arguments.append("--subproblem")
            filter_arguments.append(subproblem)

        if stage == 'default':
            pass
        else:
            filter_arguments.append("--stage")
            filter_arguments.append(stage)

        if project == 'default':
            pass
        else:
            filter_arguments.append("--project")
            filter_arguments.append(project)

        if commit_project == 'default':
            pass
        else:
            filter_arguments.append("--project")
            filter_arguments.append(commit_project)

        if ymax == 'default':
            plot_api["plotJSON"] = plot_module.main(
                base_arguments + filter_arguments
            )
        else:
            plot_api["plotJSON"] = plot_module.main(
                base_arguments + filter_arguments + ["--ylimit", ymax]
            )

        return plot_api


class ScenarioResultsIncludedPlots(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """
        conn = connect_to_database(db_path=self.db_path)
        c = conn.cursor()

        plots_query = c.execute(
          """SELECT results_plot, caption, load_zone_form_control,
          rps_zone_form_control, carbon_cap_zone_form_control,
          period_form_control, horizon_form_control,
          start_timepoint_form_control, end_timepoint_form_control,
          subproblem_form_control, stage_form_control,
          project_form_control, commit_project_form_control
          FROM ui_scenario_results_plot_metadata
          WHERE include = 1;"""
        ).fetchall()

        # TODO: add formGroup, Ymax and button
        included_plots_api = []
        for plot in plots_query:
            (results_plot, caption, load_zone_form_control,
                rps_zone_form_control, carbon_cap_zone_form_control,
                period_form_control, horizon_form_control,
                start_timepoint_form_control, end_timepoint_form_control,
                subproblem_form_control, stage_form_control,
                project_form_control, commit_project_form_control) \
                = plot
            plot_api = {
                "plotType": results_plot,
                "caption": caption,
                "loadZone": [] if load_zone_form_control else "default",
                "rpsZone": [] if rps_zone_form_control else "default",
                "carbonCapZone": [] if carbon_cap_zone_form_control
                else "default",
                "period": [] if period_form_control else "default",
                "horizon": [] if horizon_form_control else "default",
                "startTimepoint": [] if start_timepoint_form_control
                else "default",
                "endTimepoint": [] if end_timepoint_form_control
                else "default",
                "subproblem": [] if subproblem_form_control else "default",
                "stage": [] if stage_form_control else "default",
                "project": [] if project_form_control else "default",
                "commitProject": [] if commit_project_form_control else
                "default"
            }
            included_plots_api.append(plot_api)

        return included_plots_api


class ScenarioResultsTable(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id, table):
        """

        :return:
        """
        if table == "null":
            return None
        else:
            return create_data_table_api(
              db_path=self.db_path,
              table=table,
              scenario_id=scenario_id
            )


class ScenarioResultsIncludedTables(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self):
        """

        :return:
        """
        conn = connect_to_database(db_path=self.db_path)
        c = conn.cursor()

        tables_query = c.execute(
            """SELECT results_table, caption
            FROM ui_scenario_results_table_metadata
            WHERE include = 1;"""
        ).fetchall()

        included_tables_api = []
        for table in tables_query:
            table_api = {
              "table": table[0].replace("_", "-"),
              "caption": table[1]
            }
            included_tables_api.append(table_api)

        return included_tables_api


def create_data_table_api(
      db_path, table, scenario_id):
    """
    :param db_path:
    :param table:
    :param scenario_id:
    :return:
    """
    conn = connect_to_database(db_path=db_path)
    c = conn.cursor()

    data_table_api = dict()
    data_table_api['table'] = table

    data_table_api['caption'] = c.execute(
        """SELECT caption FROM ui_scenario_results_table_metadata
        WHERE results_table = '{}';""".format(table.replace("-", "_"))
    ).fetchone()[0]

    data_table_api['columns'] = get_table_data(
        db_path=db_path,
        table=table.replace("-", "_"),
        scenario_id=scenario_id,
        other_scenarios=[]
    )['columns']

    data_table_api['rowsData'] = get_table_data(
        db_path=db_path,
        table=table.replace("-", "_"),
        scenario_id=scenario_id,
        other_scenarios=[]
    )['rowsData']

    return data_table_api

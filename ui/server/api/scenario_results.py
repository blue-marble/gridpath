# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

from flask_restful import Resource
import importlib

from ui.server.common_functions import connect_to_database
from viz import capacity_plot, capacity_factor_plot, cost_plot, \
  dispatch_plot, energy_plot


class ScenarioResultsOptions(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """
        io, c = connect_to_database(db_path=self.db_path)

        options_api = dict()

        load_zone_options = [z[0] for z in c.execute(
            """SELECT load_zone FROM inputs_geography_load_zones 
            WHERE load_zone_scenario_id = (
            SELECT load_zone_scenario_id
            FROM scenarios
            WHERE scenario_id = {});""".format(scenario_id)
          ).fetchall()]
        options_api["loadZoneOptions"] = ['Select Zone'] + load_zone_options

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

        timepoint_options = [h[0] for h in c.execute(
            """SELECT timepoint FROM inputs_temporal_timepoints 
            WHERE temporal_scenario_id = (
            SELECT temporal_scenario_id
            FROM scenarios
            WHERE scenario_id = {});""".format(scenario_id)
          ).fetchall()]
        options_api["timepointOptions"] = \
            ['Select Timepoint'] + timepoint_options

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

        project_options = [h[0] for h in c.execute(
            """SELECT project FROM inputs_project_portfolios 
            WHERE project_portfolio_scenario_id = (
            SELECT project_portfolio_scenario_id
            FROM scenarios
            WHERE scenario_id = {});""".format(scenario_id)
          ).fetchall()]
        options_api["projectOptions"] = \
            ['Select Generator'] + project_options

        return options_api


class ScenarioResultsPlot(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, plot, scenario_id, load_zone, period, horizon, timepoint,
            stage, project, ymax):
        """

        :return:
        """

        plot_module = importlib.import_module("viz." + plot.replace("-", "_"))
        plot_api = dict()

        base_arguments = [
            "--return_json",
            "--database", self.db_path,
            "--scenario_id", scenario_id,
        ]

        filter_arguments = []
        if load_zone == 'default':
            pass
        else:
            filter_arguments.append("--load_zone")
            filter_arguments.append(load_zone)

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

        if timepoint == 'default':
            pass
        else:
            filter_arguments.append("--timepoint")
            filter_arguments.append(timepoint)

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
        io, c = connect_to_database(db_path=self.db_path)
        plots_query = c.execute(
          """SELECT results_plot, caption, load_zone_form_control, 
          period_form_control, horizon_form_control, timepoint_form_control, 
          stage_form_control, project_form_control
          FROM ui_scenario_results_plot_metadata
          WHERE include = 1;"""
        ).fetchall()

        # TODO: add formGroup, Ymax and button
        included_plots_api = []
        for plot in plots_query:
            (results_plot, caption, load_zone_form_control,
                period_form_control, horizon_form_control,
                timepoint_form_control, stage_form_control,
                project_form_control) \
              = plot
            plot_api = {
                "plotType": results_plot,
                "caption": caption,
                "loadZone": [] if load_zone_form_control else "default",
                "period": [] if period_form_control else "default",
                "horizon": [] if horizon_form_control else "default",
                "timepoint": [] if timepoint_form_control else "default",
                "stage": [] if stage_form_control else "default",
                "project": [] if project_form_control else "default"
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
              columns='*',
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
        io, c = connect_to_database(db_path=self.db_path)
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
      db_path, columns, table, scenario_id):
    """
    :param db_path:
    :param columns:
    :param table:
    :param scenario_id:
    :return:
    """
    io, c = connect_to_database(db_path=db_path)

    data_table_api = dict()
    data_table_api['table'] = table

    data_table_api['caption'] = c.execute(
        """SELECT caption FROM ui_scenario_results_table_metadata
        WHERE results_table = '{}';""".format(table.replace("-", "_"))
    ).fetchone()[0]

    column_names, data_rows = get_table_data(
      db_path=db_path,
      columns=columns,
      table=table.replace("-", "_"),
      scenario_id=scenario_id
    )
    data_table_api['columns'] = column_names
    data_table_api['rowsData'] = data_rows

    return data_table_api


def get_table_data(db_path, columns, table, scenario_id):
    """
    :param db_path:
    :param columns:
    :param table:
    :param scenario_id:
    :return:
    """
    io, c = connect_to_database(db_path=db_path)

    table_data_query = c.execute(
      """SELECT {} FROM {} 
         WHERE scenario_id = {};""".format(columns, table, scenario_id))

    column_names = [s[0] for s in table_data_query.description]

    rows_data = []
    for row in table_data_query.fetchall():
        row_values = list(row)
        row_dict = dict(zip(column_names, row_values))
        rows_data.append(row_dict)

    return column_names, rows_data

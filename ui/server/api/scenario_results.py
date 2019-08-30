# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

from flask_restful import Resource

from ui.server.common_functions import connect_to_database
from viz import capacity_plot, capacity_factor_plot, cost_plot, \
  dispatch_plot, energy_plot


# TODO: create results views to show, which ones?

class ScenarioResultsProjectCapacity(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """
        return create_data_table_api(
            db_path=self.db_path,
            ngifkey='results-project-capacity',
            caption='Project Capacity',
            columns='*',
            table='results_project_capacity_all',
            scenario_id=scenario_id
        )


class ScenarioResultsProjectRetirements(Resource):
    """
    Currently combines binary and linear economic retirement tables.
    """
    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """
        return create_data_table_api(
          db_path=self.db_path,
          ngifkey='results-project-retirements',
          caption='Project Retirements',
          columns='*',
          table='results_project_capacity_binary_economic_retirement UNION '
                'SELECT * '
                'FROM results_project_capacity_linear_economic_retirement',
          scenario_id=scenario_id
        )


class ScenarioResultsProjectNewBuild(Resource):
    """
    Currently combines new build generator and storage tables
    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """
        return create_data_table_api(
          db_path=self.db_path,
          ngifkey='results-project-new-build',
          caption='Project New Build',
          columns='*, NULL AS new_build_mwh',
          table='results_project_capacity_new_build_generator UNION '
                'SELECT * '
                'FROM results_project_capacity_new_build_storage',
          scenario_id=scenario_id
        )


class ScenarioResultsProjectDispatch(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """
        return create_data_table_api(
          db_path=self.db_path,
          ngifkey='results-project-dispatch',
          caption='Project Dispatch',
          columns='*',
          table='results_project_dispatch_all',
          scenario_id=scenario_id
        )


class ScenarioResultsProjectCarbon(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """
        return create_data_table_api(
          db_path=self.db_path,
          ngifkey='results-project-carbon',
          caption='Project Carbon Emissions',
          columns='*',
          table='results_project_carbon_emissions',
          scenario_id=scenario_id
        )


class ScenarioResultsTransmissionCapacity(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """
        return create_data_table_api(
          db_path=self.db_path,
          ngifkey='results-transmission-capacity',
          caption='Transmission Capacity',
          columns='*',
          table='results_transmission_capacity',
          scenario_id=scenario_id
        )


class ScenarioResultsTransmissionFlows(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """
        return create_data_table_api(
          db_path=self.db_path,
          ngifkey='results-transmission-flows',
          caption='Transmission Flows',
          columns='*',
          table='results_transmission_operations',
          scenario_id=scenario_id
        )


class ScenarioResultsImportsExports(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """
        return create_data_table_api(
          db_path=self.db_path,
          ngifkey='results-imports-exports',
          caption='Imports/Exports',
          columns='*',
          table='results_transmission_imports_exports',
          scenario_id=scenario_id
        )


class ScenarioResultsSystemLoadBalance(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """
        return create_data_table_api(
          db_path=self.db_path,
          ngifkey='results-system-load-balance',
          caption='Load Balance',
          columns='*',
          table='results_system_load_balance',
          scenario_id=scenario_id
        )


class ScenarioResultsSystemRPS(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """
        return create_data_table_api(
          db_path=self.db_path,
          ngifkey='results-system-rps',
          caption='RPS',
          columns='*',
          table='results_system_rps',
          scenario_id=scenario_id
        )


class ScenarioResultsSystemCarbonCap(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """
        return create_data_table_api(
          db_path=self.db_path,
          ngifkey='results-system-carbon-cap',
          caption='Carbon Cap',
          columns='*',
          table='results_system_carbon_emissions',
          scenario_id=scenario_id
        )


class ScenarioResultsSystemPRM(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id):
        """

        :return:
        """
        return create_data_table_api(
          db_path=self.db_path,
          ngifkey='results-system-prm',
          caption='PRM',
          columns='*',
          table='results_system_prm',
          scenario_id=scenario_id
        )


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

        return options_api


class ScenarioResultsDispatchPlot(Resource):
    """

    """
    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id, load_zone, horizon, ymax):
        """

        :return:
        """
        plot_api = dict()

        base_arguments_list = [
            "--return_json",
            "--database", self.db_path,
            "--scenario_id", scenario_id,
            "--load_zone", load_zone,
            "--horizon", horizon
        ]
        arguments_list_w_ymax = base_arguments_list + ["--ylimit", ymax]
        if ymax == 'default':
            plot_api["plotJSON"] = dispatch_plot.main(
              base_arguments_list
            )
        else:
            plot_api["plotJSON"] = dispatch_plot.main(
                arguments_list_w_ymax
            )

        return plot_api


class ScenarioResultsCapacityNewPlot(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id, load_zone, ymax):
        """

        :return:
        """
        plot_api = dict()

        base_arguments_list = [
            "--return_json",
            "--database", self.db_path,
            "--scenario_id", scenario_id,
            "--load_zone", load_zone,
            "--capacity_type", "new"
        ]
        arguments_list_w_ymax = base_arguments_list + ["--ylimit", ymax]

        if ymax == 'default':
            plot_api["plotJSON"] = capacity_plot.main(
                base_arguments_list
            )
        else:
            plot_api["plotJSON"] = capacity_plot.main(
                arguments_list_w_ymax
            )

        return plot_api


class ScenarioResultsCapacityRetiredPlot(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id, load_zone, ymax):
        """

        :return:
        """
        plot_api = dict()

        base_arguments_list = [
            "--return_json",
            "--database", self.db_path,
            "--scenario_id", scenario_id,
            "--load_zone", load_zone,
            "--capacity_type", "retired"
        ]
        arguments_list_w_ymax = base_arguments_list + ["--ylimit", ymax]

        if ymax == 'default':
            plot_api["plotJSON"] = capacity_plot.main(
                base_arguments_list
            )
        else:
            plot_api["plotJSON"] = capacity_plot.main(
                arguments_list_w_ymax
            )

        return plot_api


class ScenarioResultsCapacityTotalPlot(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id, load_zone, ymax):
        """

        :return:
        """
        plot_api = dict()

        base_arguments_list = [
            "--return_json",
            "--database", self.db_path,
            "--scenario_id", scenario_id,
            "--load_zone", load_zone,
            "--capacity_type", "all"
        ]
        arguments_list_w_ymax = base_arguments_list + ["--ylimit", ymax]

        if ymax == 'default':
            plot_api["plotJSON"] = capacity_plot.main(
                base_arguments_list
            )
        else:
            plot_api["plotJSON"] = capacity_plot.main(
                arguments_list_w_ymax
            )

        return plot_api


class ScenarioResultsEnergyPlot(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id, load_zone, stage, ymax):
        """

        :return:
        """
        plot_api = dict()

        base_arguments_list = [
          "--return_json",
          "--database", self.db_path,
          "--scenario_id", scenario_id,
          "--load_zone", load_zone,
          "--stage", stage
        ]
        arguments_list_w_ymax = base_arguments_list + ["--ylimit", ymax]

        if ymax == 'default':
            plot_api["plotJSON"] = energy_plot.main(
              base_arguments_list
            )
        else:
            plot_api["plotJSON"] = energy_plot.main(
              arguments_list_w_ymax
            )

        return plot_api


class ScenarioResultsCostPlot(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id, load_zone, stage, ymax):
        """

        :return:
        """
        plot_api = dict()

        base_arguments_list = [
            "--return_json",
            "--database", self.db_path,
            "--scenario_id", scenario_id,
            "--load_zone", load_zone,
            "--stage", stage
          ]
        arguments_list_w_ymax = base_arguments_list + ["--ylimit", ymax]

        if ymax == 'default':
            plot_api["plotJSON"] = cost_plot.main(
              base_arguments_list
            )
        else:
            plot_api["plotJSON"] = cost_plot.main(
              arguments_list_w_ymax
            )

        return plot_api


class ScenarioResultsCapacityFactorPlot(Resource):
    """

    """

    def __init__(self, **kwargs):
        self.db_path = kwargs["db_path"]

    def get(self, scenario_id, load_zone, stage, ymax):
        """

        :return:
        """
        plot_api = dict()

        base_arguments_list = [
          "--return_json",
          "--database", self.db_path,
          "--scenario_id", scenario_id,
          "--load_zone", load_zone,
          "--stage", stage
        ]
        arguments_list_w_ymax = base_arguments_list + ["--ylimit", ymax]

        if ymax == 'default':
            plot_api["plotJSON"] = capacity_factor_plot.main(
              base_arguments_list
            )
        else:
            plot_api["plotJSON"] = capacity_factor_plot.main(
              arguments_list_w_ymax
            )

        return plot_api


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
            return create_data_table_api_refactored(
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
              "ngIfKey": table[0].replace("_", "-"),
              "caption": table[1]
            }
            included_tables_api.append(table_api)

        return included_tables_api


def create_data_table_api(db_path, ngifkey, caption, columns, table,
                          scenario_id):
    """
    :param db_path:
    :param ngifkey:
    :param caption:
    :param columns:
    :param table:
    :param scenario_id:
    :return:
    """
    data_table_api = dict()
    data_table_api['ngIfKey'] = ngifkey
    data_table_api['caption'] = caption
    column_names, data_rows = get_table_data(
      db_path=db_path,
      columns=columns,
      table=table,
      scenario_id=scenario_id
    )
    data_table_api['columns'] = column_names
    data_table_api['rowsData'] = data_rows

    return data_table_api


def create_data_table_api_refactored(
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
    data_table_api['ngIfKey'] = table

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

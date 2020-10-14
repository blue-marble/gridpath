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

import pandas as pd
from bokeh.models import ColumnDataSource

from viz.common_functions import order_cols_by_nunique


class DataProvider(object):
    def __init__(self, conn):
        self.objective_metrics = get_objective_metrics(conn)

        # Get drop down options
        self.scenario_options = get_scenario_options(conn)
        self.period_options = get_period_options(conn, self.scenario_options)
        self.stage_options = get_stage_options(conn, self.scenario_options)
        self.zone_options = get_zone_options(conn, self.scenario_options)
        self.cap_options = ["new_build_capacity", "retired_capacity",
                            "total_capacity", "cumulative_new_build_capacity",
                            "cumulative_retired_capacity"]
        # TODO: ideally dynamically update zone_options based on selected scenarios

        # Load data for all scenarios into a set of pandas DataFrames
        self.summary = get_all_summary_data(conn, self.scenario_options)
        self.objective = get_objective_cost_data(conn, self.scenario_options)
        self.cost = get_all_cost_data(conn, self.scenario_options)
        self.energy = get_all_energy_data(conn, self.scenario_options)
        self.capacity = get_all_capacity_data(conn, self.scenario_options)

    def get_objective_src(self, scenario, stage):
        scenario = scenario if isinstance(scenario, list) else [scenario]
        df = self.objective.copy()

        scenario_filter = df["scenario"].isin(scenario)
        stage_filter = (df["stage_id"] == int(stage))
        df = df[scenario_filter & stage_filter]

        # 'Unpivot' from wide to long format (move metrics into a col)
        df = pd.melt(
            df,
            id_vars=['scenario', 'stage_id'],
            var_name='objective_metric',
            value_name='value'
        )
        # # Pivot scenarios into columms
        df = pd.pivot_table(
            df,
            index=['stage_id', 'objective_metric'],
            columns='scenario',
            values='value'
        ).reset_index().fillna(0)

        # Convert to categorical for sorting
        df['objective_metric'] = pd.Categorical(
            values=df['objective_metric'],
            categories=self.objective_metrics
        )
        df = df.sort_values(by=["objective_metric"])

        src = ColumnDataSource(df)
        return src

    def get_summary_src(self, scenario, stage, period, zone):
        scenario = scenario if isinstance(scenario, list) else [scenario]
        period = period if isinstance(period, list) else [period]
        df = self.summary.copy()

        scenario_filter = df["scenario"].isin(scenario)
        period_filter = df["period"].isin(period)
        stage_filter = (df["stage_id"] == int(stage))
        zone_filter = (df["load_zone"] == zone)

        df = df[period_filter & stage_filter & scenario_filter & zone_filter]

        # 'Unpivot' from wide to long format (move metrics into a col)
        df = pd.melt(
            df,
            id_vars=['scenario', 'stage_id', 'period', 'load_zone'],
            var_name='summary_metric',
            value_name='value'
        )
        # Pivot scenarios into columms
        df = pd.pivot_table(
            df,
            index=['load_zone', 'stage_id', 'period', 'summary_metric'],
            columns='scenario',
            values='value'
        ).reset_index().fillna(0)

        # Convert to categorical for sorting
        df['summary_metric'] = pd.Categorical(
            values=df['summary_metric'],
            categories=["capacity_cost", "operational_cost", "transmission_cost",
                        "total_cost", "load", "average_cost", "overgeneration",
                        "unserved_energy", "carbon_emissions"]
        )
        df = df.sort_values(by=["load_zone", "period", "summary_metric"])

        src = ColumnDataSource(df)
        return src

    def get_cost_src(self, scenario, stage, period, zone):
        scenario = scenario if isinstance(scenario, list) else [scenario]
        period = period if isinstance(period, list) else [period]
        df = self.cost.copy()

        scenario_filter = df["scenario"].isin(scenario)
        stage_filter = (df["stage_id"] == int(stage))
        period_filter = df["period"].isin(period)
        zone_filter = (df["load_zone"] == zone)

        df = df[scenario_filter & stage_filter & period_filter & zone_filter]
        df = df.drop(["load_zone", "stage_id"], axis=1)  # drop bc not stacked

        x_col = ["period", "scenario"]
        x_col_reordered = order_cols_by_nunique(df, x_col)
        df = df.set_index(x_col_reordered)

        src = ColumnDataSource(df)
        x_col_src = "_".join(x_col_reordered)
        return src, x_col_src

    def get_energy_src(self, scenario, stage, period, zone):
        scenario = scenario if isinstance(scenario, list) else [scenario]
        period = period if isinstance(period, list) else [period]
        df = self.energy.copy()

        scenario_filter = df["scenario"].isin(scenario)
        period_filter = df["period"].isin(period)
        stage_filter = (df["stage_id"] == int(stage))
        zone_filter = (df["load_zone"] == zone)

        df = df[scenario_filter & period_filter & stage_filter & zone_filter]
        df = df.drop(["load_zone", "stage_id"], axis=1)  # drop bc not stacked

        x_col = ["period", "scenario"]
        x_col_reordered = order_cols_by_nunique(df, x_col)
        df = df.set_index(x_col_reordered)

        src = ColumnDataSource(df)
        x_col_src = "_".join(x_col_reordered)
        return src, x_col_src

    def get_cap_src(self, scenario, stage, period, zone, capacity_metric):
        scenario = scenario if isinstance(scenario, list) else [scenario]
        period = period if isinstance(period, list) else [period]
        df = self.capacity.copy()

        scenario_filter = df["scenario"].isin(scenario)
        period_filter = df["period"].isin(period)
        stage_filter = (df["stage_id"] == int(stage))
        zone_filter = (df["load_zone"] == zone)
        cap_metric_filter = (df["capacity_metric"] == capacity_metric)

        df = df[scenario_filter & period_filter & stage_filter & zone_filter &
                cap_metric_filter]
        df = df.drop(["load_zone", "stage_id", "capacity_metric"], axis=1)

        x_col = ["period", "scenario"]
        x_col_reordered = order_cols_by_nunique(df, x_col)
        df = df.set_index(x_col_reordered)

        src = ColumnDataSource(df)
        x_col_src = "_".join(x_col_reordered)
        return src, x_col_src


def get_objective_metrics(conn):
    data = conn.execute("""SELECT * FROM results_system_costs WHERE 0 = 1;""")
    cols = [s[0] for s in data.description]
    cols = cols[3:]  # remove scenario_id, subproblem_id, stage_id
    return cols


def get_scenario_options(conn):
    scenario_options = [sc[0] for sc in conn.execute(
        """SELECT scenario_name FROM scenarios
        WHERE run_status_id = 2  --scenarios that have finished;"""
    ).fetchall()]
    return scenario_options


def get_zone_options(conn, scenarios):
    scenarios = scenarios if isinstance(scenarios, list) else [scenarios]
    # TODO: refactor with ui.server.api.scenario_results
    load_zone_options = [z[0] for z in conn.execute(
        """SELECT DISTINCT load_zone FROM inputs_geography_load_zones
        WHERE load_zone_scenario_id in (
            SELECT load_zone_scenario_id
            FROM scenarios
            WHERE scenario_name in ({})
        );""".format(",".join("?" * len(scenarios)))
        , scenarios
    ).fetchall()]

    return load_zone_options


def get_period_options(conn, scenarios):
    # TODO: refactor with ui.server.api.scenario_results
    scenarios = scenarios if isinstance(scenarios, list) else [scenarios]
    period_options = [str(p[0]) for p in conn.execute(
        """SELECT DISTINCT period FROM inputs_temporal_periods
        WHERE temporal_scenario_id in (
            SELECT temporal_scenario_id
            FROM scenarios
            WHERE scenario_name in ({})
        );""".format(",".join("?" * len(scenarios)))
        , scenarios
      ).fetchall()]

    return period_options


def get_stage_options(conn, scenarios):
    scenarios = scenarios if isinstance(scenarios, list) else [scenarios]
    stage_options = [str(s[0]) for s in conn.execute(
        """SELECT DISTINCT stage_id
        FROM inputs_temporal_subproblems_stages
        WHERE temporal_scenario_id in (
            SELECT temporal_scenario_id
            FROM scenarios
            WHERE scenario_name in ({})
        );""".format(",".join("?" * len(scenarios)))
        , scenarios
    ).fetchall()]

    return stage_options


def get_all_cost_data(conn, scenarios):
    scenarios = scenarios if isinstance(scenarios, list) else [scenarios]
    # TODO: add tx deliverability costs, but those aren't by zone!?
    #  might just keep zone NULL and make sure filter can deal with it
    sql = """SELECT scenario_name AS scenario, stage_id, period, load_zone,
        SUM(capacity_cost) AS capacity_cost, 
        SUM(variable_om_cost) AS variable_om_cost, 
        SUM(fuel_cost) AS fuel_cost, 
        SUM(startup_cost) AS startup_cost, 
        SUM(shutdown_cost) AS shutdown_cost, 
        SUM(tx_capacity_cost) AS tx_capacity_cost, 
        SUM(tx_hurdle_cost) AS tx_hurdle_cost
        FROM results_costs_by_period_load_zone
        INNER JOIN 
        (SELECT scenario_name, scenario_id FROM scenarios
         WHERE scenario_name in ({}) ) as scen_table
        USING (scenario_id)
        WHERE spinup_or_lookahead = 0
        GROUP BY scenario, stage_id, period, load_zone
        ;""".format(",".join(["?"] * len(scenarios)))
    df = pd.read_sql(sql, conn, params=scenarios).fillna(0)
    df['period'] = df['period'].astype(str)  # for categorical axis in Bokeh
    return df


def get_all_capacity_data(conn, scenarios):
    # Note: this averages capacity across subproblems within one period
    scenarios = scenarios if isinstance(scenarios, list) else [scenarios]
    sql = """SELECT scenario_name AS scenario, stage_id, period, load_zone, 
        technology, 
        -- average across subproblems
        AVG(new_build_capacity) AS new_build_capacity, 
        AVG(retired_capacity) AS retired_capacity, 
        AVG(total_capacity) AS total_capacity
        FROM (
        SELECT scenario_id, stage_id, period, load_zone, technology, 
        -- sum across projects
        SUM(new_build_mw) AS new_build_capacity, 
        SUM(retired_mw) AS retired_capacity, 
        SUM(capacity_mw) AS total_capacity
        FROM results_project_capacity
        GROUP BY scenario_id, subproblem_id, stage_id, period, load_zone, 
        technology) AS agg_tbl
        INNER JOIN 
        (SELECT scenario_name, scenario_id FROM scenarios
         WHERE scenario_name in ({}) ) as scen_table
        USING (scenario_id)
        
        GROUP BY scenario, stage_id, period, load_zone, technology;
        """.format(",".join(["?"] * len(scenarios)))
    df = pd.read_sql(sql, conn, params=scenarios).fillna(0)

    df["cumulative_new_build_capacity"] = df.groupby(
        ["scenario", "stage_id", "load_zone", "technology"]
    )["new_build_capacity"].transform(pd.Series.cumsum)
    df["cumulative_retired_capacity"] = df.groupby(
        ["scenario", "stage_id", "load_zone", "technology"]
    )["retired_capacity"].transform(pd.Series.cumsum)

    # 'Unpivot' capacity metrics from wide to long format
    df = pd.melt(
        df,
        id_vars=['scenario', 'stage_id', 'period', 'load_zone', 'technology'],
        var_name='capacity_metric',
        value_name='capacity'
    )

    # Pivot technologies to wide format (for stack chart)
    # Note: df.pivot does not work with multi-index as of pandas 1.0.5
    df = pd.pivot_table(
        df,
        index=['scenario', 'stage_id', 'period', 'load_zone',
               'capacity_metric'],
        columns='technology',
        values='capacity'
    ).fillna(0).reset_index()

    df['period'] = df['period'].astype(str)  # for categorical axis in Bokeh
    return df


def get_all_energy_data(conn, scenarios):
    # note: this will aggregate across subproblems
    scenarios = scenarios if isinstance(scenarios, list) else [scenarios]
    sql = """SELECT scenario_name AS scenario, stage_id, period, load_zone, 
        technology, 
        SUM(energy_mwh) AS energy
        FROM results_project_dispatch_by_technology_period
        INNER JOIN 
        (SELECT scenario_name, scenario_id FROM scenarios
         WHERE scenario_name in ({}) ) as scen_table
        USING (scenario_id)
        WHERE spinup_or_lookahead = 0
        GROUP BY scenario, stage_id, period, load_zone, technology;
        """.format(",".join(["?"] * len(scenarios)))
    df = pd.read_sql(sql, conn, params=scenarios).fillna(0)
    # Pivot technologies to wide format (for stack chart)
    # Note: df.pivot does not work with multi-index as of pandas 1.0.5
    df = pd.pivot_table(
        df,
        index=['scenario', 'stage_id', 'period', 'load_zone'],
        columns='technology',
        values='energy'
    ).fillna(0).reset_index()

    df['period'] = df['period'].astype(str)  # for categorical axis in Bokeh
    return df


# Data gathering functions
def get_objective_cost_data(conn, scenarios):
    # note: this will include costs that are part of spinup/lookahead tmps!
    # note: this will aggregate across subproblems
    scenarios = scenarios if isinstance(scenarios, list) else [scenarios]
    objective_metrics = get_objective_metrics(conn)
    sql1 = """SELECT scenario_name AS scenario, stage_id, """
    sql2 = ",".join(["SUM({}) AS {} ".format(c, c) for c in objective_metrics])
    sql3 = """FROM results_system_costs
        INNER JOIN
        (SELECT scenario_name, scenario_id FROM scenarios
        WHERE scenario_name in ({}) ) AS scen_table
        USING (scenario_id)

        GROUP BY scenario, stage_id
        ;""".format(",".join(["?"] * len(scenarios)))
    sql = sql1 + sql2 + sql3

    df = pd.read_sql(sql, conn, params=scenarios).fillna(0)

    return df


def get_all_summary_data(conn, scenarios):
    # TODO: could link summary columns to a python variable which can then be
    #  reused when creating the categorical column
    scenarios = scenarios if isinstance(scenarios, list) else [scenarios]
    sql = """
    SELECT scenario_name AS scenario, stage_id, period, load_zone, 
    capacity_cost, operational_cost, transmission_cost,
    (ifnull(capacity_cost, 0) 
     + ifnull(operational_cost, 0) 
     + ifnull(transmission_cost, 0)) AS total_cost, 
    load, 
    (ifnull(capacity_cost, 0) 
     + ifnull(operational_cost, 0) 
     + ifnull(transmission_cost, 0))
    /ifnull(load,0) AS average_cost, 
    overgeneration, unserved_energy, carbon_emissions

    FROM (
        SELECT scenario_id, stage_id, period, load_zone, 
        SUM(capacity_cost) AS capacity_cost,
        SUM(variable_om_cost + fuel_cost + startup_cost + shutdown_cost) AS 
        operational_cost,  
        SUM(tx_capacity_cost + tx_hurdle_cost) AS transmission_cost
        FROM results_costs_by_period_load_zone
        WHERE spinup_or_lookahead = 0
        GROUP BY scenario_id, stage_id, period, load_zone
        ) AS cost_table

    INNER JOIN 
    (SELECT scenario_id, stage_id, period, load_zone, 
    SUM(timepoint_weight * number_of_hours_in_timepoint * load_mw) AS load,
    SUM(timepoint_weight * number_of_hours_in_timepoint * overgeneration_mw) 
    AS overgeneration,
    SUM(timepoint_weight * number_of_hours_in_timepoint * unserved_energy_mw) 
    AS unserved_energy
    FROM results_system_load_balance
    WHERE spinup_or_lookahead = 0
    GROUP BY scenario_id, stage_id, period, load_zone
    ) AS load_table
    USING (scenario_id, stage_id, period, load_zone)

    INNER JOIN
    (SELECT scenario_id, stage_id, period, load_zone,
    SUM(carbon_emission_tons) AS carbon_emissions
    FROM results_project_carbon_emissions_by_technology_period
    WHERE spinup_or_lookahead = 0
    GROUP BY scenario_id, stage_id, period, load_zone
    ) AS carbon_table
    USING(scenario_id, stage_id, period, load_zone)

    INNER JOIN
    (SELECT scenario_name, scenario_id FROM scenarios
    WHERE scenario_name in ({}) ) AS scen_table
    USING (scenario_id)
    ;""".format(",".join(["?"] * len(scenarios)))

    df = pd.read_sql(sql, conn, params=scenarios).fillna(0)
    df['period'] = df['period'].astype(str)  # Bokeh CDS needs string columns

    return df

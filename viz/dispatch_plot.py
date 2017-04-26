#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Make results dispatch plot (by load zone and horizon)
"""

from argparse import ArgumentParser
from collections import OrderedDict
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import os.path
import sqlite3
import sys


def determine_x_axis(c, scenario_id, horizon, load_zone):
    """
    Determine the number of timepoints for the x axis and make a list of
    timepoints from 1 to that number
    :param c:
    :param scenario_id:
    :param horizon:
    :param load_zone:
    :return:
    """
    # Get x-axis values
    x_axis_count = c.execute(
        """SELECT COUNT(DISTINCT timepoint)
           FROM results_project_dispatch_all
           WHERE scenario_id = {}
           AND horizon = {}
           AND load_zone = '{}'""".format(
            scenario_id, horizon, load_zone
        )
    ).fetchone()[0]

    x_axis = range(1, x_axis_count + 1)

    return x_axis_count, x_axis


def determine_technologies(c, scenario_id, horizon, load_zone):
    """
    Get a list of technologies for the current
    :param c:
    :param scenario_id:
    :param horizon:
    :param load_zone:
    :return:
    """
    # Get list of technologies
    technologies_ = [str(t[0]) for t in c.execute(
        """SELECT DISTINCT technology
           FROM results_project_dispatch_all
           WHERE scenario_id = {}
           AND horizon = {}
           AND load_zone = '{}'""".format(
            scenario_id, horizon, load_zone
        )
    ).fetchall()]

    return technologies_


def get_power_by_tech_results(c, scenario_id, horizon, load_zone):
    """
    Get results for power by technology and create dictionary
    :param c:
    :param scenario_id:
    :param horizon:
    :param load_zone:
    :return:
    """
    # Power by technology
    power_by_technology_list = c.execute(
        """SELECT technology, period, horizon, timepoint,
           sum(power_mw) as power_mw
           FROM results_project_dispatch_all
           WHERE scenario_id = {}
           AND horizon = {}
           AND load_zone = '{}'
           GROUP BY load_zone, technology, timepoint;""".format(
            scenario_id, horizon, load_zone
        )
    ).fetchall()

    power_by_technology_dict = dict()
    for i in power_by_technology_list:
        tech = i[0]
        if tech in power_by_technology_dict.keys():
            power_by_technology_dict[str(tech)].append(i[4])
        else:
            power_by_technology_dict[str(tech)] = [i[4]]

    return power_by_technology_dict


def check_if_tech_exists(c, scenario_id, horizon,
                         load_zone, power_by_technology_dict, x_axis_count):
    """
    Check if the technology exists for this load_zone/horizon; if not,
    assign 0s as values in the dictionary
    :param c:
    :param scenario_id:
    :param horizon:
    :param load_zone:
    :param power_by_technology_dict:
    :param x_axis_count:
    :return:
    """
    # These are the technologies we are expecting
    # At this stage, if other technologies are specified, the script will break
    implemented_techs = [
        "Battery",
        "Biomass",
        "Coal",
        "CCGT",
        "CHP",
        "Geothermal",
        "Hydro",
        "Nuclear",
        "Peaker",
        "Pumped_Storage",
        "Small_Hydro",
        "Solar",
        "Solar_BTM",
        "Steam",
        "unspecified",
        "Wind"
    ]

    # These are the actual technologies
    technologies = determine_technologies(
        c=c,
        scenario_id=scenario_id,
        horizon=horizon,
        load_zone=load_zone
    )

    for tech in implemented_techs:
        if tech in technologies:
            pass
        else:
            power_by_technology_dict[tech] = [0] * x_axis_count

    return power_by_technology_dict


def get_variable_curtailment_results(c, scenario_id, load_zone, horizon):
    """
    Get variable generator curtailment by load_zone and horizon
    :param c:
    :param scenario_id:
    :param load_zone:
    :param horizon:
    :return:
    """
    # TODO: export curtailment by load zone directly from model
    curtailment = [
        i[1] for i in c.execute(
            """SELECT timepoint, sum(scheduled_curtailment_mw)
            FROM results_project_dispatch_variable
            WHERE scenario_id = {}
            AND load_zone = '{}'
            AND horizon = {}
            GROUP BY timepoint
            ORDER BY timepoint;""".format(
                scenario_id, load_zone, horizon
            )
        ).fetchall()
        ]

    return curtailment


def get_hydro_curtailment_results(c, scenario_id, load_zone, horizon):
    """
    Get conventional hydro curtailment by load_zone and horizon
    :param c:
    :param scenario_id:
    :param load_zone:
    :param horizon:
    :return:
    """
    # TODO: export curtailment by load zone directly from model
    curtailment = [
        i[1] for i in c.execute(
            """SELECT timepoint, sum(scheduled_curtailment_mw)
            FROM results_project_dispatch_hydro_curtailable
            WHERE scenario_id = {}
            AND load_zone = '{}'
            AND horizon = {}
            GROUP BY timepoint
            ORDER BY timepoint;""".format(
                scenario_id, load_zone, horizon
            )
        ).fetchall()
        ]

    return curtailment


def get_imports_exports_results(c, scenario_id, horizon, load_zone):
    """
    Get imports/exports results for the load zone and horizon
    :param c:
    :param scenario_id:
    :param load_zone:
    :param horizon:
    :return:
    """
    net_imports = c.execute(
        """SELECT net_imports_mw
        FROM results_transmission_imports_exports
        WHERE scenario_id = {}
        AND load_zone = '{}'
        AND horizon = {};""".format(
            scenario_id, load_zone, horizon
        )
    ).fetchall()

    imports = [i[0] if i[0] > 0 else 0 for i in net_imports]
    exports = [-e[0] if e[0] < 0 else 0 for e in net_imports]

    return imports, exports


def get_load(c, scenario_id, load_zone, horizon):
    """

    :param c:
    :param scenario_id:
    :param load_zone:
    :param horizon:
    :return:
    """
    # TODO: get this from results, not inputs
    load_zone_scenario_id = c.execute(
        """SELECT load_scenario_id
        FROM scenarios
        WHERE scenario_id = {}""".format(scenario_id)
    ).fetchone()[0]

    load_lz_h = c.execute(
        """SELECT load_mw
        FROM inputs_system_load
        WHERE load_scenario_id = {}
        AND load_zone = '{}'
        AND ROUND(timepoint/100) = {}""".format(
            load_zone_scenario_id, load_zone, horizon
        )
    ).fetchall()

    return load_lz_h


def make_figure(
        power_by_tech, curtailment_variable, curtailment_hydro,
        imports, exports, load_,
        x_axis, x_axis_count
):
    """

    :param power_by_tech:
    :param curtailment_variable:
    :param curtailment_hydro:
    :param imports:
    :param exports:
    :param load_:
    :param x_axis:
    :param x_axis_count:
    :return:
    """

    # Make figure object
    fig = plt.figure()

    # Add axes subplot
    # These are subplot grid parameters encoded as a single integer.
    # For example, "111" means "1x1 grid, first subplot" and "234" means
    # "2x3 grid, 4th subplot".
    ax = fig.add_subplot(111)

    # Assign colors to each technology
    # These are in an 'OrderedDict' because we want a specific order for the
    # legend
    tech_colors = OrderedDict([
        ("unspecified", "ghostwhite"),
        ("Nuclear", "purple"),
        ("Coal", "dimgrey"),
        ("CHP", "darkkhaki"),
        ("Geothermal", "yellowgreen"),
        ("Biomass", "olivedrab"),
        ("Small_Hydro", "mediumaquamarine"),
        ("Steam", "whitesmoke"),
        ("CCGT", "lightgrey"),
        ("Hydro", "darkblue"),
        ("Imports", "darkgrey"),
        ("Peaker", "grey"),
        ("Wind", "deepskyblue"),
        ("Solar_BTM", "orange"),
        ("Solar", "gold"),
        ("Pumped_Storage", "darkslategrey"),
        ("Battery", "teal"),
        ("Curtailment_Variable", "indianred"),
        ("Curtailment_Hydro", "firebrick")
    ])

    # Make stack plot of power by technology
    ax.stackplot(x_axis,
                 power_by_tech["unspecified"],
                 power_by_tech["Nuclear"],
                 power_by_tech["Coal"],
                 power_by_tech["CHP"],
                 power_by_tech["Geothermal"],
                 power_by_tech["Biomass"],
                 power_by_tech["Small_Hydro"],
                 power_by_tech["Steam"],
                 power_by_tech["CCGT"],
                 power_by_tech["Hydro"],
                 imports,
                 power_by_tech["Peaker"],
                 power_by_tech["Wind"],
                 power_by_tech["Solar_BTM"],
                 power_by_tech["Solar"],
                 [i if i > 0 else 0 for i in power_by_tech["Pumped_Storage"]],
                 [i if i > 0 else 0 for i in power_by_tech["Battery"]],
                 curtailment_variable,
                 # Not all load zones have curtailable hydro; list will be
                 # empty if not, so replace with 0s if list is empty to
                 # ignore in drawing the plot
                 [0] * x_axis_count if not curtailment_hydro else
                 curtailment_hydro,
                 colors=[
                     tech_colors["unspecified"],
                     tech_colors["Nuclear"],
                     tech_colors["Coal"],
                     tech_colors["CHP"],
                     tech_colors["Geothermal"],
                     tech_colors["Biomass"],
                     tech_colors["Small_Hydro"],
                     tech_colors["Steam"],
                     tech_colors["CCGT"],
                     tech_colors["Hydro"],
                     tech_colors["Imports"],
                     tech_colors["Peaker"],
                     tech_colors["Wind"],
                     tech_colors["Solar_BTM"],
                     tech_colors["Solar"],
                     tech_colors["Pumped_Storage"],
                     tech_colors["Battery"],
                     tech_colors["Curtailment_Variable"],
                     tech_colors["Curtailment_Hydro"]
                  ]
                 )

    # Can't put stackplot categories directly on legend, so make empty lines
    # and put those on legend instead
    for tech in tech_colors.keys():
        power = \
            imports if tech == 'Imports' \
            else curtailment_variable if tech == 'Curtailment_Variable' \
            else curtailment_hydro if tech == 'Curtailment_Hydro' \
            else power_by_tech[tech]
        # Don't add to legend if tech does nothing (all 0s)
        if all(round(x, 5) == 0 for x in power):
            pass
        else:
            ax.plot([],[],color=tech_colors[tech], label=tech, linewidth=5)

    # 'Load' lines
    inactive_batteries = all(x == 0 for x in power_by_tech["Battery"])
    inactive_pumped_storage = all(x == 0 for x in power_by_tech[
        "Pumped_Storage"])
    inactive_exports = all(x == 0 for x in exports)

    # Plot load + exports + pumped storage + battery
    if inactive_batteries:
        pass  # don't plot if batteries aren't doing anything
    else:
        # Change label if no exports and/or pumped storage
        battery_label = \
            'Load' + \
            str('' if inactive_exports else ' + Exports') + \
            str('' if inactive_pumped_storage else ' + Pumped Storage') + \
            ' + Battery'

        ax.plot(range(1, x_axis_count + 1),
                [load_[i][0] + exports[i] +
                 [-x if x < 0 else 0 for x in power_by_tech["Pumped_Storage"]][
                     i] +
                 [-x if x < 0 else 0 for x in power_by_tech["Battery"]][i]
                 for i in range(0, x_axis_count)],
                color=tech_colors["Battery"],
                label=battery_label,
                linewidth=1, linestyle="--")

    # Plot load + exports + pumped storage
    if inactive_pumped_storage:
        pass  # don't plot if pumped storage isn't doing anything
    else:
        # Change label if no exports
        ps_label = \
            'Load' + \
            str('' if inactive_exports else ' + Exports') + \
            ' + Pumped_Storage'
        ax.plot(range(1, x_axis_count + 1),
                 [load_[i][0] + exports[i] +
                  [-x if x < 0 else 0 for x in power_by_tech["Pumped_Storage"]][i]
                  for i in range(0, x_axis_count)],
                color=tech_colors["Pumped_Storage"],
                label=ps_label,
                linewidth=2, linestyle="--")

    # Plot load + exports
    if inactive_exports:
        pass
    else:
        ax.plot(range(1, x_axis_count + 1),
                [load_[i][0] + exports[i] for i in range(0, x_axis_count)],
                color='black', label='Load + Exports', linewidth=2,
                linestyle="--")

    # Plot load
    ax.plot(range(1, x_axis_count + 1), [l[0] for l in load_],
            color='black', label='Load', linewidth=2)

    return fig, ax


def prettify_figure(load_zone, horizon, fig, ax, x_axis_count):
    """
    Make graph nice
    :param load_zone:
    :param horizon:
    :param fig:
    :param ax:
    :param x_axis_count:
    :return:
    """

    # Shrink vertical axis to make space for legend
    box = ax.get_position()
    ax.set_position(
        [box.x0, box.y0 + box.height * 0.25,
         box.width, box.height * 0.8]
    )

    # Axes labels and title
    plt.xlabel('Hour Ending')
    plt.ylabel('MW')
    plt.title(str(load_zone) + ", "
              + str(horizon)[0:4] + ", day " + str(horizon)[-2:],
              fontweight='bold')

    # Legend below axes, 4 columns, move down, reduce font size
    plt.legend(loc="lower center", ncol=4, bbox_to_anchor=(0.4825, -0.475),
               fontsize=7.5)

    # Set x axis ticks
    plt.xticks(np.arange(1, x_axis_count + 1, 1))
    for tick in ax.xaxis.get_major_ticks():
                    tick.label.set_fontsize(10)
                    tick.label.set_rotation('vertical')

    # Format y axis tick labels (thousands with a comma)
    ax.get_yaxis().set_major_formatter(
        ticker.FuncFormatter(lambda x, p: format(int(x), ',')))

    return fig, ax


def draw_dispatch_plot(c, scenario_id, horizon, load_zone, arguments):
    # X axis
    x_axis_count_results, x_axis_results = determine_x_axis(
        c=c,
        scenario_id=scenario_id,
        horizon=horizon,
        load_zone=load_zone
    )

    # Data values
    power_by_tech_results = check_if_tech_exists(
        c=c,
        scenario_id=scenario_id,
        horizon=horizon,
        load_zone=load_zone,
        power_by_technology_dict=get_power_by_tech_results(
            c=c,
            scenario_id=scenario_id,
            horizon=horizon,
            load_zone=load_zone
        ),
        x_axis_count=x_axis_count_results
    )

    curtailment_variable_results = get_variable_curtailment_results(
        c=c,
        scenario_id=scenario_id,
        horizon=horizon,
        load_zone=load_zone
    )

    curtailment_hydro_results = get_hydro_curtailment_results(
        c=c,
        scenario_id=scenario_id,
        horizon=horizon,
        load_zone=load_zone
    )

    imports_results, exports_results = get_imports_exports_results(
        c=c,
        scenario_id=scenario_id,
        horizon=horizon,
        load_zone=load_zone
    )

    load_results = get_load(
        c=c,
        scenario_id=scenario_id,
        horizon=horizon,
        load_zone=load_zone
    )

    # Make figure
    figure, axes = make_figure(
        power_by_tech=power_by_tech_results,
        curtailment_variable=curtailment_variable_results,
        curtailment_hydro=curtailment_hydro_results,
        imports=imports_results, exports=exports_results,
        load_=load_results,
        x_axis=x_axis_results,
        x_axis_count=x_axis_count_results
    )

    # Make figure nicer
    pretty_figure, pretty_axes = prettify_figure(
        load_zone=load_zone, horizon=horizon,
        fig=figure, ax=axes, x_axis_count=x_axis_count_results
    )

    # Show and/or save the figure
    if not arguments.save_only:
        plt.show()

    if arguments.save or arguments.save_only:
        plt.savefig(
            "dispatch_plot_{}_{}".format(
                str(load_zone), str(horizon)
            )
        )

# if __name__ == "__main__":
#     args = sys.argv[1:]
#     parsed_args = parse_arguments(arguments=args)
#
#     # Which dispatch plot are we making
#     SCENARIO_NAME = parsed_args.scenario
#     HORIZON = parsed_args.horizon
#     LOAD_ZONE = parsed_args.load_zone
#
#     # Connect to database
#     io = connect_to_database(parsed_args)
#     cursor = io.cursor()
#
#     # Get the scenario ID
#     SCENARIO_ID = cursor.execute(
#         """SELECT scenario_id
#         FROM scenarios
#         WHERE scenario_name = '{}';""".format(SCENARIO_NAME)
#     ).fetchone()[0]
#
#     draw_dispatch_plot(
#         c=cursor,
#         scenario_id=SCENARIO_ID,
#         horizon=HORIZON,
#         load_zone=LOAD_ZONE,
#         arguments=parsed_args
#     )
#
#     # # X axis
#     # x_axis_count_results, x_axis_results = determine_x_axis(
#     #     c=cursor,
#     #     scenario_id=SCENARIO_ID,
#     #     horizon=HORIZON,
#     #     load_zone=LOAD_ZONE
#     # )
#     #
#     # # Data values
#     # power_by_tech_results = check_if_tech_exists(
#     #     power_by_technology_dict=get_power_by_tech_results(
#     #         c=cursor,
#     #         scenario_id=SCENARIO_ID,
#     #         horizon=HORIZON,
#     #         load_zone=LOAD_ZONE
#     #     ),
#     #     x_axis_count=x_axis_count_results
#     # )
#     #
#     # imports_results, exports_results = get_imports_exports_results(
#     #     c=cursor,
#     #     scenario_id=SCENARIO_ID,
#     #     horizon=HORIZON,
#     #     load_zone=LOAD_ZONE
#     # )
#     #
#     # load_results = get_load(
#     #     c=cursor,
#     #     scenario_id=SCENARIO_ID,
#     #     horizon=HORIZON,
#     #     load_zone=LOAD_ZONE
#     # )
#     #
#     # # Make figure
#     # figure, axes = make_figure(
#     #     power_by_tech=power_by_tech_results,
#     #     imports=imports_results, exports=exports_results,
#     #     load_=load_results,
#     #     x_axis=x_axis_results,
#     #     x_axis_count=x_axis_count_results
#     # )
#     #
#     # # Make figure nicer
#     # pretty_figure, pretty_axes = prettify_figure(
#     #     load_zone=LOAD_ZONE, horizon=HORIZON,
#     #     fig=figure, ax=axes, x_axis_count=x_axis_count_results
#     # )
#     #
#     # # Show and/or save the figure
#     # if not parsed_args.save_only:
#     #     plt.show()
#     #
#     # if parsed_args.save or parsed_args.save_only:
#     #     plt.savefig(
#     #         "dispatch_plot_{}_{}".format(
#     #             str(LOAD_ZONE), str(HORIZON)
#     #         )
#     #     )

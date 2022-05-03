import csv
import os.path


def fix_variables(m, d, scenario_directory, subproblem, stage):
    """
    Don't allow market participation if the final participation stage was before the
    current stage
    """
    if m.first_stage_flag:  # buy/sell variables not fixed in the first stage
        pass
    else:
        for (z, hub, tmp) in m.LZ_MARKETS * m.TMPS:
            if m.no_market_participation_in_stage[z, hub]:
                m.Sell_Power[z, hub, tmp] = 0
                m.Sell_Power[z, hub, tmp].fixed = True

                m.Buy_Power[z, hub, tmp] = 0
                m.Buy_Power[z, hub, tmp].fixed = True
            else:
                pass


def write_pass_through_file_headers(pass_through_directory):
    with open(
        os.path.join(pass_through_directory, "market_positions.tab"),
        "w",
        newline="",
    ) as market_positions_file:
        writer = csv.writer(market_positions_file, delimiter="\t", lineterminator="\n")
        writer.writerow(
            [
                "load_zone",
                "market" "timepoint",
                "stage",
                "final_sell_power_position",
                "final_buy_power_position",
            ]
        )


def export_pass_through_inputs(scenario_directory, subproblem, stage, m):
    """
    This function exports the market position for all load zones and markets. This
    becomes the starting position for the following stage (for load balance purposes).

    :param scenario_directory:
    :param subproblem:
    :param stage:
    :param m:
    :return:
    """

    with open(
        os.path.join(
            scenario_directory,
            subproblem,
            "pass_through_inputs",
            "market_positions.tab",
        ),
        "a",
    ) as market_positions_file:
        fixed_commitment_writer = csv.writer(
            market_positions_file, delimiter="\t", lineterminator="\n"
        )
        for (lz, m, tmp) in m.LZ_MARKETS * m.TMPS:
            fixed_commitment_writer.writerow(
                [
                    lz,
                    m,
                    tmp,
                    stage,
                    m.Final_Sell_Power_Position[lz, m, tmp].expr.value,
                    m.Final_Buy_Power_Position[lz, m, tmp].expr.value,
                ]
            )

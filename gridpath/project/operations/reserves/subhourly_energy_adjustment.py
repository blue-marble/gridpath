#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.
from gridpath.auxiliary.dynamic_components import \
    headroom_variables, footroom_variables, \
    reserve_to_energy_adjustment_params


def footroom_subhourly_energy_adjustment_rule(d, mod, g, tmp):
    """
    Subhourly curtailment (difference from scheduled energy) from providing
    downward reserves
    :param d:
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    subhourly_footroom_adjustment = \
        sum(
            getattr(mod, c)[g, tmp] *
            # This is tricky
            # We need to get the value of the adjustment param
            # The adjustment parameter name varies by reserve type and its
            # value varies by balancing area
            # The balancing area param names also varies by reserve type
            # In the dynamic components, we have created a dictionary
            # that has the reserve variable name as key and a tuple as
            # value for each key: the first value in the tuple is the
            # subhourly adjustment parameter name and the second
            # tuple value is the balancing area parameter name (for this
            # type of reserve)
            # Here, we are getting the value for the following:
            # subhourly_adjustment_param[this type of reserve][
            getattr(mod,
                    getattr(d,
                            reserve_to_energy_adjustment_params
                            )[c][0]  # this is the adjustment param name
                    )[
                getattr(mod,
                        getattr(
                            d,
                            reserve_to_energy_adjustment_params
                        )[c][1]  # this is the balancing area param name
                        )[g]  # the balancing area (value) varies by g
            ]  # the index of the adjustment param is a balancing area
            # adjustment param name and BA param name vary by reserve type
            for c in getattr(d, footroom_variables)[g]
        )

    return subhourly_footroom_adjustment


def headroom_subhourly_energy_adjustment_rule(d, mod, g, tmp):
    """
    Subhourly additional energy delivered from providing upward reserves
    :param d:
    :param mod:
    :param g:
    :param tmp:
    :return:
    """
    subhourly_headroom_adjustment = \
        sum(
            getattr(mod, c)[g, tmp] *
            # This is tricky
            # We need to get the value of the adjustment param
            # The adjustment parameter name varies by reserve type and its
            # value varies by balancing area
            # The balancing area param names also varies by reserve type
            # In the dynamic components, we have created a dictionary
            # that has the reserve variable name as key and a tuple as
            # value for each key: the first value in the tuple is the
            # subhourly adjustment parameter name and the second
            # tuple value is the balancing area parameter name (for this
            # type of reserve)
            # Here, we are getting the value for the following:
            # subhourly_adjustment_param[this type of reserve][
            getattr(mod,
                    getattr(d,
                            reserve_to_energy_adjustment_params
                            )[c][0]  # this is the adjustment param name
                    )[
                getattr(mod,
                        getattr(
                            d,
                            reserve_to_energy_adjustment_params
                        )[c][1]  # this is the balancing area param name
                        )[g]  # the balancing area (value) varies by g
            ]  # the index of the adjustment param is a balancing area
            # adjustment param name and BA param name vary by reserve type
            for c in getattr(d, headroom_variables)[g]
        )

    return subhourly_headroom_adjustment

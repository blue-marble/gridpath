# Copyright 2026 Sylvan Energy Analytics LLC
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
Helpers for aggregating a project's reserve-provision variables in a
timepoint (headroom/footroom sums and their derated variants).

The reserve variable, derate-param, and balancing-area-param *names* live in
the dynamic components (as strings). Resolving those names with getattr on
every project-timepoint can be a significant share of model construction time,
so the resolved component objects (and per-project param values, which don't
vary by timepoint) are cached on the model instance on first use.
"""

from gridpath.auxiliary.dynamic_components import (
    headroom_variables,
    footroom_variables,
    reserve_variable_derate_params,
    reserve_to_energy_adjustment_params,
)

_CACHE_ATTR = "_gridpath_reserve_component_cache"


def _get_cache(d, mod, key, builder):
    cache = getattr(mod, _CACHE_ATTR, None)
    if cache is None:
        cache = {}
        setattr(mod, _CACHE_ATTR, cache)
    if key not in cache:
        cache[key] = builder(d, mod, key)
    return cache[key]


def _direction_attr(direction):
    return headroom_variables if direction == "headroom" else footroom_variables


def _build_vars_by_prj(d, mod, key):
    """{prj: [reserve Var component, ...]}"""
    direction = key[0]
    comp_by_name = {}
    return {
        prj: [comp_by_name.setdefault(c, getattr(mod, c)) for c in names]
        for prj, names in getattr(d, _direction_attr(direction)).items()
    }


def _build_derated_vars_by_prj(d, mod, key):
    """{prj: [(reserve Var component, derate param value for prj), ...]}"""
    direction = key[0]
    derate_param_names = getattr(d, reserve_variable_derate_params)
    comp_by_name = {}
    return {
        prj: [
            (
                comp_by_name.setdefault(c, getattr(mod, c)),
                getattr(mod, derate_param_names[c])[prj],
            )
            for c in names
        ]
        for prj, names in getattr(d, _direction_attr(direction)).items()
    }


def _build_adjusted_vars_by_prj(d, mod, key):
    """{prj: [(reserve Var component, balancing area or None, subhourly
    adjustment param value for that balancing area), ...]}

    The adjustment parameter name varies by reserve type and its value
    varies by balancing area. A project in a single balancing area
    contributes its total provision variable (indexed by project and
    timepoint; recorded with a balancing area of None) times that area's
    adjustment. A project in several balancing areas contributes, per area,
    its allocation variable (indexed by project, area and timepoint) times
    the area's adjustment. The component names needed to resolve this are
    recorded in the dynamic components by each reserve module.

    To save on memory, terms whose adjustment value is 0 (the param default)
    are dropped: a 0 x Var term contributes exactly 0 to the subhourly
    adjustment sums, so the values of the resulting expressions are
    unchanged, but the expressions -- one per project-timepoint -- don't
    store zero-valued terms.
    """
    direction = key[0]
    adjustment_params = getattr(d, reserve_to_energy_adjustment_params)
    comp_by_name = {}
    adjusted_vars_by_prj = {}
    for prj, names in getattr(d, _direction_attr(direction)).items():
        terms = []
        for c in names:
            adj_param_name, bas_by_prj_set_name, provision_by_ba_var_name = (
                adjustment_params[c]
            )
            adj_param = getattr(mod, adj_param_name)
            bas = getattr(mod, bas_by_prj_set_name)[prj]
            if len(bas) == 1:
                adj = adj_param[bas.first()]
                if adj != 0:
                    terms.append(
                        (comp_by_name.setdefault(c, getattr(mod, c)), None, adj)
                    )
            else:
                provision_by_ba = comp_by_name.setdefault(
                    provision_by_ba_var_name, getattr(mod, provision_by_ba_var_name)
                )
                for ba in bas:
                    adj = adj_param[ba]
                    if adj != 0:
                        terms.append((provision_by_ba, ba, adj))
        adjusted_vars_by_prj[prj] = terms

    return adjusted_vars_by_prj


def headroom_provision_rule(d, mod, prj, tmp):
    """Sum of the project's headroom (upward reserve) variables in tmp."""
    return sum(
        v[prj, tmp]
        for v in _get_cache(d, mod, ("headroom", "vars"), _build_vars_by_prj)[prj]
    )


def footroom_provision_rule(d, mod, prj, tmp):
    """Sum of the project's footroom (downward reserve) variables in tmp."""
    return sum(
        v[prj, tmp]
        for v in _get_cache(d, mod, ("footroom", "vars"), _build_vars_by_prj)[prj]
    )


def derated_headroom_provision_rule(d, mod, prj, tmp):
    """Sum of the project's headroom variables in tmp, each derated."""
    return sum(
        v[prj, tmp] / derate
        for (v, derate) in _get_cache(
            d, mod, ("headroom", "derated"), _build_derated_vars_by_prj
        )[prj]
    )


def derated_footroom_provision_rule(d, mod, prj, tmp):
    """Sum of the project's footroom variables in tmp, each derated."""
    return sum(
        v[prj, tmp] / derate
        for (v, derate) in _get_cache(
            d, mod, ("footroom", "derated"), _build_derated_vars_by_prj
        )[prj]
    )


def subhourly_headroom_adjustment_rule(d, mod, prj, tmp):
    """Sum of the project's headroom variables in tmp, each multiplied by
    its reserve type's subhourly energy adjustment for the project's
    balancing area."""
    return sum(
        (v[prj, tmp] if ba is None else v[prj, ba, tmp]) * adj
        for (v, ba, adj) in _get_cache(
            d, mod, ("headroom", "adjusted"), _build_adjusted_vars_by_prj
        )[prj]
    )


def subhourly_footroom_adjustment_rule(d, mod, prj, tmp):
    """Sum of the project's footroom variables in tmp, each multiplied by
    its reserve type's subhourly energy adjustment for the project's
    balancing area."""
    return sum(
        (v[prj, tmp] if ba is None else v[prj, ba, tmp]) * adj
        for (v, ba, adj) in _get_cache(
            d, mod, ("footroom", "adjusted"), _build_adjusted_vars_by_prj
        )[prj]
    )

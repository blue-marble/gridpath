# Copyright 2016-2023 Blue Marble Analytics LLC.
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


from pyomo.environ import Set, Expression

from gridpath.project.operations.reserves.reserve_provision import (
    provision_to_ba_terms,
)

_TERMS_CACHE_ATTR = "_gridpath_reserve_provision_to_ba_terms"


def get_provision_to_ba_terms(
    mod,
    reserve_prjs_by_ba_set,
    reserve_multi_ba_prjs_set,
    generator_reserve_provision_variable,
    generator_reserve_provision_by_ba_variable,
):
    """
    The per-BA contribution terms of a reserve type (see
    :code:`provision_to_ba_terms`), resolved once per reserve type and cached
    on the instance rather than rebuilt for every (BA, timepoint).
    """
    cache = getattr(mod, _TERMS_CACHE_ATTR, None)
    if cache is None:
        cache = {}
        setattr(mod, _TERMS_CACHE_ATTR, cache)
    if generator_reserve_provision_variable not in cache:
        cache[generator_reserve_provision_variable] = provision_to_ba_terms(
            mod=mod,
            reserve_prjs_by_ba_set=reserve_prjs_by_ba_set,
            reserve_multi_ba_prjs_set=reserve_multi_ba_prjs_set,
            reserve_provision_variable_name=generator_reserve_provision_variable,
            reserve_provision_by_ba_variable_name=generator_reserve_provision_by_ba_variable,
        )
    return cache[generator_reserve_provision_variable]


def generic_add_model_components(
    m,
    d,
    reserve_prjs_by_ba_set,
    reserve_multi_ba_prjs_set,
    reserve_zone_set,
    reserve_generator_set,
    generator_reserve_provision_variable,
    generator_reserve_provision_by_ba_variable,
    total_reserve_provision_expression,
):
    """
    Generic treatment of reserves. This function creates model components
    related to a particular reserve requirement, including
    1) an expression aggregating generator-level provision to total provision
    by balancing area: a project in a single BA contributes its total
    provision; a project in several BAs contributes its allocation to each
    :param m:
    :param d:
    :param reserve_prjs_by_ba_set:
    :param reserve_multi_ba_prjs_set:
    :param reserve_zone_set:
    :param reserve_generator_set:
    :param generator_reserve_provision_variable:
    :param generator_reserve_provision_by_ba_variable:
    :param total_reserve_provision_expression:
    :return:
    """

    # Reserve generators operational generators in timepoint
    # This will be the intersection of the reserve generator set and the set of
    # generators operational in the timepoint
    op_set = str(reserve_generator_set) + "_OPERATIONAL_IN_TIMEPOINT"
    setattr(
        m,
        op_set,
        Set(
            m.TMPS,
            initialize=lambda mod, tmp: getattr(mod, reserve_generator_set)
            & mod.OPR_PRJS_IN_TMP[tmp],
        ),
    )

    # Reserve provision
    def total_reserve_rule(mod, ba, tmp):
        operational_prjs = getattr(mod, op_set)[tmp]
        return sum(
            var[idx + (tmp,)]
            for (prj, var, idx) in get_provision_to_ba_terms(
                mod,
                reserve_prjs_by_ba_set,
                reserve_multi_ba_prjs_set,
                generator_reserve_provision_variable,
                generator_reserve_provision_by_ba_variable,
            ).get(ba, [])
            if prj in operational_prjs
        )

    setattr(
        m,
        total_reserve_provision_expression,
        Expression(getattr(m, reserve_zone_set), m.TMPS, rule=total_reserve_rule),
    )

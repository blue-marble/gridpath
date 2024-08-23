# Copyright 2016-2023 Blue Marble Analytics LLC. All rights reserved.

"""

**Relevant tables:**

+--------------------------------+-----------------------------------------------+
|:code:`scenarios` table column  |:code:`project_operational_chars_scenario_id`  |
+--------------------------------+-----------------------------------------------+
|:code:`scenarios` table feature |N/A                                            |
+--------------------------------+-----------------------------------------------+
|:code:`subscenario_` table      |:code:`subscenarios_project_operational_chars` |
+--------------------------------+-----------------------------------------------+
|:code:`input_` tables           |:code:`inputs_project_operational_chars`       |
+--------------------------------+-----------------------------------------------+

The user must decide how to model the operations of *projects*, e.g. is this
a fuel-based dispatchable (CCGT) or baseload project (nuclear), is it an
intermittent plant, is it a battery, etc. In GridPath, this is called the
project’s *operational type*. All implemented operational types are listed
in the :code:`mod_operational_types` table.

Each *operational type* has an associated set of characteristics, which must
be included in the :code:`inputs_project_operational_chars` table. The primary
key of this table is the :code:`project_operational_chars_scenario_id`,
which is also the column that determines project operational characteristics
for a scenario via the :code:`scenarios` table, and the project. If a
project’s operational type changes (e.g. the user decides to model a coal
plant as, say, :code:`gen_always_on` instead of :code:`gen_commit_bin`) or the
user wants to modify one of its operating characteristics (e.g. its minimum
loading level), then a new :code:`project_operational_chars_scenario_id` must
be created and all projects listed again, even if the rest of the projects'
operating types and characteristics do not change.

The ability to provide each type of reserve is currently an 'operating
characteristic' determined via the :code:`inputs_project_operational_chars`
table.

Not all operational types have all the characteristics in
the :code:`inputs_project_operational_chars`. GridPath's validation suite
does check whether certain required characteristic for an operational type are
populated and warns the user if some characteristics that have been filled
are actually not used by the respective operational type. See the matrix below
for the required and optional characteristics for each operational type.

.. image:: ../graphics/optype_opchar_matrix.svg

Several types of operational characteristics vary by dimensions are other
than project, so they are input in separate tables and linked to the
:code:`inputs_project_operational_chars` via an ID column. These include
heat rates, variable generator profiles, and hydro characteristics.

"""

if __name__ == "__main__":
    print(__doc__)

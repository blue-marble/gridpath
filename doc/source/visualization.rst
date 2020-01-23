#############
Visualization
#############

**********
Background
**********

GridPath constains a Visualization package that helps user visualize some of
the inputs and outputs of the model. The package uses the
`Bokeh <https://bokeh.org/>`_ interactive plotting library and is located in
the :code:`./viz` folder. The plotting data is pulled directly from the GridPath
database, so users need a functioning database to use this package.

The plotting package consists of a set of plotting scripts that can be called
either from the command line or through the GridPath User Interface. For
instance, to obtain a plot that shows the total installed capacity across
modeling periods for a certain scenario you would navigate to the :code:`./viz`
folder and run the following::

    python capacity_total_plot.py --scenario test --load_zone CAISO --show

The next section provides a brief description of each plotting script and
its arguments. As GridPath evolves we expect the list of visualizations to grow.

****************
Plotting scripts
****************

.. Note:: Generally capacity expansion problems will have only one subproblem/
   stage. If not specified, the plotting module assumes the subproblem and stage
   are equal to 1, which is the default if there's only one subproblem/stage.

gridpath.viz.capacity_factor_plot
---------------------------------

.. automodule:: viz.capacity_factor_plot

.. argparse::
   :module: viz.capacity_new_plot
   :func: create_parser
   :prog: capacity_factor_plot.py

gridpath.viz.capacity_new_plot
------------------------------

.. automodule:: viz.capacity_new_plot

.. argparse::
   :module: viz.capacity_new_plot
   :func: create_parser
   :prog: capacity_new_plot.py

gridpath.viz.capacity_retired_plot
----------------------------------

.. automodule:: viz.capacity_retired_plot

.. argparse::
   :module: viz.capacity_retired_plot
   :func: create_parser
   :prog: capacity_retired_plot.py

gridpath.viz.capacity_total_plot
--------------------------------

.. automodule:: viz.capacity_total_plot

.. argparse::
   :module: viz.capacity_total_plot
   :func: create_parser
   :prog: capacity_total_plot.py

gridpath.viz.capacity_total_loadzone_comparison_plot
----------------------------------------------------

.. automodule:: viz.capacity_total_loadzone_comparison_plot

.. argparse::
   :module: viz.capacity_total_loadzone_comparison_plot
   :func: create_parser
   :prog: capacity_total_loadzone_comparison_plot.py

gridpath.viz.capacity_total_scenario_comparison_plot
----------------------------------------------------

.. automodule:: viz.capacity_total_scenario_comparison_plot

.. argparse::
   :module: viz.capacity_total_scenario_comparison_plot
   :func: create_parser
   :prog: capacity_total_scenario_comparison_plot.py

gridpath.viz.carbon_plot
------------------------

.. automodule:: viz.carbon_plot

.. argparse::
   :module: viz.carbon_plot
   :func: create_parser
   :prog: carbon_plot.py

gridpath.viz.rps_plot
---------------------

.. automodule:: viz.rps_plot

.. argparse::
   :module: viz.rps_plot
   :func: create_parser
   :prog: rps_plot.py

gridpath.viz.cost_plot
----------------------

.. automodule:: viz.cost_plot

.. argparse::
   :module: viz.cost_plot
   :func: create_parser
   :prog: cost_plot.py

gridpath.viz.dispatch_plot
--------------------------

.. automodule:: viz.dispatch_plot

.. argparse::
   :module: viz.dispatch_plot
   :func: create_parser
   :prog: dispatch_plot.py

gridpath.viz.energy_plot
------------------------

.. automodule:: viz.energy_plot

.. argparse::
   :module: viz.energy_plot
   :func: create_parser
   :prog: energy_plot.py

gridpath.viz.curtailment_hydro_heatmap_plot
-------------------------------------------

.. automodule:: viz.curtailment_hydro_heatmap_plot

.. argparse::
   :module: viz.curtailment_hydro_heatmap_plot
   :func: create_parser
   :prog: curtailment_hydro_heatmap_plot.py

gridpath.viz.curtailment_variable_heatmap_plot
----------------------------------------------

.. automodule:: viz.curtailment_variable_heatmap_plot

.. argparse::
   :module: viz.curtailment_variable_heatmap_plot
   :func: create_parser
   :prog: curtailment_variable_heatmap_plot.py

gridpath.viz.project_operations_plot
------------------------------------

.. automodule:: viz.project_operations_plot

.. argparse::
   :module: viz.project_operations_plot
   :func: create_parser
   :prog: project_operations_plot.py
#######################
GridPath User Interface
#######################

The GridPath user interface (UI) makes it possible to interact with the
platform without relying on the command line. We will be distributing compiled
versions of the UI for Windows and Mac. You can also build the UI from
source (instructions are in the :code:`README.md` file in GridPath's
:code:`ui` package). Here we provide instructions for how to *use* the UI.


**********
Navigation
**********

The GridPath UI has a navigation bar at the top with five different screens
- :code:`Home`, :code:`Scenarios`, :code:`Scenarios Comparison`, :code:`New
Scenario`, and :code:`Settings`. The screen you are currently viewing will
be highlighted. Descriptions of the functionality available on each screen
are below.


********
Settings
********

Using the UI requires that several settings be specified. To do so, open the
UI and go to the :code:`Settings` screen (top right corner of the navigation
bar). You will see two tables, one for :code:`UI Settings` and another one for
:code:`Solvers`.

In the :code:`UI Settings` table, you must specify the directory where
scenarios will be written, the GridPath database file to use, and the
directory of your GridPath Python environment. In the :code:`Solvers` table,
you must specify up to three different solvers and the location of the
solver executables that the UI can then use to solve scenarios.

Scenarios Directory
*******************

The :code:`Scenarios Directory` can be any folder in your file system. To
select one click the :code:`Browse` button in the 'Change to' row of the
:code:`Scenarios Directory` table and select a folder. For the changes to
take effect, you will need to restart the UI. The 'Status' row will warn you
if this is the case (it will show 'not set' if you haven't selected a
scenarios directory yet, 'restart required' if you need to restart for the
selected directory to be recognized by the UI, or 'set' if a directory has
been selected and no further action is required.

GridPath Database
*****************

The GridPath UI uses a GridPath database file to manage inputs and outputs.
This database must conform to the GridPath database schema and be
pre-populated with input data. You can then use the UI to create and run
scenarios, and to view results. You must select the database file to use in
the :code:`Settings` screen by clicking the :code:`Browse` button in the
'Change to' row of the :code:`GridPath` table and selecting the database file
to use. For any changes to take effect, you will need to restart the UI. The
'Status' row will warn you if this is the case (it will show 'not set' if
you haven't selected a database file yet, 'restart required' if you
need to restart for the selected database file to be recognize by the UI, or
'set' if a database file has been selected and no further action is required.

GridPath Python Environment Directory
*************************************

The GridPath UI uses your GridPath Python installation. Before using it, you
must install GridPath using the instructions in
:ref:`installation-section-ref`. In particular, you must point the UI to
your GridPath Python environment directory :code:`PATH/TO/PYTHON/ENV` (see
:ref:`python-virtual-env-section-ref`). To select the directory click the
:code:`Browse` button in the 'Change to' row of the :code:`Scenarios
Directory` table and select the Python environment folder. For the changes to
take effect, you will need to restart the UI. The 'Status' row will warn you
if this is the case (it will show 'not set' if you haven't selected
an environment directory yet, 'restart required' if you need to restart for the
selected directory to be recognized by the UI, or 'set' if a directory has
been selected and no further action is required.

.. Note:: The GridPath UI server will not work until the Python environment
    directory has been selected and the UI restarted.

.. image:: ../graphics/ui_ui_settings.png

Solvers
*******
You must tell the GridPath UI where the executables are located for solvers
that you want to use to solve scenarios. You can have the UI use up to three
different solvers at a time. Select a solver name from the drop-down menu in
the 'Change to' row for one of the three solvers and then find the
executable for that solver using the :code:`Browse` button in the respective
row. The 'Status' row will warn you if a restart is required for either the
solver name or executable value to take effect.

.. image:: ../graphics/ui_solver_settings.png

****
Home
****

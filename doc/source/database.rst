******************
Database Structure
******************

All tables names in the GridPath database start with one of seven prefixes:
:code:`mod_`, :code:`subscenario_`, :code:`input_`, :code:`scenarios`,
:code:`options_`, :code:`status_`, or :code:`ui_`. This structure is meant to
organize the tables by their function. Below are descriptions of each table
type and its role, and of the kind of data tables of this type contain.

The :code:`mod_` Tables
***********************
The :code:`mod_` should not be modified except by developers. These contain
various data used by the GridPath platform to describe available
functionality, help enforce input data consistency and integrity, and aid in
validation.


The :code:`subscenario_` and :code:`input_` Tables
**************************************************

The :code:`scenarios` Table
***************************

The :code:`options_` Tables
***************************

The :code:`status_` Tables
**************************

The :code:`ui_` Tables
**********************


*********************
Building the Database
*********************

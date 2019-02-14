This is a simple UI sandbox with two buttons, one to test that we can launch
Python ('Test Python') and another that we can create and access an SQLite 
database ('Test SQLite'). Clicking on each of the buttons will prompt you to 
select a directory where to write the respective files. 

Clicking the 'Test Python' button should create a text file called 
'hello_world_from_python.txt' containing the text  'Hello World from Python!' 
in the directory you select. This assumes you have Python installed.

Clicking the 'Test SQLite' button should create a database file called 
'hello_world_from_sqlite.db' in the directory you select. The database should
contain one table called 'sample_table' with columns named 'id' and 
'input_value' containing values of 1 and 'it worked!' respectively.

The rest of this README assumes you have Node.js installed and are managing 
packages with npm.

Navigate to the 'ui' directory and install the required modules with:
>> npm install

Then you must rebuild the native dependencies with electron-builder.
Native dependencies currently include: sqlite3
>> npm run postinstall

Build the app with:
>> npm run dist

On Mac, the app is under ui/dist/mac.

This version builds on MacOS Mojave 10.14.3 with electron-builder ^20.38.5 and 
electron 4.0.3. 
NOTE: I manually changed the Electron version to 4.0.3 from 4.0.4 to get it to 
build due to this bug: 
https://github.com/electron-userland/electron-builder/issues/3660
(The build failed on electron 4.0.4 with the same message as in that issue.)
More on this bug here: https://github.com/electron/electron/pull/16687

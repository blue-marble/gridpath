'use strict';

const { remote } = require('electron');
const path = require('path');
const sqlite3 = require('sqlite3').verbose();
const dialog = remote.require('electron').dialog;

const TestPythonButton = document.getElementById('TestPythonButton');
const TestSQLiteButton = document.getElementById('TestSQLiteButton');


// Spawn a Python child process
// We need to find the Python script when we are in both
// a production environment and a development environment
// We do that by looking up app.isPackaged (this is a renderer process, so we
// need to do it via remote)
// In development, the script is in the py directory under root
// In production, we package the script in the 'py' directory under the app's
// Contents/Resources by including extraResources under "build" in package.json
function baseDirectoryAdjustment() {
    if (remote.app.isPackaged) {
      return path.join(process.resourcesPath)
    } else {
      return path.join(__dirname, "..")
    }
  }
const baseDirectory = baseDirectoryAdjustment();
const PyScriptPath = path.join(
 baseDirectory, "/py/hello_world_from_python.py"
);

// Bind the TestPythonButton with an "event listener" for a click
//  Open dialog and have user select the write path for the Python script
//  .txt write file
TestPythonButton.addEventListener('click', function (event) {
    // Write where
    let python_write_path = dialog.showOpenDialog({
        properties: ['openDirectory']
    });
    // Spawn a python child process
    let python_child = require('child_process').spawn(
    'python',
    [PyScriptPath, '--write_dir', python_write_path]
    );
});

// Create and access an SQLite database
function createandAccessSQLite(db_dir) {
    let db_file = path.join(db_dir[0], 'hello_world_from_sqlite.db');
    let db = new sqlite3.Database(db_file);
    db.serialize(() => {
        db.run("CREATE TABLE sample_table (\n" +
        "id INTEGER PRIMARY KEY AUTOINCREMENT,\n" +
        "input_value VARCHAR(32)\n" +
        ");")
        .run("INSERT INTO sample_table VALUES (1, 'it worked!')");
    });
    db.close();
  }
// Bind the TestSQLiteButton with an "event listener" for a click
//  Open dialog and have user select the write path for the database
TestSQLiteButton.addEventListener('click', function (event) {
    let db_dir = dialog.showOpenDialog({
        properties: ['openDirectory']
    });
    createandAccessSQLite(db_dir)

});

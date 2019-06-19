'use strict';

import remote from "electron";
import * as path from "path";
import * as child_process from "child_process"

const RunScenarioButton = document.getElementById('RunScenarioButton');


// The script has been packaged in the 'py' directory under the app's
// Contents/Resources by including extraResources under build in package.json
// We need to find it when we are in both the production and environment and
// a development environment
// We do that by looking up app.isPackaged (this is a renderer process, so we
// need to do it via remote)
function directoryAdjustment() {
    if (remote.app.isPackaged) {
      return path.join(process.resourcesPath)
    } else {
      return path.join(__dirname, "..")
    }
  }

const baseDirectory = directoryAdjustment();

const PyScriptPath = path.join(
 baseDirectory, "/py/helloworldfrompython.py"
);


// Bind the RunScenarioButton with an "event listener" for a click
RunScenarioButton.addEventListener('click', function (event) {
  console.log("Hello");
  // Spawn a python child process
  let python_child = child_process.spawn(
    'python',
    [PyScriptPath, '--hello_from_whom', 'Python']
  );
});

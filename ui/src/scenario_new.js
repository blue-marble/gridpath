const {ipcRenderer }= require('electron');

// Request to go back to scenario list
const BacktoScenariosListButton =
    document.getElementById(('BacktoScenariosListButton'));
BacktoScenariosListButton.addEventListener(
    'click', function (event) {
        ipcRenderer.send("Scenario-New-Window-Requests-Back-to-Scenarios");
    }
);

//
// Listen for submission of the new scenario form
document.getElementById('newScenarioDetailForm').addEventListener(
    'submit', (event) => {
        // prevent default refresh functionality of forms (?)
        event.preventDefault();

        // need to get input values here
        const scenarioName = document.getElementById(
            'newScenarioName'
        ).value;
        const loadLevel = document.getElementById(
            'loadId'
        ).value;

        // send new scenario params to main process
        ipcRenderer.send('Save-New-Scenario', [scenarioName, loadLevel])
    });

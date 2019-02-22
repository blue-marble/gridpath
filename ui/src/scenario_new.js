const {ipcRenderer }= require('electron');

// Request to go back to scenario list
const BacktoScenariosListButton =
    document.getElementById(('BacktoScenariosListButton'));
BacktoScenariosListButton.addEventListener(
    'click', function (event) {
        ipcRenderer.send("Scenario-New-Window-Requests-Back-to-Scenarios");
    }
);

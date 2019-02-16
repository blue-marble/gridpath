'use strict';

const { remote } = require('electron');

let scenario_params_dict = {
    "status": "yay",
    "portoflio": "portfolio 1",
    "op chars": "op chars 1",
    "load": "load 1",
    "fuel prices": "fuel prices"

};


// Create the html for a table
let scenarioDetailTable = '<table style="width:100%">';
Object.keys(scenario_params_dict).forEach(function(key) {
    scenarioDetailTable += '<tr>';
    scenarioDetailTable += '<td>' + key + '</td>';
    scenarioDetailTable += '<td>' + scenario_params_dict[key] + '</td>';
    scenarioDetailTable += '</tr>';
});
    scenarioDetailTable += '</table>';

document.getElementById("scenarioDetailTable").innerHTML =
    scenarioDetailTable;

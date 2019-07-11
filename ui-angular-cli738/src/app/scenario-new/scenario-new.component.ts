import { Component, OnInit } from '@angular/core';

import { FormControl, FormGroup } from '@angular/forms';

const io = (<any>window).require('socket.io-client');



@Component({
  selector: 'app-scenario-new',
  templateUrl: './scenario-new.component.html',
  styleUrls: ['./scenario-new.component.css']
})
export class ScenarioNewComponent implements OnInit {

  newScenarioForm = new FormGroup({
    scenarioName: new FormControl(''),
    scenarioDescription: new FormControl(''),
    featureTransmission: new FormControl([''])
  });

  constructor() {

  }

  ngOnInit() {
  }

  saveNewScenario() {
    console.log("In saveNewScenario");
    console.log(this.newScenarioForm.value);

    const socket = io.connect('http://127.0.0.1:8080/');
    socket.on('connect', function() {
        console.log(`Connection established: ${socket.connected}`);
    });
    socket.emit('add_new_scenario', this.newScenarioForm.value);
  }

  getYesNo() {
    return [
      {id: '1', value: 'yes'},
      {id: '2', value: 'no'}
    ]
  }

}

import { Component, OnInit } from '@angular/core';
import { NgForm } from '@angular/forms';

const io = (<any>window).require('socket.io-client');



@Component({
  selector: 'app-scenario-new',
  templateUrl: './scenario-new.component.html',
  styleUrls: ['./scenario-new.component.css']
})
export class ScenarioNewComponent implements OnInit {

  constructor() { }

  ngOnInit() {
  }

  onSubmit(f: NgForm) {
    console.log(f.value);  // { first: '', last: '' }
    console.log(f.valid);  // false

    const socket = io.connect('http://127.0.0.1:8080/');
    socket.on('connect', function() {
        console.log(`Connection established: ${socket.connected}`);
    });
    socket.emit('add_new_scenario', f.value);
  }

}

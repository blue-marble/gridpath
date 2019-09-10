import {Component} from '@angular/core';

const io = (window as any).require('socket.io-client');

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})

export class AppComponent {
  title = 'Welcome to GridPath';
}

// SocketIO connect function to be used by Angular modules
export function socketConnect() {
  const socket = io.connect('http://localhost:8080/');
  socket.on('connect', () => {
    console.log(`Connection established: ${socket.connected}`);
  });
  return socket;
}

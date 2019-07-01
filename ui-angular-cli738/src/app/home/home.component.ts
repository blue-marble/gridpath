import { Component, OnInit } from '@angular/core';
import { HomeService} from "./home.service";

const electron = (<any>window).require('electron');

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class HomeComponent implements OnInit {

  serverStatus: string;

  constructor(private homeService: HomeService) {
  }

  ngOnInit() {
    this.getServerStatus();
    console.log(this.serverStatus)
  }

  getServerStatus(): void {
    console.log("Getting server status...");
    this.homeService.getScenarios()
      .subscribe(
        status => this.serverStatus = status,
        error => {
          console.log('HTTP Error caught', error);
          this.serverStatus = 'down'
        }
      );
  }

  updateServerStatus(event): void {
    console.log('Updating server status...');
    this.getServerStatus();
  }
}

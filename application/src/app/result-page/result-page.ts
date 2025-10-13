import { Component } from '@angular/core';
import { SharedService } from '../shared';
import { JsonPipe } from '@angular/common';
import { Toolbar } from "../components/toolbar/toolbar";
import { MapLayerComponent } from "../components/map-layer/map-layer";
import { InstCardList } from '../components/inst-card-list/inst-card-list';

@Component({
  selector: 'app-result-page',
  imports: [JsonPipe, Toolbar, MapLayerComponent, InstCardList],
  templateUrl: './result-page.html',
  styleUrl: './result-page.css'
})
export class ResultPage {

  dati = [];

  //servizio di condivisione dati
  private sharedService: SharedService;

  constructor(sharedService: SharedService) { this.sharedService = sharedService; }

  //prelevo i dati dal servizio di condivisione
  ngOnInit() {
    //this.dati = this.sharedService.get();
  }

}

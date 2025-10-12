import { Component } from '@angular/core';
import { SharedService } from '../shared';
import { JsonPipe } from '@angular/common';
import { Toolbar } from "../components/toolbar/toolbar";
import { MapLayerComponent } from "../components/map-layer/map-layer";
import { InstCardList } from '../components/inst-card-list/inst-card-list';

@Component({
  selector: 'app-cattura-page',
  imports: [JsonPipe, Toolbar, MapLayerComponent, InstCardList],
  templateUrl: './cattura-page.html',
  styleUrl: './cattura-page.css'
})
export class CatturaPage {

  dati = [];

  //servizio di condivisione dati
  private sharedService: SharedService;

  constructor(sharedService: SharedService) { this.sharedService = sharedService; }

  //prelevo i dati dal servizio di condivisione
  ngOnInit() {
    //this.dati = this.sharedService.get();
  }

}

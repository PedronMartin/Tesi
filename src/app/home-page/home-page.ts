// Update the import path to match the actual location and filename of InstCardList
import { InstCardList } from '../components/inst-card-list/inst-card-list';
import { Toolbar } from '../components/toolbar/toolbar';
import { MapLayerComponent } from '../components/map-layer/map-layer';
import { Component } from '@angular/core';

@Component({
  selector: 'app-home',
  templateUrl: './home-page.html',
  styleUrls: ['./home-page.css'],
  imports: [InstCardList, Toolbar, MapLayerComponent]
})
export class HomePage {}

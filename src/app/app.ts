import { Component, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { MapLayerComponent } from './map-layer/map-layer';
import { Toolbar } from "./toolbar/toolbar";
import { InstCardList } from "./inst-card-list/inst-card-list";

@Component({
  selector: 'app-root',
  imports: [MapLayerComponent, Toolbar, InstCardList], //RouterOutlet, 
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  protected readonly title = signal('greenratingalgorithm');
}

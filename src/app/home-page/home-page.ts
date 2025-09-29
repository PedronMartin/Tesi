import { Toolbar } from '../components/toolbar/toolbar';
import { MapLayerComponent } from '../components/map-layer/map-layer';
import { Component } from '@angular/core';
import { InstructionCard } from "../components/instruction-card/instruction-card";

@Component({
  selector: 'app-home',
  templateUrl: './home-page.html',
  styleUrls: ['./home-page.css'],
  imports: [Toolbar, MapLayerComponent, InstructionCard]
})
export class HomePage {}

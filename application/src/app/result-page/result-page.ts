import { Component, Inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { SharedService } from '../shared';
import { Toolbar } from "../components/toolbar/toolbar";
import { MapResult } from "../components/map-result/map-result";
import { InstructionCard } from '../components/instruction-card/instruction-card';

@Component({
  selector: 'app-result-page',
  imports: [Toolbar, InstructionCard, MapResult],
  templateUrl: './result-page.html',
  styleUrl: './result-page.css'
})
export class ResultPage {

  dati: any = null;
  polygonData: number[][] = [];

  //servizio di condivisione dati
  private sharedService: SharedService;

  constructor(sharedService: SharedService, @Inject(PLATFORM_ID) private platformId: Object){ 
    this.sharedService = sharedService;
  }

  //prelevo i dati dal servizio di condivisione
  ngOnInit() {
    this.dati = this.sharedService.getResponseData();
    this.polygonData = this.sharedService.getPolygonData();
  }
}

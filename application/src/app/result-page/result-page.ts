import { Component, Inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { SharedService } from '../shared';
import { Toolbar } from "../components/toolbar/toolbar";
import { MapLayerComponent } from "../components/map-layer/map-layer";
import { InstructionCard } from '../components/instruction-card/instruction-card';

@Component({
  selector: 'app-result-page',
  imports: [Toolbar, MapLayerComponent, InstructionCard],
  templateUrl: './result-page.html',
  styleUrl: './result-page.css'
})
export class ResultPage {

  private dati: any = null;

  //servizio di condivisione dati
  private sharedService: SharedService;

  constructor(sharedService: SharedService, @Inject(PLATFORM_ID) private platformId: Object){ 
    this.sharedService = sharedService;
  }

  //prelevo i dati dal servizio di condivisione
  ngOnInit() {
    this.dati = this.sharedService.getResponseData();
  }

  ngAfterViewInit() {
    console.log(this.dati);
    if (isPlatformBrowser(this.platformId)) {
      document.getElementById("risultati")!.innerText = JSON.stringify(this.dati);
    }
  }

}

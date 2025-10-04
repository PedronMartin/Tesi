import { Toolbar } from '../components/toolbar/toolbar';
import { MapLayerComponent } from '../components/map-layer/map-layer';
import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { InstructionCard } from "../components/instruction-card/instruction-card";
import { SharedService } from '../shared';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-home',
  templateUrl: './home-page.html',
  styleUrls: ['./home-page.css'],
  imports: [Toolbar, MapLayerComponent, InstructionCard, CommonModule]
})
export class HomePage {

    //sottoscrizione eventlistener per la cattura
    private catturaSub!: Subscription;
    public mostraCattura = false;


    //servizio di condivisione dati
    constructor(private SharedService: SharedService) { }

    ngOnInit() {
      this.catturaSub = this.SharedService.notificaCattura$.subscribe(() => {
        this.onCapture();
      });
    }

    ngOnDestroy() {
      if (this.catturaSub) {
        this.catturaSub.unsubscribe();
      }
    }

    onCapture() {
      this.mostraCattura = true;
      setTimeout(() => {
        const section = document.getElementById("catturaSection");
        if(section)
          section.scrollIntoView({ behavior: "smooth" });
      }, 0);
    }
}

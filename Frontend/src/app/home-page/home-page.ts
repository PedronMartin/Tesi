/*
 * Copyright 2026 [Martin Giuseppe Pedron]
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

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

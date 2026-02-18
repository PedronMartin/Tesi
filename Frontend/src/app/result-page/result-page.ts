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

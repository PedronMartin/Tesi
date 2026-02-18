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

import { Component, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { CommonModule } from '@angular/common';
import { SharedService } from './shared';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, CommonModule],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  protected readonly title = signal('greenratingalgorithm');

  //costruisco lo shared in modo che l'html app veda la variabile isLoading durante le richieste api
  constructor(public shared: SharedService) {}

  ngOnInit() {
    console.log("Developed by Martin Giuseppe Pedron for Thesis in Computer Science, 2026 at University of Verona.");
    console.log("GitHub: https://github.com/PedronMartin/greenRatingAlgorithm");
    console.log("Please, if you find any bug or have any suggestion, don't hesitate to contact me! Personal Mail: pedronmartin64@gmail.com");
  }
}

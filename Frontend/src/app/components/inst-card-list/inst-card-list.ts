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

import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { CommonModule } from '@angular/common';
import { SharedService } from '../../shared';

@Component({
	selector: 'app-inst-card-list',
	imports: [MatIconModule, CommonModule],
	templateUrl: './inst-card-list.html',
	styleUrl: './inst-card-list.css'
})
export class InstCardList {

	//costruttore per il router delle pagine e per il servizio di condivisione dati
	constructor(private router: Router, private SharedService: SharedService) {};

	//array di oggetti che rappresentano le card delle istruzioni
	instructionCards = [
		{
			title: "Cattura",
			longText: "Cattura: una volta che hai individuato la zona che ti interessa analizzare, puoi catturare l'immagine cliccando sul pulsante 'Cattura'.",
			path: "assets/cattura.svg",
			button: "Cattura"
		},
		{
			title: "Calcola",
			longText: "Calcola: una volta catturata la zona di analisi, il calcolo parte in automatico. E' possibile monitorare diverse tipologie di...",
			path: "assets/calcola.svg",
			button: "Calcola"
		},
		{
			title: "Esplora",
			longText: "Esplora: nel menù 'Esplora' puoi visualizzare tutte i diversi risultati delle regole calcolate rispetto ai calcoli effettuati.",
			path: "assets/esplora.svg",
			button: "Esplora"
		},
		{
			title: "Estrai",
			longText: "Estrai: una volta ottenuti i risultati, puoi estrarre le informazioni che ti interessano nel comodo formato GeoJSON.",
			path: "assets/estrai.svg",
			button: "Estrai"
		}
	];
    
    //funzione richiamata al click del pulsante in ciascuna card, gestita tramite l'indice della card
    onCardButtonClick(index: number) {
        if(index == 0) {
			//notifico l'elemento shared per catturare i dati della mappa (per il cambio schermata)
			this.SharedService.triggerCattura();
            this.router.navigate(['/cattura']);
        }
        //TODO: comportamento altri pulsanti da schermata HOME
    }
}


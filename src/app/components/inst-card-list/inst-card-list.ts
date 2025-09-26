import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { InstructionCard } from '../instruction-card/instruction-card';
import { CommonModule } from '@angular/common';

@Component({
	selector: 'app-inst-card-list',
	imports: [MatIconModule, InstructionCard, CommonModule],
	templateUrl: './inst-card-list.html',
	styleUrl: './inst-card-list.css'
})
export class InstCardList {

	constructor(private router: Router) {};

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
            this.router.navigate(['/cattura']);
        }
        //TODO: comportamento altri pulsanti da schermata HOME
    }
}

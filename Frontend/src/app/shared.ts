import {Injectable} from '@angular/core';
import * as S from "./server-contacter";
import {Subject, BehaviorSubject} from 'rxjs';
import { Router } from '@angular/router';

@Injectable({
  providedIn: 'root'
})
export class SharedService {
  /*TODO: vedere come tipizzare meglio in quanto non so come effettivamente passare i dati per caricare la stessa mappa*/
  private CaptureZone: any[] = [];
  private PolygonData: number[][] = [];
  private responseData: any;

  //Subject per notificare la richiesta di cattura (notificaCattura per la prima mappa, catturaPoligono per la seconda)
  public notificaCattura$ = new Subject<void>();
  public catturaPoligono$ = new Subject<void>();

  //gestione caricamento impostato a false
  public isLoading$ = new BehaviorSubject<boolean>(false);

  public onPolygonReady: (() => void) | null = null;
  constructor(
    private serverContact: S.ServerContacter,
    private router: Router
  ) {}

  setCaptureZone(val: any) {
    this.CaptureZone = val;
  }

  getCaptureZone() {
    return this.CaptureZone;
  }

  setPolygonData(val: any [][]) {
    this.PolygonData = val;
  }

  getPolygonData() {
    return this.PolygonData;
  }

  // metodo per notificare la mappa
  triggerCattura() {
    this.notificaCattura$.next();
  }

  //metodo per ricevere i risultati del calcolo dal server
  getResponseData() {
    return this.responseData;
  }

  // metodo per inviare la richiesta di calcolo al server
  serverRequest() {
    this.isLoading$.next(true);
    this.serverContact.runFullAnalysis(this.PolygonData).subscribe(
      response => {
        this.responseData = response;
        this.isLoading$.next(false);
        setTimeout(() => {
          this.router.navigate(['/calcolo']);
        }, 100);
      },
      error => {
        console.error("Errore:", error);
        this.isLoading$.next(false); 
        alert("Si è verificato un errore durante l'analisi: " + error.message);
        /*
        TODO: migliorare gestione degli errori di ritorno dal server
        */
      }
    );
  }

  //metodo per scaricare i risultati del calcolo
  downloadData() {

    //estraggo gli edifici risultato
    let risultati = this.responseData.risultati;

    if (!risultati || risultati.length === 0) {
        alert("Nessun dato da scaricare!");
        return;
    }

    try {
        if (typeof risultati == 'string')
           risultati = JSON.parse(risultati);
    } catch (error) {
        console.error("Errore nel parsing del JSON sporco:", error);
        alert("Attenzione: i dati potrebbero non essere formattati correttamente.");
    }

    //converto i dati in stringa
    const dataStr = JSON.stringify(risultati, null, 2);
    
    //creo un Binary Large Object di tipo json
    const blob = new Blob([dataStr], { type: 'application/json' });
    
    //creo un URL temporaneo per il download
    const url = window.URL.createObjectURL(blob);
    
    //creo un link invisibile, lo apro e lo distruggo
    const a = document.createElement('a');
    a.href = url;
    a.download = 'greenRatingAlgorithm.geojson';
    a.click();
    
    //pulizia dell'URL temporaneo
    window.URL.revokeObjectURL(url);
  }

  /* TODO:
  si potrebbe aggiungere in home page un riquadro sotto la card2 per mostrare l'avanzamento della richiesta al server
  ed eventuali errori generati dalla richiesta. Per esempio, quando richiesto il calcolo bisogna ri-andare a caricare i dati della mappa
  dato che il poligono è modificabile. Inoltre, aggiungere un testo che esplicita il fatto che il calcolo avviene sui dati della seconda mappa e non della prima
  */
}
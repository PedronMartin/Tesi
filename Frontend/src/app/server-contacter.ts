import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { catchError } from 'rxjs/operators';

@Injectable({
  // 'providedIn: root' lo rende un singleton disponibile ovunque
  providedIn: 'root'
})
export class ServerContacter {
  
  //private apiUrl = 'https://greenratingalgorithmprovider.onrender.com/api/greenRatingAlgorithm';
  //private apiUrl = 'http://localhost:5000/api/greenRatingAlgorithm';
  private apiUrl = '/api/greenRatingAlgorithm';
  /*TODO: staccare il nome dell'endpoint in una variabile di ambiente per poterlo cambiare in base alla richiesta*/

  constructor(private http: HttpClient) {}
  /**
   * invia i dati della cattura dell'utente al backend Python per l'analisi.
   * @param polygonData array di coordinate: [[lat1, lon1], [lat2, lon2], ...]
   * @returns Observable con la risposta JSON dal server.
   */
  runFullAnalysis(polygonData: number[][]): Observable<any> {

    //backend si aspetta un oggetto JSON con la chiave 'polygon'
    const payload = {
      polygon: polygonData
      /* TODO: si potrebbe aggiugnere una chiave per il sistema di coordinate così da fissarlo anche in backend
      ed evitare errori di interpretazione delle coordinate */
    };

    console.log("Invio payload al backend:", payload);

    return this.http.post<any>(this.apiUrl, payload);
  }

  /* TODO: aggiungere gestione degli errori con catchError */
}
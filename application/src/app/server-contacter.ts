import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  // 'providedIn: root' lo rende un singleton disponibile ovunque (Dependency Injection)
  providedIn: 'root'
})
export class ServerContacter {
  
  // URL del tuo server live su Render (usiamo HTTPS)
  //private apiUrl = 'https://greenratingalgorithmprovider.onrender.com/api/greenRatingAlgorithm';
  private apiUrl = 'http://localhost:5000/api/greenRatingAlgorithm';
  /*TODO: staccare il nome dell'endpoint in una variabile di ambiente per poterlo cambiare in base alla richiesta*/

  constructor(private http: HttpClient) {}
  /**
   * invia i dati della cattura dell'utente al backend Python per l'analisi.
   * @param polygonData L'array di coordinate: [[lat1, lon1], [lat2, lon2], ...]
   * @returns Un Observable con la risposta JSON dal server.
   */
  runFullAnalysis(polygonData: number[][]): Observable<any> {

    // il backend si aspetta un oggetto JSON con la chiave 'polygon'
    const payload = {
      polygon: polygonData
      /* TODO: si potrebbe aggiugnere una chiave per il sistema di coordinate così da fissarlo anche in backend
      ed evitare errori di interpretazione delle coordinate */
    };

    console.log("Invio payload al backend:", payload);

    return this.http.post<any>(this.apiUrl, payload);
  }
}
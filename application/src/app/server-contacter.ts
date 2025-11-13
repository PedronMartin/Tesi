import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { catchError } from 'rxjs/operators';

@Injectable({
  // 'providedIn: root' lo rende un singleton disponibile ovunque
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

  /* TODO: aggiungere gestione degli errori con catchError */
  /* soluzione possibile:
  runFullAnalysis(polygonData: number[][]): Observable<any> {

    const payload = {
      polygon: polygonData
      // TODO: aggiungere crs?
    };

    console.log("Invio payload al backend:", payload);

    return this.http.post<any>(this.apiUrl, payload).pipe(
      // --- BLOCCO AGGIUNTO ---
      // Usiamo .pipe() per "intercettare" la risposta
      // e passarla a una funzione di gestione errori
      catchError(this.handleError)
      // --- FINE BLOCCO ---
    );
  }


   //* Funzione privata per "tradurre" gli errori HTTP in messaggi
   //* comprensibili per l'utente.
  private handleError(error: HttpErrorResponse) {
    let userMessage = 'Errore sconosciuto. Riprova più tardi.';

    // Guarda lo 'status' dell'errore
    switch (error.status) {
      case 400: // Bad Request
        // Se il backend ci ha dato un messaggio di errore (es. "Poligono non valido"), usalo
        if (error.error && error.error.errore) {
          userMessage = error.error.errore;
        } else {
          userMessage = "Richiesta non valida. Assicurati di aver disegnato un poligono corretto.";
        }
        break;
      
      case 413: // Payload Too Large
        userMessage = "Area di analisi troppo vasta. Seleziona un poligono più piccolo.";
        break;

      case 504: // Gateway Timeout
        userMessage = "Il server (Overpass) è sovraccarico e non ha risposto in tempo. Riprova tra qualche minuto.";
        break;
      
      case 500: // Internal Server Error
        userMessage = "Errore critico del server. (Abbiamo un bug!)";
        break;
      
      case 0: // Errore di Rete o CORS
        userMessage = "Impossibile contattare il server. (È acceso? Il CORS è configurato?)";
        break;
    }
    
    // Logga l'errore reale per noi (sviluppatori)
    console.error("Errore REALE dal backend:", error);

    // Rilancia un *nuovo* errore con il messaggio "pulito"
    // Questo verrà catturato dal componente che ha chiamato la funzione
    return throwError(() => new Error(userMessage));
  }
  }*/
}
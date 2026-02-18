# Green Rating Algorithm
VERSIONE OBSOLETA OTTOBRE 2025 (da modificare)

`GreenRatingAlgorithm` è un'applicazione web full-stack per l'analisi urbanistica e ambientale della regola 3-30-300 sul verde urbano.

Questo repository contiene l'intero progetto, suddiviso in:

1.  **Backend (Flask/GeoPandas):** Un'API REST che riceve coordinate geografiche, interroga dati live da OpenStreetMap ed esegue algoritmi di analisi geospaziale ottimizzati.
2.  **Frontend (Angular/Leaflet):** Un'applicazione web (SPA con SSR) che permette all'utente di disegnare un'area di studio su una mappa, inviarla al backend e visualizzare i risultati dell'analisi (edifici conformi, copertura arborea, ecc.).

# BACKEND

Si tratta di un'API REST monolitica basata su Flask  progettata per analizzare la qualità del verde urbano secondo la regola del "3-30-300".

Il sistema permette di analizzare qualsiasi area del mondo interrogando in tempo reale il database di OpenStreetMap (OSM) tramite Overpass API, senza la necessità di scaricare file statici pesanti.

## Stack Tecnologico

Il backend utilizza librerie Python per l'analisi e la manipolazione di dati geospaziali:

    Flask: Framework per l'API REST.

    Pandas & GeoPandas: Per la manipolazione di DataFrame e dati geografici (poligoni, punti, linee).

    Shapely: Libreria C sottostante per le operazioni geometriche (buffer, intersezioni).

## Funzionalità: Le Regole 3-30-300

Il modulo centrale (analizzatore_centrale.py) orchestra l'esecuzione sequenziale di tre algoritmi principali:
### Regola 3 (Alberi Visibili)

L'obiettivo è stabilire se ogni cittadino può vedere almeno 3 alberi dalla propria abitazione.

    Metodo: Approssimazione 2D basata su un buffer metrico di 45 metri attorno all'edificio.

    Line of Sight: Verifica l'ostruzione visiva tracciando linee tra l'edificio e gli alberi, controllando intersezioni con altri edifici e l'angolo di visuale (+/- 60° rispetto alla normale del lato).

    Output: Aggiunge agli edifici il conteggio degli alberi visibili (visible_trees_count).

### Regola 30 (Copertura Arborea)

Calcola la percentuale di copertura arborea nell'area selezionata dall'utente.

    Metodo: Calcola il rapporto tra l'area stimata delle chiome degli alberi (raggio fisso di 2m per alberi puntiformi) e l'area totale del poligono utente.

    Nota: Esclude le "Aree Verdi Ricreative" (es. parchi) dal calcolo, focalizzandosi sulla copertura arborea pura.

### Regola 300 (Prossimità Aree Verdi)

Verifica se un cittadino vive entro 300 metri da un'area verde accessibile di almeno 1 ettaro.

    Metodo: Genera un buffer di 300 metri (distanza euclidea/linea d'aria) attorno agli edifici ed esegue uno Spatial Join vettorizzato con le aree verdi qualificate.

    Output: Assegna un punteggio binario (score_300): 1 se conforme, 0 altrimenti.

## Architettura e Flusso di Esecuzione

Il sistema è strutturato come un'interazione Client-Server:

    Client (Angular): Invia una richiesta con il poligono dell'area selezionata dall'utente.

    Server (Flask):

        Riceve la richiesta e scarica i dati da OSM (edifici, alberi, aree verdi) tramite 3 query sequenziali.

        Pulisce i dati e proietta tutto nel sistema di riferimento metrico EPSG:32632.

        Esegue gli algoritmi di calcolo.

        Serializza i risultati in GeoJSON e li restituisce al client.

Nota: Sebbene il sistema sia eseguibile tramite Docker, i dettagli specifici di configurazione dei container (Dockerfile, network, porte) non sono inclusi in questa documentazione, che si limita a descrivere l'architettura logica client-server descritta nel PDF.

## Contratto API

Il backend espone un singolo endpoint per l'analisi.

    Endpoint: /api/greenRatingAlgorithm 

    Metodo: POST 

Formato Richiesta (Input)

Il server si aspetta un oggetto JSON contenente la chiave polygon.

    Formato: Array di Array di coordinate [latitudine, longitudine].

    Requisiti: Il poligono deve contenere almeno 4 punti.

Esempio di Payload:
JSON
```
{
  "polygon": [
    [45.464, 9.188],
    [45.462, 9.188],
    [45.462, 9.190],
    [45.464, 9.190],
    [45.464, 9.188]
  ]
}
```

Formato Risposta (Output)

Il server restituisce un oggetto JSON contenente i risultati dell'analisi serializzati in GeoJSON e lo stato dell'esecuzione .

Struttura JSON di risposta:
```

    Esecuzione Positiva: Booleano (True/False).

    messaggio: Stringa con eventuali errori non bloccanti o conferma di successo.

    alberi: Stringa GeoJSON degli alberi analizzati.

    aree_verdi: Stringa GeoJSON delle aree verdi analizzate.

    risultati: Stringa GeoJSON degli edifici con i punteggi calcolati.

```

Error Responses (Esempi):

```
    400 Bad Request: Il poligono di input non è valido (es. ha meno di 4 punti).

    504 Gateway Timeout: Uno dei server di Overpass è sovraccarico e non ha risposto.

    500 Internal Server Error: Errore di calcolo interno (l'errore viene loggato sul server).
```

## 5. Documentazione Tecnica Approfondita

Per un'analisi dettagliata della metodologia, delle ottimizzazioni e delle decisioni architetturali, con gestione degli errori, si rimanda al file DOCUMENTAZIONE.md.

# APPLICAZIONE FRONTEND

This project was generated using [Angular CLI](https://github.com/angular/angular-cli) version 20.2.0.

## Development server

To start a local development server, run:

```bash
ng serve
```

Once the server is running, open your browser and navigate to `http://localhost:4200/`. The application will automatically reload whenever you modify any of the source files.

## Code scaffolding

Angular CLI includes powerful code scaffolding tools. To generate a new component, run:

```bash
ng generate component component-name
```

For a complete list of available schematics (such as `components`, `directives`, or `pipes`), run:

```bash
ng generate --help
```

## Building

To build the project run:

```bash
ng build
```

This will compile your project and store the build artifacts in the `dist/` directory. By default, the production build optimizes your application for performance and speed.

## Running unit tests

To execute unit tests with the [Karma](https://karma-runner.github.io) test runner, use the following command:

```bash
ng test
```

## Running end-to-end tests

For end-to-end (e2e) testing, run:

```bash
ng e2e
```

Angular CLI does not come with an end-to-end testing framework by default. You can choose one that suits your needs.

## Additional Resources

For more information on using the Angular CLI, including detailed command references, visit the [Angular CLI Overview and Command Reference](https://angular.dev/tools/cli) page.

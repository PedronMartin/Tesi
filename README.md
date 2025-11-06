# Green Rating Algorithm

`GreenRatingAlgorithm` è un'applicazione web full-stack per l'analisi urbanistica e ambientale della regola 3-30-300 sul verde urbano.

Questo repository contiene l'intero progetto, suddiviso in:

1.  **Backend (Flask/GeoPandas):** Un'API REST che riceve coordinate geografiche, interroga dati live da OpenStreetMap ed esegue algoritmi di analisi geospaziale ottimizzati.
2.  **Frontend (Angular/Leaflet):** Un'applicazione web (SPA con SSR) che permette all'utente di disegnare un'area di studio su una mappa, inviarla al backend e visualizzare i risultati dell'analisi (edifici conformi, copertura arborea, ecc.).

# Backend

## 1. Descrizione

Questo è il servizio backend per il progetto di tesi e ricerca "GreenRatingAlgorithm".

È un'API REST basata su **Flask** che calcola la regola urbanistica del **3-30-300**. Il servizio riceve un poligono definito dall'utente, interroga i dati live da **OpenStreetMap (OSM)** tramite l'API Overpass, ed esegue un'analisi geospaziale complessa per valutare la conformità dell'area.

## 2. Stack Tecnologico

* **Server API:** Flask
* **Analisi Geospaziale:** GeoPandas, Shapely
* **Manipolazione Dati:** Pandas, NumPy
* **Sorgente Dati:** Overpass API (via `requests`)
* **Conversione Dati:** `osm2geojson`

## 3. Esecuzione Locale

Per eseguire il server in modalità di debug locale:

1.  Assicurarsi di avere un ambiente virtuale Python (es. `python -m venv venv`).
2.  Attivare l'ambiente (es. `source venv/bin/activate`).
3.  Installare le dipendenze:
    ```bash
    pip install -r requirements.txt
    ```
4.  Avviare il server Flask in modalità debug:
    ```bash
    python server.py
    ```

Il server sarà in ascolto su `http://127.0.0.1:5000`.
All'occorrenza, è stato anche eseguito un deploy su Render, contattabile facendo lo switch dell'endpoint del server nell'applicazione angular 
in *server-contacter.ts* dove segue:
```
  //private apiUrl = 'https://greenratingalgorithmprovider.onrender.com/api/greenRatingAlgorithm';
  private apiUrl = 'http://localhost:5000/api/greenRatingAlgorithm';
```

**Nota:** Assicurarsi che `requirements.txt` sia aggiornato. Le dipendenze minime sono: `flask`, `flask-cors`, `geopandas`, `pandas`, `shapely`, `requests`, `osm2geojson`, `numpy`.

## 4. Documentazione API

L'API espone un singolo endpoint per l'analisi completa.

### POST /api/greenRatingAlgorithm

Esegue l'analisi 3-30-300 completa sul poligono fornito.

**Request Body (JSON):**
*L'input deve essere un poligono con almeno 4 punti (per un triangolo valido, dove il primo e l'ultimo punto coincidono).*
```json
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

**Success Response (200 OK):**
*Il server restituisce 4 GeoJSON (serializzati come stringhe) che il frontend può parsare e renderizzare.*
```json
{
  "messaggio": "Analisi completata con successo.",
  "edifici": "<GeoJSON FeatureCollection (Tutti gli edifici nell'area)>",
  "alberi": "<GeoJSON FeatureCollection (Tutta la copertura arborea: alberi, boschi, foreste)>",
  "aree_verdi": "<GeoJSON FeatureCollection (Tutte le aree ricreative: parchi, prati)>",
  "risultati": "<GeoJSON FeatureCollection (Solo gli edifici che soddisfano tutte le regole)>"
}
```

Error Responses (Esempi):

    400 Bad Request: Il poligono di input non è valido (es. ha meno di 4 punti).

    504 Gateway Timeout: Uno dei server di Overpass è sovraccarico e non ha risposto.

    500 Internal Server Error: Errore di calcolo interno (l'errore viene loggato sul server).

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

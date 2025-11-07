# Documentazione Tecnica del Backend - GreenRatingAlgorithm

## 1. Scopo del Documento

Questo documento fornisce una descrizione tecnica approfondita dell'architettura, delle metodologie e delle decisioni implementative del backend del progetto `GreenRatingAlgorithm`.

## 2. Architettura Generale

Il backend è un'**API REST** monolitica basata su **Flask**.

Il flusso logico di una richiesta è il seguente:
1.  Un client (Angular) invia una richiesta `POST /api/greenRatingAlgorithm` con un poligono GeoJSON;
2.  Il server **Flask** riceve la richiesta;
3.  Il server costruisce ed esegue **3 query parallele** all'API **Overpass** per scaricare i dati OSM (Edifici, Copertura Arborea, Aree Verdi);
4.  I dati JSON grezzi vengono convertiti e "spacchettati" in **GeoDataFrame** (GDF) ottimizzati tramite **GeoPandas** e **Pandas**;
5.  I GDF puliti vengono passati al modulo `analizzatore_centrale.py`, che orchestra l'esecuzione dei 3 algoritmi (`regola3`, `regola30`, `regola300`);
6.  Gli algoritmi eseguono calcoli geospaziali (buffer, sjoin, clip, line-of-sight) usando GeoPandas;
7.  I risultati (sia i dati grezzi che quelli filtrati) vengono serializzati in GeoJSON e restituiti al client.

## 3. Analisi dello Stack Tecnologico

### 3.1. Flask
È un "micro-framework" web per Python, molto leggero e minimale. Fornisce gli strumenti base per il routing (gestione degli URL), le richieste e le risposte, lasciando il resto allo sviluppatore.
E' stato usato principalmente per:
    * **Velocità:** è estremamente rapido da avviare e configurare per un'API REST;
    * **Semplicità:** è la scelta ideale per questo progetto. Essendo un micro-framework, ci ha permesso di iniziare rapidamente con un singolo endpoint (/api/greenRatingAlgorithm) senza la complessità iniziale di un framework più complesso e completo come Django. L'architettura Flask è modulare e permette di aggiungere facilmente decine di nuovi endpoint in futuro (es. /api/regola3) man mano che il progetto cresce;
    * **Ecosistema:** Si integra perfettamente con Gunicorn per il deploy in produzione (come su Render).

### 3.2. GeoPandas & Shapely
* **Cos'è?** GeoPandas è "Pandas per i dati geografici". Estende i DataFrame di Pandas per includere una colonna "geometry", permettendo di trattare poligoni, punti e linee come dati. **Shapely** è la libreria C sottostante che *esegue* materialmente le operazioni (es. `buffer`, `intersects`).
* **Perché l'abbiamo usato?**
    * **È il cuore del progetto.** Senza GeoPandas, ogni calcolo (Regola 3, 30, 300) avrebbe richiesto centinaia di righe di complessa matematica geometrica.
    * **Performance:** La maggior parte delle operazioni (es. `.sindex`, `.buffer`, `.intersects`) sono ottimizzate e scritte in **C/C++**. Questo ci ha permesso di ottimizzare la Regola 3.
    * **Vettorizzazione:** Ci ha permesso di evitare lenti cicli `for` in Python, usando operazioni "vettorizzate" come `sjoin` (Regola 300) e `.clip()` (Regola 30).

### 3.3. Overpass API
* **Cos'è?** È un'API di sola lettura che permette di interrogare il database completo (e aggiornato) di OpenStreetMap (OSM) usando un linguaggio di query specifico.
* **Perché l'abbiamo usato?**
    * **Dati Live:** Ci permette di analizzare *qualsiasi* area del mondo senza dover scaricare e gestire enormi file statici (es. Shapefile o GeoPackage).
    * **Flessibilità:** Le query ci permettono di scaricare solo i dati che ci servono (es. `natural=tree` o `landuse=forest`), riducendo il carico sul server.

---

## 4. Metodologia e Ottimizzazioni degli Algoritmi

Questa sezione descrive le decisioni ingegneristiche prese per rendere gli algoritmi stabili e performanti.

### 4.1. Regola 3 (Visibilità) - Ottimizzazione Critica
* **Problema:** Un'implementazione "ingenua" (brute-force) dell'algoritmo di linea di vista (un ciclo `for` sugli edifici, un ciclo `for` sugli alberi, e un controllo `.intersects` su tutti gli ostacoli) ha una complessità $O(N^3)$. Su un set di dati di 2000 edifici, questo porterebbe a un timeout di minuti o ore.
* **Soluzione (Ottimizzazione):** L'algoritmo è stato riscritto per usare **indici spaziali (R-tree)**, forniti da GeoPandas (`.sindex`).
    1.  `alberi_idx` e `ostacoli_idx` vengono costruiti *una sola volta* all'inizio ($O(N \log N)$).
    2.  Per ogni edificio, si esegue una **query a due stadi**:
        * **Fase 1 (Veloce):** Si usa l'indice (`alberi_idx.intersection(buffer.bounds)`) per trovare una lista approssimativa di "candidati". Questa operazione è logaritmica ($O(\log M)$).
        * **Fase 2 (Precisa):** Si esegue il costoso calcolo geometrico `.within()` *solo* sul piccolo sottoinsieme di candidati.
    3.  La stessa logica a due stadi viene usata in `is_unobstructed` per controllare gli ostacoli.
    4.  **Risultato:** La complessità totale è stata ridotta drasticamente (vicino a $O(N \log N)$), permettendo analisi in pochi secondi.

### 4.2. Regola 30 (Copertura) - Correttezza Logica
* **Problema:** Un calcolo ingenuo (`Area Alberi / Area Edifici+Alberi`) produce risultati >100% (denominatore troppo piccolo, numeratore gonfiato).
* **Soluzione (Logica):**
    * **Denominatore:** È l'area totale del **poligono di input** dell'utente (proiettato in `EPSG:32632`).
    * **Numeratore (Metodo Ibrido):** Per gestire i dati misti della Query 1, l'algoritmo separa Punti e Poligoni:
        * **Poligoni** (`forest`, `wood`): Viene usata la loro area reale, ritagliata (`gpd.clip`) ai confini dell'area di studio (per evitare di contare 100 ettari di un bosco che tocca solo 1 metro del poligono).
        * **Punti** (`tree`): Viene usata un'area simulata (es. $\pi \cdot r^2$) solo per i punti il cui centroide è *dentro* (`within`) l'area di studio.

### 4.3. Regola 300 (Accesso) - Vettorizzazione
* **Soluzione (Logica):** L'algoritmo è completamente vettorizzato (non ha `for` loop) e si basa su `gpd.sjoin` (Spatial Join), l'operazione più efficiente per questo tipo di analisi ("quali di A intersecano B?").
* **Gestione "Edge Effect":** La query Overpass (Tipo 2) per le aree verdi usa un poligono "gonfiato" (bufferizzato di 300m) per includere parchi rilevanti appena fuori dal confine dell'area di studio.

---

## 5. Decisioni Critiche di Stabilità (Gestione Dati "Sporchi")

### 5.1. Il Crash `unpack_gdf_features`
* **Problema:** Le nuove query Overpass (Tipo 1) restituiscono un mix di elementi (`tree`, `forest`, `wood`) con set di tag non omogenei. La libreria `gpd.GeoDataFrame.from_features` "si arrende" e smette di spacchettare magicamente i tag, creando invece un'unica colonna `tags` che contiene un mix di dizionari Python (`{...}`) e valori `None`.
* **Crash:** Le funzioni di Pandas (`pd.json_normalize` o `apply(pd.Series)`) subiscono un **"hard crash"** (a livello C, senza traceback Python) quando tentano di processare questa colonna "sporca", specialmente quando i dizionari `tags` contengono chiavi duplicate (`id`, `type`) che sono già colonne nel GeoDataFrame principale.
* **Soluzione (Funzione `unpack_gdf_features`):** È stata scritta una funzione di "spacchettamento" robusta che:
    1.  Sostituisce tutti i `None` nella colonna `tags` con dizionari vuoti (`fillna({})`).
    2.  Usa `apply(pd.Series)` per convertire i dizionari in un nuovo DataFrame.
    3.  **Cruciale:** Rimuove le colonne duplicate (es. `type`, `id`) dal nuovo DataFrame dei tag *prima* di eseguire il `.join()`, prevenendo il crash.

---

## 6. Punti Aperti (Discussione Metodologica)

Questa sezione elenca le 4 approssimazioni metodologiche chiave da discutere e validare con il team di ricerca.

1.  **[Regola 300] Soglia Area:** La letteratura (OMS, UniFi) indica una soglia di **0.5-1 ettaro** per un'area verde "significativa". Si propone di adottare **1 ettaro**. È corretto per questo studio?
2.  **[Regola 3] Buffer Visuale:** Il buffer di **100 metri** per la "vista" è un'approssimazione valida per un contesto urbano?
3.  **[Regola 30] Definizione "Arborea":** La "Copertura Arborea" (Regola 30) deve essere "pura" (solo alberi/boschi, Query 1) o deve includere anche le "Aree Verdi Ricreative" (parchi/prati, Query 2)? (L'implementazione attuale è "pura").
4.  **[Regola 30] Raggio Alberi:** Quale raggio simulato (in metri) dovremmo usare per gli alberi puntiformi (`natural=tree`)? (L'implementazione attuale usa `2 metri`, ma `5 metri` potrebbe essere più realistico).

---

## 7. Sviluppi Futuri Proposti

* **Refactoring del Modello Dati per Analisi Dettagliata:**
    Attualmente, il backend restituisce i dati grezzi e un GDF separato (`risultati`) con i soli edifici "conformi". Un'evoluzione chiave sarà modificare `analizzatore_centrale.py` affinché restituisca un **unico GeoDataFrame `edifici` arricchito**, contenente i punteggi parziali (`visible_trees_count`, `score_300`, `coverage_percentage`) per *ogni* edificio, non solo per i vincitori. Questo permetterà al frontend di visualizzare mappe "heatmap" e pop-up dettagliati anche per gli edifici non conformi, spiegando *perché* hanno fallito il test.

* **Elaborazione Asincrona (Scalabilità):**
    Per aree di studio molto grandi (che superano i 300 secondi di timeout), un'evoluzione futura del backend dovrebbe spostare l'analisi da un processo sincrono (HTTP) a uno **asincrono**, utilizzando una coda di messaggi (es. Redis) e un "worker" separato (es. Celery).
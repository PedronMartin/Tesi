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

## 3. Strumenti e librerie

### 3.1. Flask
È un "micro-framework" web per Python, molto leggero e minimale. Fornisce gli strumenti base per il routing (gestione degli URL), le richieste e le risposte, lasciando il resto allo sviluppatore.
E' stato usato principalmente per:
    * **Velocità:** è estremamente rapido da avviare e configurare per un'API REST (stateless);
    * **Semplicità:** è la scelta ideale per questo progetto. Essendo un micro-framework, mi ha permesso di iniziare rapidamente con un singolo endpoint (/api/greenRatingAlgorithm) senza la complessità iniziale di un framework più complesso e completo come Django. L'architettura Flask è modulare e permette di aggiungere facilmente decine di nuovi endpoint in futuro (es. /api/regola3) man mano che il progetto cresce;
    * **Ecosistema:** si integra perfettamente con Gunicorn per il deploy in produzione (come su Render).

### 3.2. GeoPandas & Shapely
**Pandas** è una libreria Python per l'analisi e la manipolazione dei dati. Il suo componente principale è il DataFrame, ossia una tabella in-memoria che permette di caricare, pulire, filtrare, aggregare e unire set di dati complessi in modo incredibilmente efficiente. **GeoPandas** è Pandas per i dati geografici. Estende i DataFrame di Pandas per includere una colonna "geometry", permettendo di trattare poligoni, punti e linee come dati. **Shapely** invece è la libreria C sottostante che esegue materialmente le operazioni (es. `buffer`, `intersects`) sui dati contenuti nella colonna geomety di un GDF.

Senza, ogni calcolo (Regola 3, 30, 300) avrebbe richiesto centinaia di righe di complessa matematica geometrica. La maggior parte delle operazioni (es. `.sindex`, `.buffer`, `.intersects`) sono ottimizzate e scritte in **C/C++**.

### 3.3. Overpass API
Overpass API è un'API di sola lettura che permette di interrogare il database completo (e aggiornato) di OpenStreetMap (OSM) usando un linguaggio di query specifico. Ci permette di analizzare qualsiasi area del mondo senza dover scaricare e gestire enormi file statici (es. Shapefile o GeoPackage). Le query inoltre ci permettono di scaricare solo i dati che ci servono (es. `natural=tree` o `landuse=forest`), riducendo il carico sul server.

---

## 4. Regole 3-30-300

Questa sezione descrive le regole 3-30-300, cuore dell'algoritmo e veri esecutori del calcolo. Viene spiegato il flusso di lavoro dei vari algoitmi, dati di input e di output, costi e ottimizzazioni.

### 4.1 Regola 3 (Regola3.py)

#### 4.1.1. Concetto e Obiettivo
L'obiettivo di questo algoritmo è implementare la "Regola 3", che stabilisce che ogni cittadino dovrebbe poter vedere almeno 3 alberi dalla propria abitazione. Data la natura dei dati OSM (2D, senza altezze), l'algoritmo implementa un'**approssimazione 2D** di questa regola. Calcola, per ogni edificio, il numero di "coperture arboree" (alberi singoli, boschi, foreste) che sono visibili da esso senza essere ostruiti da altri edifici.

#### 4.1.2. Contratto della Funzione (`run_rule_3` ---> Regola3.py)

* **Input:**
    1.  `edifici (GeoDataFrame)`: il GDF di tutti gli edifici nell'area di studio;
    2.  `alberi (GeoDataFrame)`: il GDF di tutta la "copertura arborea" (`tree`, `wood`, `forest`).
* **Output:**
    * `edifici_conformi (GeoDataFrame)`: Una copia del GDF `edifici` originale, ma con una nuova colonna aggiunta: `visible_trees_count (int)`, che contiene il numero di alberi/boschi visibili.

#### 4.1.3. Flusso di Implementazione

L'algoritmo evita un approccio "brute-force" (che sarebbe troppo lento) e utilizza indici spaziali per ottimizzare le ricerche.

1.  **Proiezione:** tutti i GDF in input (edifici, alberi) vengono proiettati in un CRS metrico (es. `EPSG:32632`) per permettere calcoli in metri;
2.  **Filtro Dati:** i GDF vengono puliti per rimuovere geometrie non valide. Il GDF `alberi` viene filtrato per assicurare che contenga solo i tag rilevanti (es. `natural='tree'`, `landuse='forest'`, ecc.), gestendo i dati "sporchi" (spazi, maiuscole);
3.  **Costruzione Indici (L'Ottimizzazione):** Vengono creati due **indici spaziali (R-tree)** *una sola volta* all'inizio:
    * `ostacoli_idx = edifici_proj.sindex`
    * `alberi_idx = alberi_proj.sindex`
4.  **Ciclo Principale (per Edificio):** l'algoritmo itera su ogni edificio. Per ciascuno:
    a. **Buffer di Visuale:** crea un buffer metrico (es. 50 metri) per definire l'area di ricerca;
    b. **Ricerca Alberi (Query a 2 Stadi):** per trovare gli alberi nel buffer:
        i.  **Fase 1 (Veloce/Approssimativa):** usa `alberi_idx.intersection(buffer.bounds)` per ottenere una lista ridotta di "candidati";
        ii. **Fase 2 (Precisa):** esegue il costoso calcolo geometrico `.within()` *solo* sul piccolo sottoinsieme di candidati;
    c. **Controllo Ostruzione:** per ogni albero trovato, chiama la funzione `is_unobstructed(albero, edificio, ostacoli_idx)`.
5.  **Funzione `is_unobstructed` (Controllo Linea di Vista):**
    a. **Linea di Vista:** traccia una `LineString` (una linea) 2D tra il centroide dell'albero (`tree.geometry.centroid`) e il punto più vicino sul perimetro dell'edificio. Tramite `building.geometry.exterior.project(tree.geometry)` viene "proiettata" la geometria dell'albero sulla linea del perimetro dell'edificio, trovando il punto su quel perimetro che è geometricamente più vicino all'albero.
    b. **Ricerca Ostacoli (Query a 2 Stadi):**
        i.  **Fase 1 (Veloce):** usa `ostacoli_idx.intersection(linea_di_vista.bounds)` per trovare i "probabili" ostacoli (spesso 0 o 1).
        ii. **Fase 2 (Precisa):** esegue il costoso `.intersects()` *solo* su quei pochissimi candidati (dopo aver rimosso l'edificio di partenza dalla lista);
    c. se la linea non interseca nessun ostacolo, l'albero è visibile.
6.  **Aggregazione:** Il conteggio finale (`visible_trees_count`) viene salvato nel GDF dei risultati.

#### 4.1.4. Ottimizzazione Critica

* **Problema:** Un'implementazione "ingenua" (brute-force) di questo algoritmo (tre cicli `for` annidati: per edificio -> per albero -> per ostacolo) ha una complessità temporale di circa O(N^3) nel caso peggiore, ossia con un numero di alberi ed edifici uguali. Su un'area con >2000 edifici, questo richiederebbe miliardi di controlli e un tempo di esecuzione di parecchi minuti, se non ore;
* **Soluzione:** l'uso degli **indici spaziali (`.sindex`)** è l'ottimizzazione chiave. Un indice R-tree permette di trovare quali geometrie intersecano un'area in tempo logaritmico (O(log N)) invece che lineare (O(N)).
* **Risultato:** sostituendo i cicli interni con query sull'indice, la complessità totale dell'algoritmo scende drasticamente a circa O(NlogN), permettendo di eseguire l'analisi in pochi secondi.

#### 4.1.5. Limiti Noti e Compromessi Metodologici

* **Approssimazione 2D:** l'algoritmo è puramente 2D. Non tiene conto dell'altitudine (DEM) né dell'altezza di edifici e alberi (dati 3D non disponibili in OSM);
* **Approssimazione "Pessimista" (Linea Singola):** Per motivi di performance, la visibilità è calcolata usando una *singola linea* (dal centroide dell'albero al punto più vicino dell'edificio). In scenari urbani densi, questo può portare a falsi negativi: un albero può essere marcato come "non visibile" se la sua singola linea di test "sfiora" l'angolo di un edificio adiacente, anche se il resto della facciata ha una vista libera. In altri casi, possono capitare invece dei falsi positivi, nel caso in cui un albero è 'visibile' per l'algoritmo in quanto è effettivamente possibile costruire una linea da un punto dell'edificio all'albero, ma senza tener conto dell'angolazione con cui questo succede; per esempio, un albero potrebbe essere considerato 'valido' ai fini del calcolo di un edificio se è possibile tracciare una linea dritta tra i due elementi in un singolo angolino (vertice) dell'edificio (cosa che realisticamente non sarebbe possibile).

### 4.2 Regola 30 (Regola30.py)

#### 4.2.1. Concetto e Obiettivo

L'obiettivo di questo algoritmo è implementare la "Regola 30", che stabilisce che almeno il 30% di un'area urbana dovrebbe essere coperta da chioma arborea.

L'algoritmo calcola questa percentuale per l'intera area di studio definita dall'utente. Il risultato è un **singolo valore percentuale** (es. 2.86%) che viene poi assegnato a tutti gli edifici all'interno di quell'area per determinarne la conformità.

#### 4.2.2. Contratto della Funzione (`run_rule_30` ---> Regola30.py)

* **Input:**
    1.  `edifici (GeoDataFrame)`: GDF di tutti gli edifici *(attualmente non utilizzato nel calcolo, ma passato per coerenza architetturale)*;
    2.  `alberi (GeoDataFrame)`: GDF di tutta la "copertura arborea" (Query 1: `tree`, `wood`, `forest`);
    3.  `polygon_gdf (GeoDataFrame)`: il GDF che rappresenta il poligono di studio disegnato dall'utente.
* **Output:**
    * `percentage (float)`: un singolo valore numerico che rappresenta la percentuale di copertura.

#### 4.2.3. Flusso di Implementazione

L'algoritmo è stato progettato per risolvere le falle logiche di un'implementazione "ingenua" iniziale (che portava a risultati >100%).

1.  **Proiezione:** tutti i GDF rilevanti (`alberi`, `polygon_gdf`) vengono proiettati in un CRS metrico (es. `EPSG:32632`) per calcolare le aree in metri quadrati;
2.  **Calcolo Denominatore (Area di Studio):** l'area totale è il denominatore della nostra frazione. Viene calcolata in modo robusto prendendo l'area geometrica del poligono di input: `study_area = polygon_proj.geometry.area.sum()`;
3.  **Calcolo Numeratore (Area Arborea):** per calcolare il numeratore, viene chiamata la funzione ausiliaria `calculate_trees_area`. Questa funzione implementa una logica ibrida per gestire i dati misti (punti e poligoni) provenienti dalla Query degli alberi:
    a. **Gestione Poligoni (Boschi, Foreste):** per evitare risultati assurdi (es. 10.000% se un'area piccola tocca un bosco enorme), i poligoni della copertura arborea vengono "tagliati" (`gpd.clip`) sui confini dell'area di studio. Viene sommata solo l'area della porzione *interna* al poligono;
    b. **Gestione Punti (Alberi singoli):** per gli alberi singoli (geometrie `Point`), l'algoritmo usa una logica diversa:
        i.  seleziona solo i punti il cui centroide è *dentro* l'area di studio (`alberi_points.geometry.within(area.unary_union)`);
        ii. per ogni punto trovato, somma un'area simulata fissa (basata sulla costante `TREE_RADIUS`).
    c. **Risultato:** Il numeratore (`trees_total_area`) è la somma di `area_from_polygons + area_from_points`.
4.  **Calcolo Percentuale:** L'algoritmo esegue la divisione (`(trees_total_area / study_area) * 100`) e si assicura che il risultato non possa superare il 100%.

#### 4.2.4. Correttezza Logica (Il Bug del 101%)

* **Problema:** Un'implementazione "ingenua" soffriva di due falle logiche che la rendevano inutile:
    1.  **Denominatore Sbagliato:** L'area di studio era calcolata come `unary_union(edifici, alberi)`, risultando in un'area minuscola che ignorava strade, piazze e tetti.
    2.  **Numeratore Sbagliato:** Veniva applicato un `buffer()` a *tutte* le geometrie, inclusi i poligoni delle foreste, "gonfiando" artificialmente l'area arborea.
* **Risultato:** La combinazione di un numeratore gonfiato e un denominatore ridotto portava a percentuali assurde (es. `101.35%`);
* **Soluzione (Metodo Ibrido):** L'algoritmo è stato riscritto per usare il **poligono di input** come denominatore (risolvendo il problema 1) e per implementare la **logica Punti vs. Poligoni** (risolvendo il problema 2).

#### 4.2.5. Limiti Noti e Compromessi Metodologici

* **Approssimazione del Raggio (`TREE_RADIUS`):** l'uso di un raggio fisso (es. `2 metri`) per gli alberi puntiformi è un'approssimazione significativa. Questo valore è un numbero ambiguo e andrebbe validato o sostituito con una stima scientifica (es. raggio medio della chioma per alberi urbani comuni) per migliorare l'accuratezza del calcolo;
* **Interpretazione dei Dati OSM (Punto Chiave):** l'algoritmo adotta un'interpretazione "pura" di "copertura arborea", usando solo la Query 1 (`tree`, `forest`, `wood`). Esclude deliberatamente le "Aree Verdi Ricreative" (Query 2: `leisure=park`, `landuse=grass`) dal calcolo. Questa è una scelta metodologica che impatta direttamente e significativamente il risultato finale (spiegando perché è spesso <10%).

### 4.3 Regola 300 (Regola300.py)

#### 4.3.1. Concetto e Obiettivo

L'obiettivo di questo algoritmo è implementare la "Regola 300", che stabilisce che ogni cittadino dovrebbe vivere entro 300 metri da un'area verde accessibile.

L'algoritmo calcola, per ogni singolo edificio, se questa regola è soddisfatta (punteggio 1) o meno (punteggio 0), controllando la vicinanza con le "Aree Verdi Ricreative" (parchi, prati, giardini).

#### 4.3.2. Contratto della Funzione (`run_rule_300` ---> Regola300.py)

* **Input:**
    1.  `edifici (GeoDataFrame)`: il GDF di tutti gli edifici nell'area di studio;
    2.  `aree_verdi (GeoDataFrame)`: il GDF di tutte le "aree verdi ricreative" (Query 2: `park`, `grass`, `garden`).
* **Output:**
    * `risultato_finale (GeoDataFrame)`: una copia del GDF `edifici` originale, ma con una nuova colonna aggiunta: `score_300 (int)`, che contiene `1` se l'edificio è conforme, `0` altrimenti.

#### 4.3.3. Flusso di Implementazione

Questo algoritmo è il più efficiente del set, poiché è **completamente vettorizzato** e non usa cicli `for` in Python.

1.  **Proiezione:** tutti i GDF in input vengono proiettati in un CRS metrico (es. `EPSG:32632`) per permettere il calcolo del buffer in metri;
2.  **Filtro Dati (per ora assente):** *(Questa è una sezione in attesa di approvazione)*. L'algoritmo è predisposto per filtrare le `aree_verdi` e tenere solo quelle "significative", scartando i poligoni con un'area inferiore a una soglia definita (es. 10.000 mq / 1 ettaro);
3.  **Creazione Buffer:** l'algoritmo crea un buffer metrico di 300 metri attorno *a tutti gli edifici* in un'unica operazione vettorizzata: `edifici_buffer['geometry'] = edifici_proj.geometry.buffer(300)`;
4.  **Spatial Join:** l'algoritmo esegue un **`gpd.sjoin` (Spatial Join)** tra i buffer degli edifici e i poligoni delle aree verdi. `sjoin` è un'operazione GIS ad alte prestazioni (basata su indici R-tree) che restituisce un nuovo GeoDataFrame contenente solo gli edifici il cui buffer di 300m *interseca* almeno un'area verde.
5.  **Aggregazione:** l'algoritmo estrae gli indici unici (`.unique()`) degli edifici "vincitori" dallo `sjoin` e li usa per mappare i punteggi `1` (conformi) sul GDF `edifici` originale. Agli edifici non presenti nel risultato dello `sjoin` rimane il punteggio di default `0`.

#### 4.3.4. Ottimizzazione Critica (Vettorizzazione vs. Loop)

* **Problema:** un'implementazione "ingenua" (un ciclo `for` su ogni edificio, che a sua volta fa un ciclo `for` su ogni area verde per controllare l'intersezione) avrebbe una complessità molto alta e sarebbe lenta;
* **Soluzione (Vettorizzazione):** l'uso di **`gpd.sjoin`** sostituisce entrambi i cicli. L'operazione è interamente eseguita a livello C (tramite Shapely e indici R-tree) con una complessità logaritmica (circa O(N/logM)), risultando quasi istantanea.

#### 4.3.5. Limiti Noti e Compromessi Metodologici

* **Approssimazione 2D (Linea d'Aria vs. Percorso):** questo è il compromesso più importante. L'algoritmo calcola la distanza in **linea d'aria** (buffer di 300m). Non calcola il **percorso pedonale** reale (che richiederebbe un'analisi di rete su grafo stradale, es. con OSMnx, ed è computazionalmente *molto* più costoso). È un'approssimazione standard per la pianificazione urbana, ma la distanza reale da percorrere a piedi sarà quasi sempre superiore a quella calcolata. Una soluzione, quantomeno visiva, è utilizzare Leaflet per la visualizzazione del percorso reale che collega edificio ad area verde, in modo da avere, a costo minimo, anche la distanza reale da dover percorere;
* **Gestione "Edge Effect" (Risolto):** per evitare che un edificio sul bordo dell'area di studio "perda" un parco vicino che è appena fuori dal poligono disegnato, la query Overpass (Query 2) in `server.py` viene eseguita su un poligono di ricerca "gonfiato" di 300 metri;
* **Soglia Area Verde (Punto Aperto):** l'efficacia della regola dipende dalla soglia usata per definire un'area verde "significativa" (il punto metodologico 1 da discutere). Ci sono infatti elementi contrassegnati come 'aree verdi' che sono piccole aiuole pubbliche, che probabilmente andrebbero scartate.

















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
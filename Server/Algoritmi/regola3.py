"""
    Algoritmo per il calcolo della regola 3:
        il programma itera su ogni edificio passato come argomento, e gli alberi contenuti in un buffer che simula una distanza fattibile di visuale di una persona.
        Ogni albero ottenuto viene iterato a sua volta per l'edificio, controllando che esista un percorso 'visivo' tra i due elementi;
        viene quindi tracciato un segmento tra i due, e controllato se qualche altro oggetto (al momento gli altri edifici e basta) ostacolano la visuale.

        MANCA:
            1- decidere che elementi andare a prelevare da OSM per il controllo degli ostacoli;

        SOLUZIONI:
            1- il controllo dell'altitudine sarebbe un'operazione estremamente complessa da implementare. 
                Richiederebbe un sistema DEM (Digital Elevation Model) per il terreno, l'altezza di ogni edificio
                e l'altezza di ogni albero (quasi mai presente in OSM); gli ultimi due si potrebbero simulare con un'altezza media,
                ma l'algoritmo perderebbe di precisione;
            2-  buffer è impostato a 30 metri, con base scientifica (letteratura Asti);
            3-  per il momento usiamo solo gli altri edifici. CHIEDERE A PROFESSORE se aggiungere altro come mura o altro,
                al costo però di rallentare molto l'algoritmo generale in quanto richiederebbe una richiesta OVERPASS in più e almeno 
                un *logx in più in questo algoritmo.
"""

#importazioni
from shapely.geometry import LineString
import pandas as pd
import logging
import geopandas as gpd
import numpy as np

#costante di buffer di visuale in metri
view_buffer = 30

#costante di debuffing per gli edifici attaccati o contigui
DEBUFFER_METRI = -0.5

#costante di angolo massimo per il filtro angolare della vista
MAX_ANGLE_DEG = 45

"""
    Funzione che calcola il numero di alberi visibili da ogni edificio
"""
def run_rule_3(edifici, alberi):

    #avvio logger regola
    logger = logging.getLogger("regola3")

    #controllo input
    if edifici.empty or alberi.empty:
        logger.warning("Dati insufficienti per il calcolo. Assicurati che i GeoDataFrame non siano vuoti.")
        return edifici.assign(visible_trees_count=0)

    #blocco di correzzione e validazione input
    try:
        #proiezione edifici e gli alberi nel sistema di coordinate corretto
        if edifici.crs is None:
            edifici.set_crs("EPSG:4326", inplace=True)
        if alberi.crs is None:
            alberi.set_crs("EPSG:4326", inplace=True)

        #elimino edifici non validi (no tag building), e converto in sistema metrico
        if 'building' in edifici.columns:
            edifici_proj = edifici[edifici['building'].notna()].to_crs("EPSG:32632")
        else:
            edifici_proj = edifici.to_crs("EPSG:32632")

        #converto in sistema metrico
        alberi_proj = alberi.to_crs("EPSG:32632")

        #definisco i tag che consideriamo "copertura arborea"
        tree_tags = ['tree', 'tree_row']
        forest_tags = ['forest', 'wood']

        #creo delle maschere "vuote" (tutto Falso) come base, tenendo traccia dell'indice originale
        mask_natural = pd.Series([False] * len(alberi_proj), index=alberi_proj.index)
        mask_landuse = pd.Series([False] * len(alberi_proj), index=alberi_proj.index)
        
        #se la colonna 'natural' esiste, calcolo la sua maschera
        if 'natural' in alberi_proj.columns:
            #pulizia e formattazione: evita NaN, forza conversione in stringa, rimuove spazi e rende minuscolo tutto
            natural_col = alberi_proj['natural'].fillna('').astype(str).str.lower().str.strip()
            mask_natural = (
                natural_col.isin(tree_tags) |
                natural_col.isin(forest_tags)
            )

        #se la colonna 'landuse' esiste, calcolo la sua maschera
        if 'landuse' in alberi_proj.columns:
            #pulizia e formattazione: evita NaN, forza conversione in stringa, rimuove spazi e rende minuscolo tutto
            landuse_col = alberi_proj['landuse'].fillna('').astype(str).str.lower().str.strip()
            mask_landuse = landuse_col.isin(forest_tags)

        """
        La maschera finale è l'unione (OR) delle due maschere
        Se una colonna non esiste, la sua maschera è rimasta "False" e non contribuisce
        """
        mask = mask_natural | mask_landuse

        #applico la maschera
        alberi_proj_filtrati = alberi_proj[mask]

        #pulisci geometrie non valide (spostato dopo il filtro)
        edifici_proj = edifici_proj[edifici_proj.geometry.is_valid & ~edifici_proj.geometry.is_empty]
        alberi_proj = alberi_proj_filtrati[alberi_proj_filtrati.geometry.is_valid & ~alberi_proj_filtrati.geometry.is_empty]
        
        #controllo finale su eventuali GeoDataFrame vuoti degli edifici, gli alberi invece possono non esserci
        if edifici_proj.empty:
             logger.warning("Nessuna geometria valida trovata dopo la proiezione/filtro.")
             return edifici.assign(visible_trees_count=0)

    except Exception as e:
        logger.error(f"Errore nella proiezione dei dati: {e}")
        return edifici.assign(visible_trees_count=0)

    #eseguo una copia per i risultati e inizializzo il punteggio a 0 per tutti
    risultato_edifici = edifici_proj.copy()
    risultato_edifici['visible_trees_count'] = 0

    logger.info("Avvio del calcolo della linea di vista...")

    """
    Come per la regola 300 anche qui uso gli indici spaziali di geopandas
    per velocizzare le ricerche. Questa operazione ottimizza molto il calcolo,
    specialmente con dataset di grandi dimensioni; ci permette di passare da 
    O(n*m*n) a O(n*m*log(n)) complessità approssimativa, dove n è il numero di edifici
    e m il numero di alberi.
    """
    alberi_idx = alberi_proj.sindex
    ostacoli_idx = edifici_proj.sindex

    #itero su ogni edificio
    for idx, edificio in risultato_edifici.iterrows():

        #buffer di 30 metri attorno all'edificio
        buffer = edificio.geometry.buffer(view_buffer)
        
        """
        Uso l'indice per trovare gli alberi candidati all'interno del buffer
        questa operazione è approssimativa e fornisce più risultati di quelli reali
        ci serve in particolare per ridurre i candidati per il prossimo controllo
        """
        possible_indices = list(alberi_idx.intersection(buffer.bounds))

        #creo una sottolista con solo quei candidati
        trees_candidates = alberi_proj.iloc[possible_indices]

        """
        Eseguo il filtro preciso geospaziale solo sugli alberi candidati
        la funzione within è più precisa e lenta, ma ora lavora su un sottoinsieme ridotto
        è onerosa perchè calcola la geometria esatta e non solo i bounds
        """
        selected_trees = trees_candidates[trees_candidates.geometry.within(buffer)]

        #itero sugli alberi vicini richiamando la funzione apposita per la vista
        visible_trees = 0
        for _, albero in selected_trees.iterrows():
            if is_unobstructed(albero, edificio, edifici_proj, ostacoli_idx):
                visible_trees += 1
                
        #aggiorno il conteggio per l'edificio corrente rimappando nella lista originale
        risultato_edifici.loc[idx, 'visible_trees_count'] = visible_trees

    #creo un GDF finale e copio i risultati (indice e numero alberi visibili)
    final_result_df = pd.DataFrame(index=edifici.index)
    final_result_df['visible_trees_count'] = 0
    final_result_df.loc[risultato_edifici.index, 'visible_trees_count'] = risultato_edifici['visible_trees_count']
    
    #restituisce il risultato come GeoDataFrame
    final_result_gdf = edifici.copy()
    final_result_gdf = final_result_gdf.merge(final_result_df, left_index=True, right_index=True)
    return final_result_gdf

#Esempio di utilizzo singolo dell'algoritmo
"""edifici = gpd.read_file("./Edifici.geojson")
alberi = gpd.read_file("./Alberi.geojson")
print(run_rule_3(edifici, alberi))"""

"""
    Funzione che verifica se la linea di vista da un albero a un edificio è bloccata
"""
def is_unobstructed(tree, building, all_buildings_gdf, obstacles_idx):

    # trovo i punti target (i punti intermedi di ogni lato)
    try:
        target_points = []
        
        # estraggo le coordinate dei vertici dell'edificio
        vertici = building.geometry.exterior.coords
        
        # prendo il centroide dell'albero (serve subito per il calcolo dell'angolo)
        tree_centroid = tree.geometry.centroid

        """
        Itero su ogni lato del perimetro e compongo le linee che rappresentano i lati dell'edificio attraverso coppie di vertici.
        range(len... - 1) si ferma prima dell'ultimo punto, che è uguale al primo.
        """
        for i in range(len(vertici) - 1):
            p1 = vertici[i]
            p2 = vertici[i+1]
            
            # creo una linea per questo lato e trova il suo centroide
            lato = LineString([p1, p2])
            midpoint = lato.centroid

            # creo il vettore dal lato dell'edificio
            wall_vector = np.array([p2[0] - p1[0], p2[1] - p1[1]])
            # creo il vettore dalla linea di vista
            view_vector = np.array([tree_centroid.x - midpoint.x, tree_centroid.y - midpoint.y])
            
            # normalizzo i vettori
            norm_wall = np.linalg.norm(wall_vector)
            norm_view = np.linalg.norm(view_vector)
            
            # evito divisioni per zero
            if norm_wall == 0 or norm_view == 0: continue

            # calcolo coseno e angolo
            cos_angle = np.dot(wall_vector, view_vector) / (norm_wall * norm_view)
            angle_deg = np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0)))
            
            # accetto solo se l'angolo è "frontale" (tra 45° e 135°)
            MIN_ANGLE = 90 - MAX_ANGLE_DEG
            MAX_ANGLE = 90 + MAX_ANGLE_DEG
            
            if MIN_ANGLE <= angle_deg <= MAX_ANGLE:
                target_points.append(midpoint)

        # testo la linea di vista per ogni lato valido
        for point in target_points:

            """
            L'uso del blocco try/except salta silenziosamente i punti per i quali la LineString
            non può essere costruita (geometrie computazionalmente non calcolabili o coordinate non valide).
            """
            try:
                # traccio una linea dall'albero al centro della facciata
                line_of_sight = LineString([tree_centroid, point])
            except Exception as e:
                continue

            """
            Primo controllo: gestione del lato opposto dell'edificio rispetto all'albero (Self-occlusion).
            La funzione di Shapely crosses() è true solo se la linea passa "attraverso" l'edificio.
            Questo identifica e scarta i lati opposti, ma dà False per i lati vicini (che "toccano" solo il bordo).
            Quindi, quando la linea attraversa l'edificio, significa che l'albero è sul lato opposto rispetto a quel lato,
            rendendo quella linea non valida per la visuale. Passiamo quindi al prossimo lato con continue.
            """
            if line_of_sight.crosses(building.geometry):
                continue

            """
            Secondo controllo: gestione degli altri possibili ostacoli nella linea di vista.
            Uso l'indice per trovare quasi immediatamente i possibili ostacoli che intersecano la vista.
            Questo riduce drasticamente il numero di ostacoli da controllare geometricamente con solo quelli la cui figura interseca con la linea.
            Se siamo arrivati a questo punto, significa che la linea non attraversa l'edificio campione,
            pertanto possiamo escluderlo dalla lista ostacoli e usare la funzione intersects() per il test finale.
            """
            possible_obstacle_idx = list(obstacles_idx.intersection(line_of_sight.bounds))
            
            # se non ci sono ostacoli possibili nell'indice, la vista è libera
            if not possible_obstacle_idx:
                return True

            # altrimenti, prendi tutti i possibili ostacoli dall' indice (escluso l'edificio campione)
            possible_obstacles = all_buildings_gdf.iloc[possible_obstacle_idx]
            obstacles = possible_obstacles[possible_obstacles.index != building.name]
            
            # se non ci sono altri ostacoli, la vista è libera
            if obstacles.empty:
                return True

            """
            Terzo controllo: intersezione con DEBUFFER.
            Applico un buffer negativo (-0.5m) agli ostacoli. Questo crea una micro-separazione
            tra edifici adiacenti, permettendo alla linea di vista di passare se gli edifici sono solo "toccati".
            Questo infatti generava bug o blocchi inesistenti nella visuale anche per lati che dovrebbero esssere liberi.
            Il filtro angolare fatto all'inizio impedisce comunque che questo debuffer crei visuali irrealistiche attraverso i muri.
            """
            # creo copie temporanee ridotte degli ostacoli
            debuffed_obstacles = obstacles.copy()
            debuffed_obstacles.geometry = debuffed_obstacles.geometry.buffer(DEBUFFER_METRI)

            # intersect ritorna true se c'è intersezione con gli ostacoli
            if not debuffed_obstacles.geometry.intersects(line_of_sight).any():
                return True

        # se il ciclo finisce, nessuna linea è passata, dunque l'albero è ostruito.
        return False
        
    except Exception as e:
        # errore generico
        return False
#importazioni
from shapely.geometry import LineString
import pandas as pd
import logging
import geopandas as gpd
import time 

#costante di buffer di visuale in metri
view_buffer = 50

"""
    Funzione ausiliaria per "spacchettare" la colonna 'tags' (dizionario)
    La usiamo SOLO per il file degli edifici (che viene da OSM).
"""
def unpack_tags(gdf_raw):
    if 'tags' not in gdf_raw.columns:
        logging.warning("Colonna 'tags' non trovata, spacchettamento saltato.")
        return gdf_raw
    try:
        tags_series = gdf_raw['tags'].fillna({}).apply(pd.Series)
        original_cols = gdf_raw.columns.drop('tags')
        cols_to_drop = original_cols.intersection(tags_series.columns)
        safe_tags_df = tags_series.drop(columns=cols_to_drop, errors='ignore')
        gdf_unpacked = gdf_raw.drop(columns=['tags']).join(safe_tags_df)
        return gdf_unpacked
    except Exception as e:
        logging.error(f"Spacchettamento tag fallito: {e}")
        return gdf_raw

"""
    Funzione che verifica se la linea di vista da un albero a un edificio è bloccata
"""
def is_unobstructed(tree, building, all_buildings_gdf, obstacles_idx):
    # ... (Questa funzione è perfetta, non cambia) ...
    try:
        building_point = building.geometry.exterior.interpolate(building.geometry.exterior.project(tree.geometry))
        line_of_sight = LineString([tree.geometry.centroid, building_point])
    except Exception as e:
        return False
    
    possible_obstacle_idx = list(obstacles_idx.intersection(line_of_sight.bounds))
    
    if not possible_obstacle_idx:
        return True
    possible_obstacles = all_buildings_gdf.iloc[possible_obstacle_idx]
    obstacles = possible_obstacles[possible_obstacles.index != building.name]
    
    return not obstacles.geometry.intersects(line_of_sight).any()

"""
    Funzione che calcola il numero di alberi visibili da ogni edificio
    MODIFICATA per usare i dati puliti di Enrico (YOLO) per gli alberi
"""
def run_rule_3(edifici_raw_osm, alberi_puliti_yolo):

    #avvio logger regola
    logger = logging.getLogger("regola3")

    # --- 1. PREPARAZIONE EDIFICI (da OSM) ---
    logger.info("Avvio spacchettamento tag edifici...")
    edifici = unpack_tags(edifici_raw_osm) # Spacchetta i tag degli edifici
    logger.info("Spacchettamento edifici completato.")

    # --- 2. PREPARAZIONE ALBERI (da YOLO) ---
    # I dati di Enrico sono GIA' puliti.
    # Non serve spacchettare, non serve filtrare (mask).
    alberi = alberi_puliti_yolo
    logger.info("Dati alberi (YOLO) caricati, non necessitano filtri.")

    #controllo input
    if edifici.empty or alberi.empty:
        logger.warning("Dati insufficienti (edifici o alberi vuoti).")
        return edifici.assign(visible_trees_count=0)

    #blocco di correzzione e validazione input
    try:
        #proiezione CRS
        if edifici.crs is None:
            edifici.set_crs("EPSG:4326", inplace=True)
        if alberi.crs is None:
            alberi.set_crs("EPSG:4326", inplace=True)

        #filtro edifici (come prima)
        if 'building' in edifici.columns:
            edifici_proj = edifici[edifici['building'].notna()].to_crs("EPSG:32632")
        else:
            edifici_proj = edifici.to_crs("EPSG:32632")

        alberi_proj = alberi.to_crs("EPSG:32632")

        #pulisci geometrie non valide
        edifici_proj = edifici_proj[edifici_proj.geometry.is_valid & ~edifici_proj.geometry.is_empty]
        alberi_proj = alberi_proj[alberi_proj.geometry.is_valid & ~alberi_proj.geometry.is_empty]
        
        if edifici_proj.empty:
             logger.warning("Nessuna geometria edificio valida trovata dopo il filtro.")
             return edifici.assign(visible_trees_count=0)
        
        if alberi_proj.empty:
             logger.warning("Nessuna geometria albero valida trovata dopo il filtro.")
             
    except Exception as e:
        logger.error(f"Errore nella proiezione dei dati: {e}")
        return edifici.assign(visible_trees_count=0)

    #eseguo una copia per i risultati e inizializzo il punteggio a 0 per tutti
    risultato_edifici = edifici_proj.copy()
    risultato_edifici['visible_trees_count'] = 0

    logger.info(f"Avvio calcolo linea di vista per {len(risultato_edifici)} edifici e {len(alberi_proj)} elementi arborei...")

    #Creazione indici spaziali
    alberi_idx = alberi_proj.sindex
    ostacoli_idx = edifici_proj.sindex

    # --- Blocco di calcolo principale (NON CAMBIA) ---
    start_time_loop = time.time()
    
    #itero su ogni edificio
    for i, (idx, edificio) in enumerate(risultato_edifici.iterrows()):

        # Log di progresso ogni 100 edifici
        if (i + 1) % 100 == 0:
            logger.info(f"Processando edificio {i+1} / {len(risultato_edifici)}...")
            
        buffer = edificio.geometry.buffer(view_buffer)
        
        possible_indices = list(alberi_idx.intersection(buffer.bounds))
        if not possible_indices:
            continue 

        trees_candidates = alberi_proj.iloc[possible_indices]
        selected_trees = trees_candidates[trees_candidates.geometry.within(buffer)]
        
        if selected_trees.empty:
            continue 

        visible_trees = 0
        for _, albero in selected_trees.iterrows():
            if is_unobstructed(albero, edificio, edifici_proj, ostacoli_idx):
                visible_trees += 1
                
        risultato_edifici.loc[idx, 'visible_trees_count'] = visible_trees
    
    end_time_loop = time.time()
    logger.info(f"Calcolo linea di vista completato in {end_time_loop - start_time_loop:.2f} secondi.")
    

    # Mappatura finale dei risultati sul GDF originale (in EPSG:4326)
    logger.info("Mappatura risultati finali...")
    
    final_result_gdf = edifici.copy()
    
    final_result_gdf['visible_trees_count'] = final_result_gdf.index.map(
        risultato_edifici['visible_trees_count']
    ).fillna(0).astype(int)
    
    logger.info("Fatto.")
    return final_result_gdf

if __name__ == "__main__":
    
    # Configura il logging per stampare su console
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger = logging.getLogger("analisi_verona_yolo")
    
    INPUT_EDIFICI = "edifici.geojson"
    INPUT_ALBERI = "verona_yolo_multi.geojson"
    OUTPUT_FILE = "risultati_regola3_verona.geojson"

    try:
        # Carica i file GeoJSON
        logger.info(f"Avvio analisi. Caricamento file: {INPUT_EDIFICI}")
        edifici_gdf_raw = gpd.read_file(INPUT_EDIFICI)
        logger.info(f"Caricati {len(edifici_gdf_raw)} edifici.")
        
        logger.info(f"Caricamento file: {INPUT_ALBERI}")
        alberi_gdf_raw = gpd.read_file(INPUT_ALBERI)
        logger.info(f"Caricati {len(alberi_gdf_raw)} alberi (YOLO).")

        logger.info("Avvio 'run_rule_3'...")
        start_time_total = time.time()
        
        # Esegui l'analisi
        risultati_gdf = run_rule_3(edifici_gdf_raw, alberi_gdf_raw)
        
        end_time_total = time.time()
        logger.info(f"Analisi completata in {end_time_total - start_time_total:.2f} secondi.")

        # Salva i risultati
        if not risultati_gdf.empty:
            logger.info(f"Salvataggio risultati in: {OUTPUT_FILE}")
            
            # Pulisci il GDF finale prima di salvarlo
            colonne_da_salvare = ['geometry', 'id', 'type', 'building', 'name', 'visible_trees_count']
            colonne_esistenti = [col for col in colonne_da_salvare if col in risultati_gdf.columns]
            
            risultati_gdf_pulito = risultati_gdf[colonne_esistenti]
            risultati_gdf_pulito.to_file(OUTPUT_FILE, driver="GeoJSON")
            logger.info("Salvataggio completato.")
        else:
            logger.warning("Il risultato è vuoto, nessun file salvato.")
            
    except FileNotFoundError as e:
        logger.error(f"ERRORE: File non trovato. Assicurati che '{e.filename}' sia nella stessa cartella.")
    except Exception as e:
        logger.error(f"ERRORE IMPREVISTO DURANTE L'ESECUZIONE: {e}")
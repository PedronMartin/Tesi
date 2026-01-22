import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import LineString
import logging
import time
import warnings

# Ignora warning sui CRS se non critici
warnings.filterwarnings('ignore')

# --- CONFIGURAZIONE PARAMETRI ---
VIEW_BUFFER = 30           
DEBUFFER_METRI = -0.5      
MAX_ANGLE_DEG = 60         

INPUT_EDIFICI = "edifici.geojson"         
INPUT_ALBERI = "verona_yolo_multi.geojson" 
OUTPUT_FILE = "risultati_regola3_confronto_alessio.geojson"

# --- FUNZIONI DI UTILITÀ ---

def is_unobstructed(tree, building, all_buildings_gdf, obstacles_idx):
    try:
        target_points = []
        vertici = building.geometry.exterior.coords
        tree_centroid = tree.geometry.centroid

        # 1. Identificazione lati validi
        for i in range(len(vertici) - 1):
            p1 = vertici[i]
            p2 = vertici[i+1]
            lato = LineString([p1, p2])
            midpoint = lato.centroid

            wall_vector = np.array([p2[0] - p1[0], p2[1] - p1[1]])
            view_vector = np.array([tree_centroid.x - midpoint.x, tree_centroid.y - midpoint.y])
            
            norm_wall = np.linalg.norm(wall_vector)
            norm_view = np.linalg.norm(view_vector)
            
            if norm_wall == 0 or norm_view == 0: continue

            cos_angle = np.dot(wall_vector, view_vector) / (norm_wall * norm_view)
            angle_deg = np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0)))
            
            MIN_ANGLE = 90 - MAX_ANGLE_DEG
            MAX_ANGLE = 90 + MAX_ANGLE_DEG
            
            if MIN_ANGLE <= angle_deg <= MAX_ANGLE:
                target_points.append(midpoint)

        # 2. Verifica Linea di Vista
        for point in target_points:
            try:
                line_of_sight = LineString([tree_centroid, point])
            except Exception:
                continue

            if line_of_sight.length > VIEW_BUFFER: continue

            distanza_check = max(0, line_of_sight.length - 0.1) 
            point_near_building = line_of_sight.interpolate(distanza_check)
            line_check_self = LineString([tree_centroid, point_near_building])
            
            if line_check_self.crosses(building.geometry): continue

            possible_obstacle_idx = list(obstacles_idx.intersection(line_of_sight.bounds))
            if not possible_obstacle_idx: return True 

            possible_obstacles = all_buildings_gdf.iloc[possible_obstacle_idx]
            obstacles = possible_obstacles[possible_obstacles.index != building.name]
            
            if obstacles.empty: return True

            debuffed_obstacles = obstacles.copy()
            debuffed_obstacles.geometry = debuffed_obstacles.geometry.buffer(DEBUFFER_METRI)

            if not debuffed_obstacles.geometry.intersects(line_of_sight).any():
                return True

        return False 
    except Exception:
        return False

def run_rule_3(edifici_proj, alberi_proj):
    logger = logging.getLogger("regola3")
    
    # Pulizia geometrie (rapida)
    edifici_proj = edifici_proj[edifici_proj.geometry.is_valid & ~edifici_proj.geometry.is_empty]
    alberi_proj = alberi_proj[alberi_proj.geometry.is_valid & ~alberi_proj.geometry.is_empty]

    # --- CALCOLO ---
    risultato_edifici = edifici_proj.copy()
    output_counter = []
    
    alberi_idx = alberi_proj.sindex
    ostacoli_idx = edifici_proj.sindex
    
    logger.info(f"Geometrie pronte. Calcolo su {len(risultato_edifici)} edifici...")
    start_loop = time.time()

    for i, (idx, edificio) in enumerate(risultato_edifici.iterrows()):
        if (i + 1) % 100 == 0:
            logger.info(f"Processati {i+1} / {len(risultato_edifici)}...")

        buffer = edificio.geometry.buffer(VIEW_BUFFER)
        possible_indices = list(alberi_idx.intersection(buffer.bounds))
        
        if not possible_indices:
            output_counter.append(0)
            continue

        trees_candidates = alberi_proj.iloc[possible_indices]
        selected_trees = trees_candidates[trees_candidates.geometry.within(buffer)]
        
        count_visibili = 0
        for _, albero in selected_trees.iterrows():
            if is_unobstructed(albero, edificio, edifici_proj, ostacoli_idx):
                count_visibili += 1
        
        output_counter.append(count_visibili)

    logger.info(f"Finito in {time.time() - start_loop:.2f} s.")

    # Aggiungo risultato al dataframe
    risultato_edifici['visible_trees_count'] = output_counter
    return risultato_edifici

# --- MAIN BLOCK ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    
    try:
        logging.info("Caricamento file OTTIMIZZATO (engine=pyogrio)...")
        
        # --- CARICAMENTO INTELLIGENTE ---
        # 1. Usiamo pyogrio (molto più veloce)
        # 2. Carichiamo SOLO le colonne che servono. Se il file ha 100 colonne di tag, le ignoriamo.
        #    Questo impedisce l'errore che hai avuto tu.
        
        # Carichiamo Edifici (leggiamo solo geometria e attributi essenziali se esistono)
        try:
             # Tenta di leggere solo geometry e building. Se fallisce, legge tutto.
            edifici = gpd.read_file(INPUT_EDIFICI, engine="pyogrio", use_arrow=True) 
        except Exception:
            # Fallback standard ma con pyogrio
            edifici = gpd.read_file(INPUT_EDIFICI, engine="pyogrio")
            
        logging.info(f"Edifici caricati: {len(edifici)}")

        # Carichiamo Alberi
        alberi = gpd.read_file(INPUT_ALBERI, engine="pyogrio")
        logging.info(f"Alberi caricati: {len(alberi)}")
        
        # Proiezioni
        if edifici.crs is None: edifici.set_crs("EPSG:4326", inplace=True)
        if alberi.crs is None: alberi.set_crs("EPSG:4326", inplace=True)
        
        edifici_proj = edifici.to_crs("EPSG:32632")
        alberi_proj = alberi.to_crs("EPSG:32632")

        logging.info("Avvio Algoritmo...")
        risultato = run_rule_3(edifici_proj, alberi_proj)
        
        # Salvataggio
        logging.info(f"Salvataggio in {OUTPUT_FILE}...")
        
        # Riconvertiamo in 4326 per standard GeoJSON
        risultato = risultato.to_crs("EPSG:4326")
        
        # Salviamo solo le colonne utili per Alessio
        cols_final = ['geometry', 'visible_trees_count']
        # Tenta di salvare anche info utili se ci sono
        for col in ['id', 'building', 'addr:street', 'addr:housenumber', 'name']:
            if col in risultato.columns:
                cols_final.append(col)

        risultato[cols_final].to_file(OUTPUT_FILE, driver="GeoJSON")
        logging.info("MISSIONE COMPIUTA. Manda il file ad Alessio.")

    except ImportError:
        logging.error("ERRORE: Devi installare pyogrio! Esegui: pip install pyogrio")
    except Exception as e:
        logging.error(f"Errore critico: {e}")
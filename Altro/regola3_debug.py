#importazioni
from shapely.geometry import LineString
import pandas as pd
import logging
import geopandas as gpd
import time
import numpy as np

# --- CONFIGURAZIONE ---
VIEW_BUFFER = 30 
DEBUFFER_METRI = -0.5
MAX_ANGLE_DEG = 45

# --- DEBUG: Lista globale per salvare le linee ---
g_debug_lines = []

"""
    Funzione ausiliaria per salvare le linee di vista nel debug.
    Ora accetta anche l'ANGOLO calcolato.
"""
def _log_linea_di_vista(linea_geometria, albero, edificio, ostruita, motivo, angolo):
    global g_debug_lines
    try:
        g_debug_lines.append({
            'geometry': linea_geometria,
            'albero_id': albero.get('id', 'N/A'),
            'edificio_id': edificio.get('id', 'N/A'),
            'is_ostruita': int(ostruita), # 0=Verde (Libera), 1=Rossa (Ostruita)
            'motivo': motivo,
            'angolo_deg': float(f"{angolo:.2f}") # Salviamo l'angolo con 2 decimali
        })
    except Exception:
        pass

def unpack_tags(gdf_raw):
    if 'tags' not in gdf_raw.columns: return gdf_raw
    try:
        tags_series = gdf_raw['tags'].fillna({})
        tags_df = tags_series.apply(pd.Series)
        original_cols = gdf_raw.columns.drop('tags')
        cols_to_drop = original_cols.intersection(tags_df.columns)
        safe_tags_df = tags_df.drop(columns=cols_to_drop, errors='ignore')
        return gdf_raw.drop(columns=['tags']).join(safe_tags_df)
    except Exception:
        return gdf_raw

"""
    Funzione che verifica se la linea di vista è bloccata.
    VERSIONE DEBUG: Salva le linee e l'angolo calcolato.
"""
def is_unobstructed(tree, building, all_buildings_gdf, obstacles_idx):

    try:
        # Lista di tuple: (Punto, Angolo)
        target_points_data = []
        
        exterior_coords = building.geometry.exterior.coords
        tree_centroid = tree.geometry.centroid
        
        # 1. Trova i punti target e calcola i loro angoli
        for i in range(len(exterior_coords) - 1):
            p1 = exterior_coords[i]
            p2 = exterior_coords[i+1]
            
            lato = LineString([p1, p2])
            midpoint = lato.centroid

            # --- CALCOLO ANGOLO (Tua Logica) ---
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
                # Salvo il punto E l'angolo per il debug successivo
                target_points_data.append((midpoint, angle_deg))


        # 2. Testa le linee di vista per ogni lato valido
        for midpoint, angle in target_points_data:
            try:
                line_of_sight = LineString([tree_centroid, midpoint])
            except: continue 

            # --- CONTROLLO 1: Self-Occlusion (Crosses) ---
            if line_of_sight.crosses(building.geometry):
                # Loggo la linea fallita (Rossa)
                _log_linea_di_vista(line_of_sight, tree, building, 1, "Auto-Ostruzione (Crosses)", angle)
                continue

            # --- CONTROLLO 2: Ostacoli Esterni ---
            possible_obstacle_idx = list(obstacles_idx.intersection(line_of_sight.bounds))
            
            if not possible_obstacle_idx:
                # Loggo la linea libera (Verde)
                _log_linea_di_vista(line_of_sight, tree, building, 0, "Libera (No Vicini)", angle)
                return True

            possible_obstacles = all_buildings_gdf.iloc[possible_obstacle_idx]
            obstacles = possible_obstacles[possible_obstacles.index != building.name]
            
            if obstacles.empty:
                # Loggo la linea libera (Verde)
                _log_linea_di_vista(line_of_sight, tree, building, 0, "Libera (No Ostacoli)", angle)
                return True

            # --- CONTROLLO 3: Debuffer ---
            shrunk = obstacles.copy()
            shrunk.geometry = shrunk.geometry.buffer(DEBUFFER_METRI)

            if not shrunk.geometry.intersects(line_of_sight).any():
                # Loggo la linea libera (Verde)
                _log_linea_di_vista(line_of_sight, tree, building, 0, "Libera (Intersects False)", angle)
                return True
            
            # Se arrivo qui, è ostruita da un altro edificio
            _log_linea_di_vista(line_of_sight, tree, building, 1, "Ostruita da Esterno", angle)

        return False
        
    except Exception as e:
        return False

"""
    Funzione Principale
"""
def run_rule_3(edifici_raw, alberi_raw):
    logger = logging.getLogger("regola3")
    
    edifici = unpack_tags(edifici_raw)
    alberi = alberi_raw 

    if edifici.empty or alberi.empty: return edifici.assign(visible_trees_count=0)

    try:
        if edifici.crs is None: edifici.set_crs("EPSG:4326", inplace=True)
        if alberi.crs is None: alberi.set_crs("EPSG:4326", inplace=True)

        if 'building' in edifici.columns:
            edifici_proj = edifici[edifici['building'].notna()].to_crs("EPSG:32632")
        else:
            edifici_proj = edifici.to_crs("EPSG:32632")

        alberi_proj = alberi.to_crs("EPSG:32632")
        
        edifici_proj = edifici_proj[edifici_proj.geometry.is_valid & ~edifici_proj.geometry.is_empty]
        alberi_proj = alberi_proj[alberi_proj.geometry.is_valid & ~alberi_proj.geometry.is_empty]

    except Exception as e:
        logger.error(f"Errore proiezione: {e}")
        return edifici.assign(visible_trees_count=0)

    risultato_edifici = edifici_proj.copy()
    risultato_edifici['visible_trees_count'] = 0

    alberi_idx = alberi_proj.sindex
    ostacoli_idx = edifici_proj.sindex

    logger.info(f"Avvio calcolo su {len(risultato_edifici)} edifici...")
    
    start_time_loop = time.time()
    for i, (idx, edificio) in enumerate(risultato_edifici.iterrows()):

        if (i + 1) % 100 == 0: logger.info(f"Processando {i+1}...")
        
        buffer = edificio.geometry.buffer(VIEW_BUFFER)
        possible_indices = list(alberi_idx.intersection(buffer.bounds))
        if not possible_indices: continue

        trees_candidates = alberi_proj.iloc[possible_indices]
        selected_trees = trees_candidates[trees_candidates.geometry.within(buffer)]
        
        visible = 0
        for _, albero in selected_trees.iterrows():
            if is_unobstructed(albero, edificio, edifici_proj, ostacoli_idx):
                visible += 1
        
        risultato_edifici.loc[idx, 'visible_trees_count'] = visible
    
    end_time_loop = time.time()
    logger.info(f"Calcolo completato in {end_time_loop - start_time_loop:.2f} secondi.")
    
    final_result_gdf = edifici.copy()
    final_result_gdf['visible_trees_count'] = final_result_gdf.index.map(
        risultato_edifici['visible_trees_count']
    ).fillna(0).astype(int)
    
    return final_result_gdf

# --- MAIN ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logger = logging.getLogger("analisi")
    
    # INPUT FILE DI TEST
    INPUT_EDIFICI = "edificiOSMverona.geojson"
    INPUT_ALBERI = "alberiOSMverona.geojson"
    
    # OUTPUT
    OUTPUT_FILE = "TEST_REGOLA3.geojson"
    OUTPUT_DEBUG = "LIMITI_DEGRAD.geojson"

    try:
        edifici = gpd.read_file(INPUT_EDIFICI)
        alberi = gpd.read_file(INPUT_ALBERI)
        
        res = run_rule_3(edifici, alberi)
        
        if not res.empty:
            cols = ['geometry', 'id', 'type', 'building', 'name', 'visible_trees_count']
            clean_cols = [c for c in cols if c in res.columns]
            res[clean_cols].to_file(OUTPUT_FILE, driver="GeoJSON")
            logger.info(f"Risultati salvati in {OUTPUT_FILE}")
        
        if g_debug_lines:
            gdf_debug = gpd.GeoDataFrame(g_debug_lines, crs="EPSG:32632")
            gdf_debug.to_crs("EPSG:4326").to_file(OUTPUT_DEBUG, driver="GeoJSON")
            logger.info(f"Linee di debug salvate in {OUTPUT_DEBUG}")
        else:
            logger.warning("Nessuna linea di debug generata.")
            
    except Exception as e:
        logger.error(f"Errore: {e}")
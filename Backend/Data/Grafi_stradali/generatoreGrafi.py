import osmnx as ox
import networkx as nx
import geopandas as gpd
import os
import time

#I/O
inputFile = "./../city_boundaries.json"
outputFolder = "./"

"""
    I grafi scaricabili da OSMnx spesso contengono dati sporchi o inutili.
    Questa funzione serve a pulire i dati, mantenendo solo la rete stradale scelta principale,
    rimuovendo vicoli ciechi isolati e pezzi di grafo non connessi.
    Inoltre, gestisce versioni diverse di OSMnx.
"""
def get_largest_component_safe(G):
    #strongly serve a mantenere l'orientamento delle strade, anche se con le pedonali non dovrebbe essere necessario
    return ox.truncate.largest_component(G, strongly=True)

def download_graphs():
    
    #assunta cartella output già esistente

    #leggo confini nel file di input
    try:
        cities_gdf = gpd.read_file(inputFile)
    except Exception as e:
        print(f"Errore apertura file: {e}")
        return

    #ciclo le città presenti
    for idx, row in cities_gdf.iterrows():
        city_name = row.get('city_name', f"City_{idx}")
        geometry = row.geometry

        #il buffer(0) risolve il 99% dei problemi dovuti a geometrie sporche (self-intersections o altri errori generati da Shapely)
        if not geometry.is_valid:
            print(f"Geometria invalida per {city_name}. Provo fix automatico.")
            geometry = geometry.buffer(0)
        
        #nome di salvataggio sicuro
        safe_name = city_name.replace(" ", "_").replace(",", "")
        file_path = os.path.join(outputFolder, f"{safe_name}.graphml")
        
        print(f"Elaborazione: {city_name}")
        
        #se esiste già per X città, salto
        if os.path.exists(file_path):
            print(f"File già esistente. Non ricalcolo.")
            continue
            
        try:
            
            #download grafo pedonale. La flag simplify riduce i nodi inutili (es. strade dritte con troppi punti)
            print("Download grafo pedonale da OSM (attendere)")
            G = ox.graph_from_polygon(geometry, network_type='walk', simplify=True)
            
            #pulisco dati con funzione ausiliaria
            G_clean = get_largest_component_safe(G)
            
            #salvo in file
            print(f"Salvataggio in {safe_name}.graphml")
            ox.save_graphml(G_clean, file_path)
            
        except Exception as e:
            print(f"ERRORE elaborando {city_name}: {e}")
            raise e 



#MAIN
if __name__ == "__main__":
    download_graphs()
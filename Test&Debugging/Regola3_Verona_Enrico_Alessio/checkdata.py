import geopandas as gpd
import time
import os

# I nomi dei tuoi file
FILE_EDIFICI = "edifici.geojson"
FILE_ALBERI = "verona_yolo_multi.geojson"

def test_load(filename):
    print(f"--------------------------------------------------")
    print(f"TEST: Caricamento {filename}")
    
    # 1. Controllo esistenza e dimensione
    if not os.path.exists(filename):
        print(f"❌ ERRORE: Il file {filename} NON ESISTE.")
        return None
    
    size_mb = os.path.getsize(filename) / (1024 * 1024)
    print(f"📂 Dimensione file: {size_mb:.2f} MB")
    
    if size_mb > 200:
        print("⚠️ ATTENZIONE: Il file è molto grande! Potrebbe essere lento.")

    # 2. Provo a caricare con il motore veloce (pyogrio) se disponibile, altrimenti standard
    try:
        start = time.time()
        # Provo a forzare l'uso di pyogrio che è 10x più veloce
        gdf = gpd.read_file(filename, engine="pyogrio") 
        end = time.time()
        print(f"✅ CARICATO (engine=pyogrio) in {end - start:.2f} secondi.")
    except Exception as e:
        print(f"⚠️ Pyogrio non disponibile o fallito ({e}), provo metodo standard...")
        try:
            start = time.time()
            gdf = gpd.read_file(filename)
            end = time.time()
            print(f"✅ CARICATO (standard) in {end - start:.2f} secondi.")
        except Exception as e2:
            print(f"❌ CRITICO: Impossibile leggere il file. Errore: {e2}")
            return None

    print(f"📊 Info Dati: {len(gdf)} righe trovate.")
    print(f"   Colonne: {list(gdf.columns)}")
    return gdf

if __name__ == "__main__":
    print("AVVIO DIAGNOSTICA FILE...")
    
    edifici = test_load(FILE_EDIFICI)
    alberi = test_load(FILE_ALBERI)
    
    if edifici is not None and alberi is not None:
        print("\n✅ I FILE SONO SANI. Il problema era altrove o nel buffer di stampa.")
    else:
        print("\n❌ C'È UN PROBLEMA CON I FILE.")
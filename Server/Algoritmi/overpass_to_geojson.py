def convert_to_feature(el):
    # Gestione nodi (alberi, punti)
    if el['type'] == 'node':
        geometry = {
            'type': 'Point',
            'coordinates': [el['lon'], el['lat']]
        }
    # Gestione way (edifici, aree verdi)
    elif el['type'] == 'way' and 'geometry' in el:
        coords = [[pt['lon'], pt['lat']] for pt in el['geometry']]
        # Se chiuso, poligono
        if coords[0] == coords[-1]:
            geometry = {
                'type': 'Polygon',
                'coordinates': [coords]
            }
        else:
            geometry = {
                'type': 'LineString',
                'coordinates': coords
            }
    else:
        return None
    return {
        'type': 'Feature',
        'geometry': geometry,
        'properties': el.get('tags', {})
    }

# Esempio di utilizzo:
# overpass_json = ... # risultato della query Overpass
# features = [convert_to_feature(el) for el in overpass_json['elements'] if convert_to_feature(el)]
# Poi filtra per tag come nell'esempio precedente

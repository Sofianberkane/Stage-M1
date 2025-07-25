import os
import folium
from pathlib import Path
import webbrowser
import sys
sys.path.append("C:/Users/sofian.berkane/Downloads/Soso/Code/data")
from gps_utils import convert_to_decimal_degrees, parse_gnrmc_line, haversine_km
os.chdir("C:/Users/sofian.berkane/Downloads/Soso/Code/data")

def tracer_une_carte_par_fichier(dossier_txt):
    dossier = Path(dossier_txt)
    fichiers = list(dossier.glob("*.txt"))
    
    dossier_cartes = Path("C:/Users/sofian.berkane/Downloads/Soso/Code/data/Recup_DATA_AE2T/cartes")
    dossier_cartes.mkdir(parents=True, exist_ok=True)

    if not fichiers:
        print(" Aucun fichier .txt trouvé dans le dossier.")
        return

    for fichier in fichiers:
        with open(fichier, "r") as f:
            coords = [parse_gnrmc_line(line) for line in f if parse_gnrmc_line(line)]
            coords = [c for c in coords if c]

        if not coords or len(coords) < 2:
            print(f" Données insuffisantes dans {fichier.name}")
            continue

        # Créer une carte pour ce fichier
        m = folium.Map(location=coords[0], zoom_start=12, tiles="OpenStreetMap")
        m.add_child(folium.LatLngPopup())
        folium.PolyLine(coords, color='blue', weight=4, tooltip=fichier.name).add_to(m)
        folium.Marker(coords[0], icon=folium.Icon(color='green'), tooltip="Départ").add_to(m)
        folium.Marker(coords[-1], icon=folium.Icon(color='red'), tooltip="Arrivée").add_to(m)

        # Sauvegarder la carte
        nom_carte =  dossier_cartes / f"carte_{fichier.stem}.html"
        m.save(str(nom_carte))
        print(f" Carte générée : {nom_carte}")
        webbrowser.open(nom_carte)
        
# 🧪 Appelle la fonction ici avec ton chemin
tracer_une_carte_par_fichier("C:/Users/sofian.berkane/Downloads/Soso/data_test")

import os
from pathlib import Path
import shutil
from math import radians, cos, sin, asin, sqrt, isfinite
import sys
sys.path.append("C:/Users/sofian.berkane/Downloads/Soso/Code/data")
from gps_utils import convert_to_decimal_degrees, parse_gnrmc_line, haversine_km
os.chdir("C:/Users/sofian.berkane/Downloads/Soso/Code/data")

# ------------ UTILITAIRES GPS --------------

def load_gps_from_file(filepath, sample_rate):
    coords = []
    with open(filepath, "r") as f:
        for line in f:
            if "$GNRMC" in line:
                pt = parse_gnrmc_line(line)
                if pt:
                    coords.append(pt)
    return coords[::sample_rate]

# ------------ MÉTHODE DE COMPARAISON LOCALE --------------

def count_close_matches(test_coords, ref_coords, threshold_km):
    count = 0
    for pt in test_coords:
        distances = [haversine_km(pt, ref_pt) for ref_pt in ref_coords]
        if min(distances) < threshold_km:
            count += 1
    return count

# ------------ CLASSIFICATION PRINCIPALE --------------

def classify_by_local_matching(ref_folder, input_folder, output_folder, sample_rate, threshold_km):
    ref_folder = Path(ref_folder)
    input_folder = Path(input_folder)
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    # Charger tous les parcours de référence
    reference_paths = {}
    for ref_file in ref_folder.glob("*.txt"):
        name = ref_file.stem
        coords = load_gps_from_file(ref_file, sample_rate=1)  # on ne sample pas les références
        if coords:
            reference_paths[name] = coords
    print(f"{len(reference_paths)} parcours de référence chargés.")

    # Traiter chaque fichier brut
    for file in input_folder.glob("*.txt"):
        print(f"\nTraitement de {file.name}...")
        coords_test = load_gps_from_file(file, sample_rate=sample_rate)

        if len(coords_test) < 10:
            print(" Trop peu de points valides, ignoré.")
            continue
        
        # 🔒 Filtrer les trajets trop courts (< 1 km)
        start_point = coords_test[0]
        end_point = coords_test[-1]
        trajet_km = haversine_km(start_point, end_point)
        if trajet_km < 3.0:
            print(f"   Trajet ignoré (distance départ-arrivée < 1 km : {trajet_km:.2f} km)")
            continue

        scores = {}
        for ref_name, ref_coords in reference_paths.items():
            match_count = count_close_matches(coords_test, ref_coords, threshold_km)
            scores[ref_name] = match_count
            print(f" {ref_name} → {match_count} points proches")

        best_match = max(scores, key=scores.get)
        if scores[best_match] == 0:
            print("Aucun match significatif trouvé.")
            continue

        dest = output_folder / best_match
        dest.mkdir(exist_ok=True)
        shutil.copy(file, dest / file.name)
        print(f"Classé dans : {best_match}")

# ------------ PARAMÈTRES D'APPEL --------------

if __name__ == "__main__":
    dossier_ref = "C:/Users/sofian.berkane/Downloads/Soso/Code/data/fichiers_tram/ref"
    dossier_input = "C:/Users/sofian.berkane/Downloads/Soso/Code/data/fichiers_tram/brut"
    dossier_output = "C:/Users/sofian.berkane/Downloads/Soso/Code/data/fichiers_tram/resultats"

    classify_by_local_matching(
        ref_folder=dossier_ref,
        input_folder=dossier_input,
        output_folder=dossier_output,
        sample_rate=30,          # un point sur 30
        threshold_km=0.02        # 50 mètres
    )

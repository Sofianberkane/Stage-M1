import os
from pathlib import Path
from math import radians, cos, sin, asin, sqrt
import sys
sys.path.append("C:/Users/sofian.berkane/Downloads/Soso/Code/data")
from gps_utils import convert_to_decimal_degrees, parse_gnrmc_line, haversine_km
os.chdir("C:/Users/sofian.berkane/Downloads/Soso/Code/data")

# === CONFIGURATION ===
TERMINUS_DICT = {
    "ligne_4": [(45.7815, 4.8722), (45.6882, 4.8652)],
    "ligne_1": [(45.7869, 4.8819), (45.7312, 4.8346)],
    "ligne_2": [(45.6926, 4.9559), (45.7495, 4.8270)],
    "ligne_5": [(45.7319, 4.9481), (45.7425, 4.8793)],
    "ligne_3": [(45.7567, 4.8619), (45.7677, 5.0316)],
    "ligne_6": [(45.7476, 4.8968), (45.7312, 4.8347)]
}

SEUIL_TERMINUS_KM = 0.2  # 50 m
DISTANCE_MIN_KM = 3   # 100 m


def est_proche(pt, ref, seuil=SEUIL_TERMINUS_KM):
    return haversine_km(pt, ref) <= seuil

def segment_distance(coords):
    if len(coords) < 2:
        return 0
    return sum(haversine_km(coords[i], coords[i+1]) for i in range(len(coords)-1))

# === MAIN SEGMENTATION ===

def segmenter_fichier(fichier, term_A, term_B, dossier):
    with open(fichier, "r") as f:
        lignes = [l for l in f if "$GNRMC" in l]
    coords = [parse_gnrmc_line(l) for l in lignes]
    valid = [(l, c) for l, c in zip(lignes, coords) if c]

    if len(valid) < 10:
        return

    segments = []
    segment_lines = []
    segment_coords = []

    dans_terminus = None
    en_segment = False
    origine = None

    for line, coord in valid:
        proche_A = est_proche(coord, term_A)
        proche_B = est_proche(coord, term_B)

        if proche_A:
            if not dans_terminus:
                dans_terminus = 'A'
            if en_segment:
                if origine == 'A':
                    # retour vers point de départ → ignorer
                    pass
                elif origine == 'B':
                    segments.append((segment_lines.copy(), segment_coords.copy(), 'sens_2'))
                else:
                    segments.append((segment_lines.copy(), segment_coords.copy(), 'sens_2'))
                segment_lines.clear()
                segment_coords.clear()
                en_segment = False
                origine = None
            continue

        if proche_B:
            if not dans_terminus:
                dans_terminus = 'B'
            if en_segment:
                if origine == 'B':
                    pass
                elif origine == 'A':
                    segments.append((segment_lines.copy(), segment_coords.copy(), 'sens_1'))
                else:
                    segments.append((segment_lines.copy(), segment_coords.copy(), 'sens_1'))
                segment_lines.clear()
                segment_coords.clear()
                en_segment = False
                origine = None
            continue

        # === Sortie d’un terminus ===
        if dans_terminus:
            origine = dans_terminus
            dans_terminus = None
            en_segment = True
            segment_lines = []
            segment_coords = []

        if en_segment:
            segment_lines.append(line)
            segment_coords.append(coord)

    # Dernier segment
    if en_segment and segment_coords:
        if origine == 'A':
            segments.append((segment_lines, segment_coords, 'sens_1'))
        elif origine == 'B':
            segments.append((segment_lines, segment_coords, 'sens_2'))

    # Enregistrer segments valides
    for idx, (lines, coords, sens) in enumerate(segments):
        d = segment_distance(coords)
        if d < DISTANCE_MIN_KM:
            continue
        dest = dossier / sens
        dest.mkdir(exist_ok=True)
        out_name = f"{fichier.stem}_segment_{idx+1}.txt"
        with open(dest / out_name, "w") as f_out:
            f_out.writelines(lines)

# === GLOBALE ===

def traiter_tous_les_dossiers(base_resultats):
    base = Path(base_resultats)
    for dossier in base.iterdir():
        if not dossier.is_dir():
            continue
        nom = dossier.name
        if nom not in TERMINUS_DICT:
            print(f"⚠️ Terminus inconnus pour {nom}")
            continue

        term_A, term_B = TERMINUS_DICT[nom]
        print(f"\n🔍 Traitement : {nom}")

        for fichier in dossier.glob("*.txt"):
            segmenter_fichier(fichier, term_A, term_B, dossier)
            fichier.unlink()  # Supprimer l’original après découpe

# === LANCEMENT ===

if __name__ == "__main__":
    dossier_resultats = "C:/Users/sofian.berkane/Downloads/Soso/Code/data/fichiers_tram/resultats"
    traiter_tous_les_dossiers(dossier_resultats)

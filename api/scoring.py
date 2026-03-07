"""Auto-scoring des annonces selon le cahier des charges."""

from api.models import Annonce

# Quartiers avec leurs scores pré-calculés
QUARTIER_SCORES = {
    # 6e - Top
    "vauban": 95,
    "castellane": 90,
    "palais de justice": 88,
    "notre-dame-du-mont": 75,
    "prefecure": 85,
    "lodi": 80,
    # 7e - Très bon
    "saint-victor": 90,
    "le pharo": 85,
    "endoume": 82,
    "bompard": 80,
    "roucas blanc": 78,
    "saint-lambert": 75,
    # 4e - Bon
    "cinq avenues": 88,
    "longchamp": 85,
    "les chartreux": 80,
    "la blancarde": 75,
    # 5e - Bon
    "la plaine": 78,
    "le camas": 75,
    "baille": 72,
    # 8e - Intéressant
    "perier": 82,
    "prado": 80,
    "saint-giniez": 78,
    "bonneveine": 72,
    "la plage": 75,
    "pointe rouge": 70,
    "montredon": 65,
    # Éliminatoires
    "belsunce": 20,
    "noailles": 25,
    "la joliette": 40,
    "le panier": 45,
    "belle de mai": 15,
    "saint-mauront": 10,
}

# Arrondissements par défaut si quartier inconnu
ARRONDISSEMENT_SCORES = {
    "6e": 85,
    "7e": 80,
    "4e": 78,
    "5e": 72,
    "8e": 75,
    "1er": 50,
    "2e": 40,
    "3e": 15,
    "9e": 55,
    "10e": 30,
    "11e": 35,
    "12e": 55,
    "13e": 15,
    "14e": 10,
    "15e": 10,
    "16e": 10,
}


def compute_score(annonce: Annonce) -> int:
    """
    Calcule un score de 0 à 100 pour une annonce.
    
    Pondération :
    - Localisation : 30 pts
    - Surface & agencement : 20 pts
    - Prix : 15 pts
    - Confort & cachet : 15 pts
    - Extras (terrasse, cave, vélo) : 10 pts
    - DPE : 10 pts
    """
    score = 0.0

    # === LOCALISATION (30 pts) ===
    loc_score = 50  # default
    if annonce.quartier:
        q = annonce.quartier.lower().strip()
        for key, val in QUARTIER_SCORES.items():
            if key in q:
                loc_score = val
                break
    elif annonce.arrondissement:
        arr = annonce.arrondissement.lower().strip()
        for key, val in ARRONDISSEMENT_SCORES.items():
            if key in arr:
                loc_score = val
                break
    score += (loc_score / 100) * 30

    # === SURFACE & AGENCEMENT (20 pts) ===
    surf = annonce.surface_m2
    if 95 <= surf <= 120:
        score += 20  # idéal
    elif 80 <= surf < 95:
        score += 15
    elif 120 < surf <= 140:
        score += 17
    elif surf > 140:
        score += 10  # trop grand = charges
    else:
        score += 5  # trop petit

    # Bonus traversant
    if annonce.traversant:
        score += 3

    # Bonus chambres
    if annonce.nb_chambres and annonce.nb_chambres >= 2:
        score += 2
    if annonce.nb_chambres and annonce.nb_chambres >= 3:
        score += 1

    # === PRIX (15 pts) ===
    prix = annonce.prix
    if prix <= 900_000:
        score += 15
    elif prix <= 1_000_000:
        score += 13
    elif prix <= 1_200_000:
        score += 10
    elif prix <= 1_500_000:
        score += 7
    else:
        score += 0

    # Prix au m²
    prix_m2 = annonce.prix_m2 or (prix / surf if surf > 0 else 0)
    if prix_m2 <= 7000:
        score += 3
    elif prix_m2 <= 8500:
        score += 2
    elif prix_m2 <= 10000:
        score += 1

    # === CONFORT & CACHET (15 pts) ===
    # On ne peut scorer que ce qu'on sait
    if annonce.ascenseur:
        score += 3
    if annonce.exposition:
        expo = annonce.exposition.lower()
        if "sud" in expo:
            score += 4
        elif "ouest" in expo or "est" in expo:
            score += 2
        elif "nord" in expo:
            score -= 5  # éliminatoire-ish

    # Type de bien bonus
    if annonce.type_bien in ("duplex", "maison"):
        score += 3
    
    # === EXTRAS (10 pts) ===
    if annonce.terrasse or annonce.balcon:
        score += 3
    if annonce.terrasse_m2 and annonce.terrasse_m2 >= 20:
        score += 2
    if annonce.cave:
        score += 2
    if annonce.parking:
        score += 1
    if annonce.local_velo:
        score += 3
    elif annonce.cave:  # cave peut servir pour vélo
        score += 1

    # === DPE (10 pts) ===
    dpe_scores = {"A": 10, "B": 9, "C": 7, "D": 5, "E": 3, "F": 1, "G": 0}
    if annonce.dpe and annonce.dpe.upper() in dpe_scores:
        score += dpe_scores[annonce.dpe.upper()]

    # Clamp 0-100
    return max(0, min(100, int(score)))

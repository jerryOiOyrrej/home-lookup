"""Database models for the Marseille apartment search app."""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel, JSON, Column


class Statut(str, Enum):
    nouveau = "nouveau"
    interessant = "interessant"
    a_visiter = "a_visiter"
    visite = "visite"
    offre = "offre"
    ecarte = "ecarte"


class Source(str, Enum):
    bienici = "bienici"
    seloger = "seloger"
    leboncoin = "leboncoin"
    pap = "pap"
    figaro = "figaro"
    barnes = "barnes"
    autre = "autre"


class TypeBien(str, Enum):
    appartement = "appartement"
    maison = "maison"
    duplex = "duplex"
    loft = "loft"
    autre = "autre"


class Quartier(SQLModel, table=True):
    """Quartiers de Marseille avec métadonnées pour le scoring."""

    id: Optional[int] = Field(default=None, primary_key=True)
    nom: str = Field(index=True, unique=True)
    arrondissement: str
    distance_velo_st_charles_min: Optional[int] = None
    distance_velo_port_min: Optional[int] = None
    pente: Optional[str] = None  # plat, modere, raide
    ambiance: Optional[str] = None
    score_global: Optional[int] = None  # 0-100
    notes: Optional[str] = None


class Annonce(SQLModel, table=True):
    """Une annonce immobilière."""

    id: Optional[int] = Field(default=None, primary_key=True)
    url: str = Field(index=True, unique=True)
    source: Source
    titre: str
    description: Optional[str] = None

    # Prix
    prix: int
    prix_m2: Optional[int] = None
    prix_historique: Optional[list] = Field(default=None, sa_column=Column(JSON))

    # Caractéristiques
    surface_m2: float
    nb_pieces: int
    nb_chambres: Optional[int] = None
    type_bien: TypeBien = TypeBien.appartement
    etage: Optional[int] = None
    etage_total: Optional[int] = None
    ascenseur: Optional[bool] = None
    traversant: Optional[bool] = None
    exposition: Optional[str] = None

    # Extérieur
    terrasse: Optional[bool] = None
    terrasse_m2: Optional[float] = None
    balcon: Optional[bool] = None
    jardin: Optional[bool] = None

    # Stockage / parking
    cave: Optional[bool] = None
    parking: Optional[bool] = None
    local_velo: Optional[bool] = None

    # Énergie
    dpe: Optional[str] = None
    ges: Optional[str] = None

    # Localisation
    quartier: Optional[str] = None
    arrondissement: Optional[str] = None
    adresse: Optional[str] = None

    # Agence
    agence: Optional[str] = None
    telephone: Optional[str] = None

    # Médias
    photos: Optional[list] = Field(default=None, sa_column=Column(JSON))
    nb_photos: Optional[int] = None

    # Scoring & statut
    score: Optional[int] = None  # 0-100, auto-calculé
    statut: Statut = Statut.nouveau
    notes_perso: Optional[str] = None
    raison_ecarte: Optional[str] = None

    # Timestamps
    first_seen_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class AnnonceCreate(SQLModel):
    """Schema pour créer une annonce."""

    url: str
    source: Source
    titre: str
    description: Optional[str] = None
    prix: int
    surface_m2: float
    nb_pieces: int
    nb_chambres: Optional[int] = None
    type_bien: TypeBien = TypeBien.appartement
    etage: Optional[int] = None
    etage_total: Optional[int] = None
    ascenseur: Optional[bool] = None
    traversant: Optional[bool] = None
    exposition: Optional[str] = None
    terrasse: Optional[bool] = None
    terrasse_m2: Optional[float] = None
    balcon: Optional[bool] = None
    jardin: Optional[bool] = None
    cave: Optional[bool] = None
    parking: Optional[bool] = None
    local_velo: Optional[bool] = None
    dpe: Optional[str] = None
    ges: Optional[str] = None
    quartier: Optional[str] = None
    arrondissement: Optional[str] = None
    adresse: Optional[str] = None
    agence: Optional[str] = None
    telephone: Optional[str] = None
    photos: Optional[list] = None
    nb_photos: Optional[int] = None
    notes_perso: Optional[str] = None


class AnnonceUpdate(SQLModel):
    """Schema pour mettre à jour une annonce."""

    titre: Optional[str] = None
    description: Optional[str] = None
    prix: Optional[int] = None
    surface_m2: Optional[float] = None
    nb_pieces: Optional[int] = None
    nb_chambres: Optional[int] = None
    type_bien: Optional[TypeBien] = None
    etage: Optional[int] = None
    ascenseur: Optional[bool] = None
    traversant: Optional[bool] = None
    exposition: Optional[str] = None
    terrasse: Optional[bool] = None
    terrasse_m2: Optional[float] = None
    balcon: Optional[bool] = None
    jardin: Optional[bool] = None
    cave: Optional[bool] = None
    parking: Optional[bool] = None
    local_velo: Optional[bool] = None
    dpe: Optional[str] = None
    ges: Optional[str] = None
    quartier: Optional[str] = None
    arrondissement: Optional[str] = None
    statut: Optional[Statut] = None
    notes_perso: Optional[str] = None
    raison_ecarte: Optional[str] = None
    photos: Optional[list] = None

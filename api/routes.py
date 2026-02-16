"""API routes for the apartment search app."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, col

from api.database import get_session
from api.models import (
    Annonce, AnnonceCreate, AnnonceUpdate,
    Quartier, Statut, Source, TypeBien,
)
from api.scoring import compute_score
from api.auth import get_current_user

router = APIRouter(prefix="/api")


# ── Annonces ─────────────────────────────────────────────────


@router.get("/annonces")
def list_annonces(
    statut: Optional[Statut] = None,
    source: Optional[Source] = None,
    arrondissement: Optional[str] = None,
    quartier: Optional[str] = None,
    type_bien: Optional[TypeBien] = None,
    prix_min: Optional[int] = None,
    prix_max: Optional[int] = None,
    surface_min: Optional[float] = None,
    surface_max: Optional[float] = None,
    score_min: Optional[int] = None,
    sort_by: str = Query(default="score", pattern="^(score|prix|surface_m2|prix_m2|first_seen_at)$"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    session: Session = Depends(get_session),
):
    """Liste les annonces avec filtres et tri."""
    query = select(Annonce)

    if statut:
        query = query.where(Annonce.statut == statut)
    if source:
        query = query.where(Annonce.source == source)
    if arrondissement:
        query = query.where(Annonce.arrondissement == arrondissement)
    if quartier:
        query = query.where(col(Annonce.quartier).contains(quartier))
    if type_bien:
        query = query.where(Annonce.type_bien == type_bien)
    if prix_min:
        query = query.where(Annonce.prix >= prix_min)
    if prix_max:
        query = query.where(Annonce.prix <= prix_max)
    if surface_min:
        query = query.where(Annonce.surface_m2 >= surface_min)
    if surface_max:
        query = query.where(Annonce.surface_m2 <= surface_max)
    if score_min:
        query = query.where(Annonce.score >= score_min)

    # Tri
    sort_col = getattr(Annonce, sort_by)
    if sort_order == "desc":
        query = query.order_by(col(sort_col).desc())
    else:
        query = query.order_by(col(sort_col).asc())

    query = query.offset(offset).limit(limit)
    annonces = session.exec(query).all()

    total = session.exec(
        select(Annonce).where(*query.whereclause.clauses if hasattr(query.whereclause, 'clauses') else [])
    ).all() if False else None  # TODO: count query

    return {"annonces": annonces, "count": len(annonces)}


@router.get("/annonces/{annonce_id}")
def get_annonce(annonce_id: int, session: Session = Depends(get_session)):
    """Détail d'une annonce."""
    annonce = session.get(Annonce, annonce_id)
    if not annonce:
        raise HTTPException(404, "Annonce introuvable")
    return annonce


@router.post("/annonces", status_code=201)
def create_annonce(data: AnnonceCreate, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    """Créer une nouvelle annonce."""
    # Vérifier doublon par URL
    existing = session.exec(select(Annonce).where(Annonce.url == data.url)).first()
    if existing:
        # Mise à jour du last_seen_at et éventuellement du prix
        existing.last_seen_at = datetime.utcnow()
        if data.prix != existing.prix:
            # Tracker l'historique de prix
            if not existing.prix_historique:
                existing.prix_historique = []
            existing.prix_historique.append({
                "prix": existing.prix,
                "date": existing.last_seen_at.isoformat(),
            })
            existing.prix = data.prix
            existing.prix_m2 = int(data.prix / data.surface_m2) if data.surface_m2 > 0 else None
        existing.updated_at = datetime.utcnow()
        existing.score = compute_score(existing)
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return {"status": "updated", "annonce": existing}

    annonce = Annonce(**data.model_dump())
    annonce.prix_m2 = int(data.prix / data.surface_m2) if data.surface_m2 > 0 else None
    annonce.score = compute_score(annonce)
    session.add(annonce)
    session.commit()
    session.refresh(annonce)
    return {"status": "created", "annonce": annonce}


@router.patch("/annonces/{annonce_id}")
def update_annonce(
    annonce_id: int,
    data: AnnonceUpdate,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    """Mettre à jour une annonce (statut, notes, etc.)."""
    annonce = session.get(Annonce, annonce_id)
    if not annonce:
        raise HTTPException(404, "Annonce introuvable")

    update_data = data.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        setattr(annonce, key, val)

    annonce.updated_at = datetime.utcnow()

    # Recalculer le prix/m² si prix ou surface changé
    if "prix" in update_data or "surface_m2" in update_data:
        annonce.prix_m2 = int(annonce.prix / annonce.surface_m2) if annonce.surface_m2 > 0 else None

    # Recalculer le score
    annonce.score = compute_score(annonce)

    session.add(annonce)
    session.commit()
    session.refresh(annonce)
    return annonce


@router.delete("/annonces/{annonce_id}")
def delete_annonce(annonce_id: int, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    """Supprimer une annonce."""
    annonce = session.get(Annonce, annonce_id)
    if not annonce:
        raise HTTPException(404, "Annonce introuvable")
    session.delete(annonce)
    session.commit()
    return {"status": "deleted"}


@router.post("/annonces/{annonce_id}/ecarter")
def ecarter_annonce(
    annonce_id: int,
    raison: str = Query(...),
    session: Session = Depends(get_session),
):
    """Écarter une annonce avec une raison."""
    annonce = session.get(Annonce, annonce_id)
    if not annonce:
        raise HTTPException(404, "Annonce introuvable")
    annonce.statut = Statut.ecarte
    annonce.raison_ecarte = raison
    annonce.updated_at = datetime.utcnow()
    session.add(annonce)
    session.commit()
    return annonce


# ── Stats ────────────────────────────────────────────────────


@router.get("/stats")
def get_stats(session: Session = Depends(get_session)):
    """Statistiques globales."""
    all_annonces = session.exec(select(Annonce)).all()
    if not all_annonces:
        return {"total": 0}

    active = [a for a in all_annonces if a.statut != Statut.ecarte]
    return {
        "total": len(all_annonces),
        "par_statut": {
            s.value: len([a for a in all_annonces if a.statut == s])
            for s in Statut
        },
        "par_arrondissement": _count_by(active, "arrondissement"),
        "prix_moyen": int(sum(a.prix for a in active) / len(active)) if active else 0,
        "prix_m2_moyen": int(
            sum(a.prix_m2 for a in active if a.prix_m2) /
            len([a for a in active if a.prix_m2])
        ) if any(a.prix_m2 for a in active) else 0,
        "score_moyen": int(
            sum(a.score for a in active if a.score is not None) /
            len([a for a in active if a.score is not None])
        ) if any(a.score is not None for a in active) else 0,
    }


def _count_by(annonces: list, field: str) -> dict:
    counts = {}
    for a in annonces:
        val = getattr(a, field) or "inconnu"
        counts[val] = counts.get(val, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: -x[1]))


# ── Quartiers ────────────────────────────────────────────────


@router.get("/quartiers")
def list_quartiers(session: Session = Depends(get_session)):
    """Liste des quartiers."""
    return session.exec(select(Quartier).order_by(col(Quartier.score_global).desc())).all()


@router.post("/quartiers", status_code=201)
def create_quartier(quartier: Quartier, session: Session = Depends(get_session)):
    """Ajouter un quartier."""
    session.add(quartier)
    session.commit()
    session.refresh(quartier)
    return quartier

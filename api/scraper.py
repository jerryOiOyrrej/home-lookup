"""Scrape annonce details from a URL."""

import re
from typing import Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9",
}


def detect_source(url: str) -> str:
    domain = urlparse(url).netloc.lower()
    if "bienici" in domain:
        return "bienici"
    if "seloger" in domain:
        return "seloger"
    if "leboncoin" in domain:
        return "leboncoin"
    if "pap.fr" in domain:
        return "pap"
    if "figaro" in domain or "bellesdemeures" in domain:
        return "figaro"
    if "barnes" in domain:
        return "barnes"
    return "autre"


def _first_int(patterns: list[str], text: str) -> Optional[int]:
    """Try multiple regex patterns, return first int match."""
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            raw = m.group(1).replace("\xa0", "").replace(" ", "").replace(".", "").replace(",", "")
            try:
                return int(raw)
            except ValueError:
                continue
    return None


def _first_float(patterns: list[str], text: str) -> Optional[float]:
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            raw = m.group(1).replace("\xa0", "").replace(" ", "").replace(",", ".")
            try:
                return float(raw)
            except ValueError:
                continue
    return None


def _extract_arrondissement(text: str) -> Optional[str]:
    m = re.search(r"(\d{1,2})(?:e|è|ème|er)\s*arrondissement", text, re.IGNORECASE)
    if m:
        return f"{m.group(1)}e"
    m = re.search(r"marseille\s+(\d{1,2})(?:e|è|ème|er)?", text, re.IGNORECASE)
    if m:
        return f"{m.group(1)}e"
    # Postal code 130XX
    m = re.search(r"130(\d{2})", text)
    if m:
        arr = int(m.group(1))
        if 1 <= arr <= 16:
            return f"{arr}e"
    return None


def _has_keyword(text: str, keywords: list[str]) -> Optional[bool]:
    t = text.lower()
    for kw in keywords:
        if kw in t:
            return True
    return None


def _extract_dpe(text: str) -> Optional[str]:
    m = re.search(r"(?:dpe|diagnostic|énergie|energy)[^a-z]*([A-G])\b", text, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    return None


async def scrape_annonce(url: str) -> dict:
    """Fetch URL and extract annonce data. Returns a dict compatible with AnnonceCreate."""
    async with httpx.AsyncClient(follow_redirects=True, timeout=20, headers=HEADERS) as client:
        resp = await client.get(url)
        resp.raise_for_status()

    html = resp.text
    soup = BeautifulSoup(html, "html.parser")

    # Full text for regex
    text = soup.get_text(separator=" ", strip=True)

    # Title
    og_title = soup.find("meta", property="og-title") or soup.find("meta", property="og:title")
    title_tag = soup.find("title")
    titre = ""
    if og_title and og_title.get("content"):
        titre = og_title["content"]
    elif title_tag:
        titre = title_tag.get_text(strip=True)

    # Description
    og_desc = soup.find("meta", property="og:description") or soup.find("meta", attrs={"name": "description"})
    description = og_desc["content"] if og_desc and og_desc.get("content") else None

    # Prix
    prix = _first_int([
        r"(\d[\d\s\xa0.]{2,10})\s*€",
        r"prix[^:]*:\s*(\d[\d\s\xa0.]{2,10})",
        r"(\d{3,}[\s\xa0.]?\d{3})\s*(?:euros|EUR)",
    ], text)

    # Surface
    surface = _first_float([
        r"(\d{2,4}(?:[.,]\d+)?)\s*m²",
        r"surface[^:]*:\s*(\d{2,4}(?:[.,]\d+)?)",
    ], text)

    # Pieces
    nb_pieces = _first_int([
        r"(\d+)\s*pièce",
        r"T(\d+)",
        r"F(\d+)",
    ], text)

    # Chambres
    nb_chambres = _first_int([
        r"(\d+)\s*chambre",
    ], text)

    # Arrondissement
    arrondissement = _extract_arrondissement(text)

    # DPE
    dpe = _extract_dpe(text)

    # Boolean features
    terrasse = _has_keyword(text, ["terrasse"])
    balcon = _has_keyword(text, ["balcon"])
    cave = _has_keyword(text, ["cave"])
    parking = _has_keyword(text, ["parking", "garage", "stationnement"])
    ascenseur = _has_keyword(text, ["ascenseur"])
    traversant = _has_keyword(text, ["traversant"])
    jardin = _has_keyword(text, ["jardin"])

    # Photos count
    images = soup.find_all("img")
    photo_urls = [img.get("src") or img.get("data-src") for img in images if img.get("src") or img.get("data-src")]
    # Filter likely property photos (heuristic)
    nb_photos = len([u for u in photo_urls if u and ("photo" in u or "image" in u or "img" in u or "cdn" in u)])

    # Type bien
    type_bien = "appartement"
    tl = text.lower()
    if "maison" in tl:
        type_bien = "maison"
    elif "duplex" in tl:
        type_bien = "duplex"
    elif "loft" in tl:
        type_bien = "loft"

    source = detect_source(url)

    result = {
        "url": url,
        "source": source,
        "titre": titre or f"Annonce {source}",
        "description": description,
        "prix": prix or 0,
        "surface_m2": surface or 0,
        "nb_pieces": nb_pieces or 0,
        "nb_chambres": nb_chambres,
        "type_bien": type_bien,
        "arrondissement": arrondissement,
        "dpe": dpe,
        "terrasse": terrasse,
        "balcon": balcon,
        "cave": cave,
        "parking": parking,
        "ascenseur": ascenseur,
        "traversant": traversant,
        "jardin": jardin,
        "nb_photos": nb_photos if nb_photos > 0 else None,
    }

    # Remove None values
    return {k: v for k, v in result.items() if v is not None}

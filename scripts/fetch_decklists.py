"""Récupère les decklists officielles publiées sur fabtcg.com.

Le script lit le tableau de https://fabtcg.com/decklists/ page par page
(colonnes : Country/Region, Date, Name, Event, Format, Hero, Rank),
garde les decklists du format choisi publiées depuis la date "since"
de config.json, et écrit le résultat dans data/decklists.json.

Il n'utilise que la bibliothèque standard de Python : rien à installer.
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LISTING_URL = "https://fabtcg.com/decklists/"
USER_AGENT = "fab-meta-static-site/1.0 (non-commercial fan site)"
DELAY_SECONDS = 1.0  # pause entre deux pages, pour rester poli avec le site


# --------------------------------------------------------------------------
# Lecture des tableaux HTML
# --------------------------------------------------------------------------
class TableParser(HTMLParser):
    """Extrait tous les <table> d'une page : lignes -> cellules (texte, lien)."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[dict]] = []
        self._depth = 0
        self._row: list[dict] | None = None
        self._cell: dict | None = None

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._depth += 1
            if self._depth == 1:
                self.tables.append([])
        elif self._depth != 1:
            return
        elif tag == "tr":
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = {"text": "", "href": None, "header": tag == "th"}
        elif tag == "a" and self._cell is not None and self._cell["href"] is None:
            self._cell["href"] = dict(attrs).get("href")
        elif tag == "br" and self._cell is not None:
            self._cell["text"] += " "

    def handle_endtag(self, tag):
        if tag == "table":
            self._depth = max(0, self._depth - 1)
        elif self._depth != 1:
            return
        elif tag in ("td", "th") and self._cell is not None and self._row is not None:
            self._cell["text"] = " ".join(self._cell["text"].split())
            self._row.append(self._cell)
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if self._row:
                self.tables[-1].append({"cells": self._row})
            self._row = None

    def handle_data(self, data):
        if self._cell is not None:
            self._cell["text"] += data


COLUMN_KEYS = {
    "country": ("country", "region", "pays"),
    "date": ("date",),
    "name": ("name", "decklist", "nom"),
    "event": ("event", "évén", "tournament"),
    "format": ("format",),
    "hero": ("hero", "héros"),
    "rank": ("rank", "place", "position", "finish"),
}


def map_columns(header: list[str]) -> dict[str, int]:
    mapping: dict[str, int] = {}
    for i, label in enumerate(header):
        low = label.lower()
        for key, words in COLUMN_KEYS.items():
            if key not in mapping and any(w in low for w in words):
                mapping[key] = i
                break
    return mapping


def parse_listing(html: str) -> list[dict]:
    parser = TableParser()
    parser.feed(html)
    for table in parser.tables:
        if not table:
            continue
        header = [c["text"] for c in table[0]["cells"]]
        cols = map_columns(header)
        if not {"date", "format", "hero"} <= cols.keys():
            continue
        rows = []
        for row in table[1:]:
            cells = row["cells"]
            if len(cells) < len(header):
                continue

            def get(key):
                idx = cols.get(key)
                return cells[idx] if idx is not None else {"text": "", "href": None}

            rows.append(
                {
                    "date_raw": get("date")["text"],
                    "name": get("name")["text"],
                    "url": get("name")["href"],
                    "event": get("event")["text"],
                    "event_url": get("event")["href"],
                    "format": get("format")["text"],
                    "hero": get("hero")["text"],
                    "rank_raw": get("rank")["text"],
                    "country": get("country")["text"],
                }
            )
        return rows
    raise ValueError(
        "Aucun tableau de decklists trouvé sur la page (colonnes Date/Format/Hero). "
        "La mise en page de fabtcg.com a peut-être changé."
    )


# --------------------------------------------------------------------------
# Nettoyage des valeurs
# --------------------------------------------------------------------------
DATE_FORMATS = ("%d %b %Y", "%d %B %Y", "%B %d, %Y", "%b %d, %Y", "%Y-%m-%d", "%d/%m/%Y")


def parse_date(text: str) -> date | None:
    text = text.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    return None


def parse_rank(text: str) -> int | None:
    """'1st' -> 1, '5th' -> 5, 'Top 8' -> 8, '' -> None."""
    match = re.search(r"\d+", text or "")
    return int(match.group()) if match else None


def player_from_name(name: str) -> str:
    # Le titre est "Joueur – Héros – Événement"
    return re.split(r"\s+[–-]\s+", name, maxsplit=1)[0].strip()


# --------------------------------------------------------------------------
# Téléchargement
# --------------------------------------------------------------------------
def fetch(url: str, attempts: int = 4) -> str:
    for attempt in range(1, attempts + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError) as err:
            if isinstance(err, urllib.error.HTTPError) and err.code == 404:
                raise
            if attempt == attempts:
                raise
            wait = 2**attempt
            print(f"  erreur ({err}), nouvel essai dans {wait}s…", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError("unreachable")


def page_url(page: int) -> str:
    return LISTING_URL if page == 1 else f"{LISTING_URL}page/{page}/"


def collect(config: dict) -> list[dict]:
    wanted_format = config["format"].lower()
    since = date.fromisoformat(config["since"])
    max_pages = int(config.get("max_pages", 80))

    decks: list[dict] = []
    seen: set[str] = set()
    for page in range(1, max_pages + 1):
        url = page_url(page)
        print(f"Page {page} : {url}")
        try:
            rows = parse_listing(fetch(url))
        except urllib.error.HTTPError as err:
            if err.code == 404:
                print("  plus de pages.")
                break
            raise
        if not rows:
            break

        dated = [(parse_date(r["date_raw"]), r) for r in rows]
        unknown = [r["date_raw"] for d, r in dated if d is None]
        if unknown:
            print(f"  attention : dates illisibles {unknown[:3]}", file=sys.stderr)

        kept = 0
        for d, r in dated:
            if d is None or d < since:
                continue
            if r["format"].strip().lower() != wanted_format:
                continue
            key = r["url"] or f'{r["name"]}|{r["date_raw"]}'
            if key in seen:
                continue
            seen.add(key)
            decks.append(
                {
                    "date": d.isoformat(),
                    "player": player_from_name(r["name"]),
                    "hero": r["hero"].strip(),
                    "event": r["event"].strip(),
                    "event_url": r["event_url"],
                    "rank": parse_rank(r["rank_raw"]),
                    "country": r["country"].strip(),
                    "url": r["url"],
                }
            )
            kept += 1
        print(f"  {len(rows)} lignes, {kept} decklists {config['format']} retenues")

        # Le tableau est trié du plus récent au plus ancien : on s'arrête
        # dès qu'une page entière est antérieure à la date de départ.
        known = [d for d, _ in dated if d is not None]
        if known and max(known) < since:
            print("  page entièrement antérieure à la date de départ : arrêt.")
            break
        time.sleep(DELAY_SECONDS)
    else:
        print(f"Limite de {max_pages} pages atteinte.", file=sys.stderr)

    decks.sort(key=lambda d: (d["date"], -(d["rank"] or 999)), reverse=True)
    return decks


def main() -> int:
    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    decks = collect(config)
    if not decks:
        print(
            "Aucune decklist récupérée : on n'écrase pas les données. "
            "Vérifie config.json ou la page https://fabtcg.com/decklists/",
            file=sys.stderr,
        )
        return 1
    out = ROOT / "data" / "decklists.json"
    out.parent.mkdir(exist_ok=True)
    payload = {
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": LISTING_URL,
        "format": config["format"],
        "since": config["since"],
        "decklists": decks,
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(decks)} decklists écrites dans {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

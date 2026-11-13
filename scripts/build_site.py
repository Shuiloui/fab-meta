"""Construit le site statique à partir de data/decklists.json.

Calcule, pour chaque héros : nombre de decklists, part de la meta,
victoires (1re place) et présences en top 8. Écrit le tout dans site/.
"""

from __future__ import annotations

import html
import json
import shutil
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"
OUT = ROOT / "site"

MONTHS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]

EXTERNAL_LINKS = [
    ("fabtcgmeta", "https://fabtcgmeta.com/", "taux de victoire et matchups"),
    ("Fablazing", "https://fablazing.com/", "statistiques de tournois"),
    ("FaBrary", "https://fabrary.net/", "decklists de la communauté"),
    ("Decklists officielles", "https://fabtcg.com/decklists/", "la source de cette page"),
]


def fr_date(iso: str) -> str:
    d = date.fromisoformat(iso[:10])
    return f"{d.day} {MONTHS_FR[d.month - 1]} {d.year}"


def esc(value) -> str:
    return html.escape(str(value or ""), quote=True)


def link(url: str | None, text: str) -> str:
    if not url:
        return esc(text)
    return f'<a href="{esc(url)}" rel="noopener">{esc(text)}</a>'


def hero_stats(decks: list[dict]) -> list[dict]:
    stats: dict[str, dict] = defaultdict(
        lambda: {"decks": 0, "wins": 0, "top8": 0, "events": set()}
    )
    for d in decks:
        s = stats[d["hero"]]
        s["decks"] += 1
        s["events"].add(d["event"])
        if d["rank"] == 1:
            s["wins"] += 1
        if d["rank"] is not None and d["rank"] <= 8:
            s["top8"] += 1
    total = len(decks) or 1
    rows = [
        {
            "hero": hero,
            "decks": s["decks"],
            "share": 100 * s["decks"] / total,
            "wins": s["wins"],
            "top8": s["top8"],
            "events": len(s["events"]),
        }
        for hero, s in stats.items()
    ]
    rows.sort(key=lambda r: (-r["decks"], -r["wins"], -r["top8"], r["hero"]))
    return rows


def hero_table(rows: list[dict]) -> str:
    top_share = max((r["share"] for r in rows), default=1) or 1
    out = []
    for i, r in enumerate(rows, 1):
        width = 100 * r["share"] / top_share
        tip = (
            f'{r["hero"]} : {r["decks"]} decklists ({r["share"]:.1f} %), '
            f'{r["wins"]} victoire(s), {r["top8"]} top 8'
        )
        out.append(
            f'<tr title="{esc(tip)}">'
            f'<td class="num muted">{i}</td>'
            f'<td class="hero">{esc(r["hero"])}</td>'
            f'<td class="bar-cell" data-sort="{r["share"]:.4f}">'
            f'<div class="bar-wrap"><span class="bar-track"><span class="bar" style="width:{width:.1f}%"></span></span>'
            f'<span class="bar-label">{r["share"]:.1f} %</span></div></td>'
            f'<td class="num">{r["decks"]}</td>'
            f'<td class="num">{r["wins"]}</td>'
            f'<td class="num">{r["top8"]}</td>'
            f'<td class="num">{r["events"]}</td>'
            "</tr>"
        )
    return "\n".join(out)


def winners_list(decks: list[dict], limit: int = 15) -> str:
    winners = [d for d in decks if d["rank"] == 1][:limit]
    if not winners:
        return '<p class="muted">Aucune victoire publiée sur la période pour le moment.</p>'
    items = []
    for d in winners:
        items.append(
            "<li>"
            f'<span class="date">{esc(fr_date(d["date"]))}</span> '
            f'<strong>{esc(d["hero"])}</strong> '
            f'<span class="muted">par</span> {link(d["url"], d["player"])} '
            f'<span class="muted">à</span> {link(d["event_url"], d["event"])}'
            "</li>"
        )
    return "<ul class=\"winners\">" + "\n".join(items) + "</ul>"


def decklist_table(decks: list[dict]) -> str:
    out = []
    for d in decks:
        rank = f'{d["rank"]}' if d["rank"] is not None else "–"
        out.append(
            "<tr>"
            f'<td data-sort="{esc(d["date"])}">{esc(fr_date(d["date"]))}</td>'
            f'<td>{esc(d["hero"])}</td>'
            f'<td>{link(d["url"], d["player"])}</td>'
            f'<td>{link(d["event_url"], d["event"])}</td>'
            f'<td class="num" data-sort="{d["rank"] if d["rank"] is not None else 9999}">{rank}</td>'
            f'<td>{esc(d["country"])}</td>'
            "</tr>"
        )
    return "\n".join(out)


def build() -> int:
    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    data_file = ROOT / "data" / "decklists.json"
    if not data_file.exists():
        print("data/decklists.json manquant : lance d'abord scripts/fetch_decklists.py", file=sys.stderr)
        return 1
    data = json.loads(data_file.read_text(encoding="utf-8"))
    decks = data["decklists"]
    heroes = hero_stats(decks)
    fetched = datetime.fromisoformat(data["fetched_at"].replace("Z", "+00:00"))

    values = {
        "FORMAT": esc(config["format"]),
        "SINCE": esc(fr_date(config["since"])),
        "SINCE_LABEL": esc(config.get("since_label", "")),
        "SINCE_URL": esc(config.get("since_url", "")),
        "NEXT_BANLIST": esc(fr_date(config["next_banlist"])) if config.get("next_banlist") else "à annoncer",
        "UPDATED": esc(f'{fr_date(fetched.date().isoformat())} à {fetched:%H:%M} UTC'),
        "TOTAL_DECKS": str(len(decks)),
        "TOTAL_HEROES": str(len(heroes)),
        "TOTAL_EVENTS": str(len({d["event"] for d in decks})),
        "TOTAL_WINS": str(sum(1 for d in decks if d["rank"] == 1)),
        "HERO_ROWS": hero_table(heroes),
        "WINNERS": winners_list(decks),
        "DECK_ROWS": decklist_table(decks),
        "EXTERNAL_LINKS": "\n".join(
            f'<li>{link(url, name)} <span class="muted">– {esc(desc)}</span></li>'
            for name, url, desc in EXTERNAL_LINKS
        ),
        "YEAR": str(date.today().year),
    }

    page = (TEMPLATES / "index.html").read_text(encoding="utf-8")
    for key, value in values.items():
        page = page.replace("{{" + key + "}}", value)

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    (OUT / "index.html").write_text(page, encoding="utf-8")
    for asset in ("style.css", "app.js"):
        shutil.copy(TEMPLATES / asset, OUT / asset)
    shutil.copy(data_file, OUT / "decklists.json")
    print(f"Site généré dans site/ ({len(decks)} decklists, {len(heroes)} héros)")
    return 0


if __name__ == "__main__":
    sys.exit(build())

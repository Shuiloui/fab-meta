"""Tests rapides, sans réseau : python3 -m unittest discover tests"""

import json
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import fetch_decklists as fd  # noqa: E402


def row(country, date, name, url, event, fmt, hero, rank):
    return (
        f"<tr><td>{country}</td><td>{date}</td><td><a href='{url}'>{name}</a></td>"
        f"<td><a href='https://fabtcg.com/e/'>{event}</a></td><td>{fmt}</td><td>{hero}</td><td>{rank}</td></tr>"
    )


HEAD = (
    "<table><thead><tr><th>Country/Region</th><th>Date</th><th>Name</th><th>Event</th>"
    "<th>Format</th><th>Hero</th><th>Rank</th></tr></thead><tbody>"
)
PAGE1 = HEAD + "".join([
    row("Australia", "12 Nov 2026", "Jackie Rousseau &#8211; Aurora &#8211; Primed to Fight",
        "https://fabtcg.com/decklists/a/", "Primed to Fight", "Silver Age", "Aurora", ""),
    row("Slovenia", "08 Nov 2026", "Davorin Pokorn – Ira, Crimson Haze – Showdown",
        "https://fabtcg.com/decklists/b/", "Sunday Showdown: Paris 2026", "Silver Age", "Ira, Crimson Haze", "1st"),
    row("Canada", "07 Nov 2026", "Matt Muus – Teklovossen – Calling",
        "https://fabtcg.com/decklists/c/", "Calling: Paris 2026", "Classic Constructed", "Teklovossen", "1st"),
]) + "</tbody></table>"
PAGE2 = HEAD + "".join([
    row("France", "27 Oct 2026", "Léa X – Aurora – Showdown",
        "https://fabtcg.com/decklists/d/", "Sunday Showdown: Paris 2026", "Silver Age", "Aurora", "5th"),
    row("France", "20 Oct 2026", "Old – Aurora – Old",
        "https://fabtcg.com/decklists/e/", "Old event", "Silver Age", "Aurora", "1st"),
]) + "</tbody></table>"
PAGE3 = HEAD + row("France", "01 Oct 2026", "Older – Kano – x",
                   "https://fabtcg.com/decklists/f/", "x", "Silver Age", "Kano", "1st") + "</tbody></table>"


class FetchTests(unittest.TestCase):
    def test_parse_values(self):
        self.assertEqual(fd.parse_rank("1st"), 1)
        self.assertEqual(fd.parse_rank("Top 8"), 8)
        self.assertIsNone(fd.parse_rank(""))
        self.assertEqual(str(fd.parse_date("08 Nov 2026")), "2026-11-08")
        self.assertEqual(str(fd.parse_date("November 8, 2026")), "2026-11-08")

    def test_collect_filters_format_and_date(self):
        pages = {fd.page_url(1): PAGE1, fd.page_url(2): PAGE2, fd.page_url(3): PAGE3}
        config = {"format": "Silver Age", "since": "2026-10-26", "max_pages": 10}
        with mock.patch.object(fd, "fetch", side_effect=lambda u: pages[u]), \
                mock.patch.object(fd.time, "sleep"):
            decks = fd.collect(config)
        self.assertEqual([d["url"][-2] for d in decks], ["a", "b", "d"])
        self.assertEqual(decks[0]["player"], "Jackie Rousseau")
        self.assertEqual(decks[1]["hero"], "Ira, Crimson Haze")
        self.assertEqual(decks[1]["rank"], 1)
        self.assertIsNone(decks[0]["rank"])

    def test_no_table_raises(self):
        with self.assertRaises(ValueError):
            fd.parse_listing("<html><body>rien</body></html>")


if __name__ == "__main__":
    unittest.main()

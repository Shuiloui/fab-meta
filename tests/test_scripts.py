"""Tests rapides : python3 -m unittest discover tests"""

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_site as bs  # noqa: E402

HEADER = "date,heros,joueur,tournoi,place,pays,lien_decklist,lien_tournoi\n"


def write_csv(text: str) -> Path:
    tmp = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8")
    tmp.write(HEADER + text)
    tmp.close()
    return Path(tmp.name)


class LoadTests(unittest.TestCase):
    def test_reads_and_filters_by_date(self):
        path = write_csv(
            '2026-11-08,"Ira, Crimson Haze",Davorin,Showdown,1,Slovenia,https://a/,\n'
            "2026-11-12,Aurora,Jackie,Primed,,Australia,,\n"
            "2026-10-01,Kano,Old,Old event,1,France,,\n"
        )
        decks = bs.load_results(path, "2026-10-26")
        self.assertEqual([d["player"] for d in decks], ["Jackie", "Davorin"])
        self.assertEqual(decks[1]["hero"], "Ira, Crimson Haze")
        self.assertEqual(decks[1]["rank"], 1)
        self.assertIsNone(decks[0]["rank"])
        self.assertIsNone(decks[0]["url"])

    def test_reports_bad_lines(self):
        path = write_csv("12/11/2026,Aurora,Jackie,Primed,,,,\n2026-11-12,,Jackie,Primed,1er,,,\n")
        with self.assertRaises(bs.DataError) as ctx:
            bs.load_results(path, "2026-10-26")
        msg = str(ctx.exception)
        self.assertIn("ligne 2", msg)
        self.assertIn("ligne 3", msg)

    def test_stats(self):
        decks = [
            {"hero": "Aurora", "rank": 1, "event": "A"},
            {"hero": "Aurora", "rank": 9, "event": "B"},
            {"hero": "Kano", "rank": 3, "event": "A"},
            {"hero": "Kano", "rank": None, "event": "A"},
        ]
        stats = {r["hero"]: r for r in bs.hero_stats(decks)}
        self.assertEqual(stats["Aurora"]["wins"], 1)
        self.assertEqual(stats["Aurora"]["top8"], 1)
        self.assertEqual(stats["Kano"]["events"], 1)
        self.assertAlmostEqual(stats["Kano"]["share"], 50.0)

    def test_repository_csv_is_valid(self):
        config = bs.json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
        bs.load_results(ROOT / "data" / "resultats.csv", config["since"])


if __name__ == "__main__":
    unittest.main()

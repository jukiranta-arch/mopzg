import os
import random
import tempfile
import unittest

from whodunit.generate import (BOOK_BALANCE, BOOK_CLUES, CAST, PAGE_LEVEL, SAMPLE_CLUES, build_register,
                               generate_any)
from whodunit.model import READINGS, Register, catalogue, letters, solve
from whodunit.names import CHARACTERS, FIRST, PLACES_INDOOR, PLACES_OUTDOOR, ROYALS

SAMPLE = dict(n_pages=30, per_page=(270, 300), n_chapters=4, n_indoor=2, clue_keys=SAMPLE_CLUES,
              balance=dict(BOOK_BALANCE, page_level_keep=(0.02, 0.2)))


def reg_of(*pages, chapters=None, indoor=None, cast=()):
    return Register([list(p) for p in pages], chapters or [("The Ballroom", 0)],
                    indoor={0} if indoor is None else indoor, cast=set(cast)).index()


class ClueTests(unittest.TestCase):
    def setUp(self):
        self.cat = catalogue(cast_window=2)

    def check(self, key, name, expected):
        self.assertEqual(self.cat[key].test(reg_of([name]), 0), expected, (key, name))

    def test_word_clues(self):
        self.check("odd_consonants", "Lucy", True)          # L, C, Y: Y is a consonant
        self.check("odd_consonants", "Anna", False)
        self.check("even_vowels", "Lynn", True)             # no vowels counts as even
        self.check("even_vowels", "Tim", False)
        self.check("ends_consonant", "Lucy", True)
        self.check("ends_consonant", "Anna", False)
        self.check("double_letter", "Bella", True)
        self.check("double_letter", "Tom", False)
        self.check("first_half", "Mabel", True)
        self.check("first_half", "Nora", False)
        self.check("last_two_rising", "Lucy", True)
        self.check("last_two_rising", "Ann", False)

    def test_place_clues(self):
        cat = self.cat
        r = reg_of(["Ada", "Snow White", "Bo"], ["Cy", "Dee", "Eve", "Fay"], cast={"Snow White"})
        near = cat["near_character"]
        self.assertTrue(near.test(r, 0))                    # within 2 names
        self.assertTrue(near.test(r, 3))                    # counts across a page break
        self.assertFalse(near.test(r, 4))
        self.assertFalse(near.test(r, 1))                   # a character isn't near itself
        r = reg_of(["Ann"], ["Hansel"], ["Bo"], ["Cy"], ["Gretel"], ["Di"])
        between = cat["between_hansel_gretel"]
        self.assertEqual([between.test(r, i) for i in range(6)], [False, False, True, True, False, False])
        r = reg_of(["Ann", "Snow Queen"], ["Bo", "Cy"])
        self.assertTrue(cat["royal_on_page"].test(r, 0))    # any name with the word Queen in it
        self.assertFalse(cat["royal_on_page"].test(r, 2))
        r.set_reading({"royal_first_word": True})
        self.assertFalse(cat["royal_on_page"].test(r, 0))   # the misreading the generator also checks
        r = reg_of(["Kit", "Zoe Kane", "Zoe"])
        self.assertTrue(cat["key_letter"].test(r, 1))       # key letter K
        self.assertFalse(cat["key_letter"].test(r, 2))
        r = reg_of(["Ann", "Papa Bear", "Mama Bear", "Baby Bear"], ["Bo"], ["Cy", "Papa Bear", "Mama Bear"],
                   chapters=[("The Ballroom", 0), ("The Orchard", 2)])
        self.assertTrue(cat["three_bears"].test(r, 0))
        self.assertFalse(cat["three_bears"].test(r, 5))     # two bears only
        r = reg_of(["Ann"], ["Bo"], chapters=[("The Ballroom", 0), ("The Orchard", 1)], indoor={0})
        self.assertEqual([cat["chapter_indoors"].test(r, i) for i in range(2)], [True, False])

    def test_page_start_with_duplicate_names(self):
        r = reg_of(["Ann", "Bo"], ["Ann", "Cy", "Di"])
        self.assertEqual(r.page_start, [0, 2])


class NameTests(unittest.TestCase):
    def test_no_titles_and_no_clashes(self):
        self.assertFalse({"Mr", "Mrs", "Miss", "Dr", "Sir", "Lady"} & set(FIRST))
        self.assertTrue(all(len(n.split()) == 1 for n in FIRST))            # guests are single first names
        self.assertFalse(set(FIRST) & set(CHARACTERS + ROYALS))
        self.assertFalse(set(PLACES_INDOOR) & set(PLACES_OUTDOOR))


class GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg, cls.clues, cls.sol = generate_any(range(1, 60), **SAMPLE)

    def test_puzzle_has_exactly_two_suspects_under_every_reading(self):
        reg, clues, sol = self.reg, self.clues, self.sol
        for reading in READINGS:                             # the same answer whatever slip a solver makes
            self.assertEqual(len(solve(reg, clues, reading)[0]), 2, reading)
        alive, counts = solve(reg, clues)
        self.assertEqual(sorted(reg.flat[i] for i in alive), sorted(s["name"] for s in sol["suspects"]))
        for s in sol["suspects"]:
            self.assertIn(s["name"], FIRST)                  # a plain first name, never a character
        a, b = (len(letters(s["name"])) for s in sol["suspects"])
        self.assertNotEqual(a, b)
        self.assertEqual(len(letters(sol["killer"])), max(a, b))
        before = sol["total_names"]
        for after in counts:                                 # every clue does real work
            self.assertLessEqual(after, before * 0.97)
            before = after

    def test_balance_no_knockout_page_clue(self):
        for c in self.clues:
            if c.key in PAGE_LEVEL:
                self.assertGreaterEqual(self.sol["standalone"][c.key], 0.30, c.key)
        self.assertEqual([cp["names"] for cp in self.sol["checkpoints"]], self.sol["counts"])

    def test_suspects_in_indoor_chapters_with_the_bears_optional(self):
        reg = self.reg
        for i in self.sol["pair"]:
            self.assertIn(reg.chapter_of_page[reg.page_of[i]], reg.indoor)

    def test_landmarks_survive_placement(self):
        from whodunit.generate import GenerationError
        for seed in range(1, 50):                            # some seeds can't place the suspect pages
            try:
                reg = build_register(random.Random(seed), n_pages=30, per_page=(270, 300), n_chapters=4,
                                     n_indoor=2)
                break
            except GenerationError:
                continue
        self.assertEqual(reg.flat.count("Hansel"), 1)
        self.assertEqual(reg.flat.count("Gretel"), 1)
        self.assertGreaterEqual(reg.flat.count("Big Bad Wolf"), 2)
        self.assertTrue(set(reg.flat) & set(ROYALS))
        self.assertTrue(all(n in FIRST or n in CAST for n in reg.flat))


try:
    import reportlab  # noqa: F401
    HAVE_REPORTLAB = True
except ImportError:
    HAVE_REPORTLAB = False


@unittest.skipUnless(HAVE_REPORTLAB, "reportlab not installed")
class RenderTests(unittest.TestCase):
    def test_renders_sample(self):
        from whodunit.render import render
        reg, clues, sol = generate_any(range(1, 60), **SAMPLE)
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "s.pdf")
            n = render(reg, clues, sol, path)
            with open(path, "rb") as fh:
                pdf = fh.read()
            self.assertIn(b"/FontFile2", pdf)                    # fonts embedded, as KDP requires
            for base14 in (b"/Helvetica", b"/Times-Roman", b"/Times-Bold"):
                self.assertNotIn(base14, pdf)
            self.assertEqual(n % 2, 0)                             # even page count for print
            try:
                import pymupdf
            except ImportError:
                return
            doc = pymupdf.open(path)
            self.assertEqual(doc.page_count, n)
            text = [pg.get_text() for pg in doc]
            for section in ("The Palace", "Who’s Who", "The Clues", "CHECKPOINT A", "CLUE CARD",
                            "The Final Deduction", "Hints"):
                self.assertTrue(any(section in t for t in text), section)
            self.assertFalse(any("Mr " in t or "Mrs " in t for t in text))   # no titles anywhere
            killer = sol["killer"]
            stop = next(i for i, t in enumerate(text) if t.strip().startswith("Stop!"))
            self.assertEqual(stop % 2, 0)                          # a right-hand page (0-based even)
            self.assertIn("It was %s." % killer, text[stop + 1])   # the solution is on its back
            clue_pages = [t for t in text[:stop] if "Rule:" in t or "Example:" in t or "Hints" in t]
            self.assertFalse(any(killer in t for t in clue_pages))  # examples and hints never name a suspect
            import subprocess
            import sys
            out = subprocess.run([sys.executable, "-m", "whodunit.check_pdf", path], capture_output=True,
                                 text=True, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.assertEqual(out.returncode, 0, out.stdout + out.stderr)   # solved from the PDF alone


if __name__ == "__main__":
    unittest.main()

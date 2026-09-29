import os
import tempfile
import unittest

from whodunit.generate import build_register, generate_any, random_name
from whodunit.model import PERSON_TITLES, READINGS, Register, catalogue, letters, solve, words
from whodunit.names import FEMALE, FEMALE_TITLES, MALE, MALE_TITLES

import random


def reg_of(*pages, chapters=None):
    return Register([list(p) for p in pages], chapters or [("", 0)]).index()


class ClueTests(unittest.TestCase):
    def setUp(self):
        self.cat = catalogue(queen_window=2)

    def check(self, key, name, expected):
        self.assertEqual(self.cat[key].test(reg_of([name]), 0), expected, (key, name))

    def test_word_clues(self):
        self.check("odd_consonants", "Lucy", True)          # L, C, Y: Y is a consonant
        self.check("odd_consonants", "Ada", True)
        self.check("odd_consonants", "Mrs Ada", True)       # titles don't count: checked as Ada
        self.check("first_half", "Lady Nell", False)        # begins with N once the title is dropped
        self.check("even_vowels", "Tim", False)
        self.check("even_vowels", "Lynn", True)             # no vowels counts as even
        self.check("ends_consonant", "Mrs O'Neil", True)    # apostrophe ignored
        self.check("double_letter", "Bella", True)
        self.check("double_letter", "Jess Smith", True)
        self.check("double_letter", "Tom Mason", False)     # letters split by a space don't count
        self.check("first_half", "Mabel", True)
        self.check("first_half", "Nora", False)
        self.check("last_two_rising", "Lucy", True)
        self.check("last_two_rising", "Ann", False)

    def test_place_clues(self):
        cat = self.cat
        r = reg_of(["Ada", "Queen Ivy", "Bo"], ["Cy", "Dee", "Eve", "Fay"])
        near = cat["near_queen"]
        self.assertTrue(near.test(r, 0))                    # within 2 names
        self.assertTrue(near.test(r, 3))                    # counts across a page break
        self.assertFalse(near.test(r, 4))
        self.assertFalse(near.test(r, 1))                   # a Queen isn't near herself
        self.assertFalse(cat["even_page"].test(r, 0))
        self.assertTrue(cat["even_page"].test(r, 3))
        r = reg_of(["Ann"], ["Hansel"], ["Bo"], ["Cy"], ["Gretel"], ["Di"])
        between = cat["between_hansel_gretel"]
        self.assertEqual([between.test(r, i) for i in range(6)], [False, False, True, True, False, False])
        r = reg_of(["Ann", "Robin King", "Evil Queen"], ["Bo", "Cy"])
        self.assertTrue(cat["king_and_queen"].test(r, 0))   # any name with the word King / Queen in it
        self.assertFalse(cat["king_and_queen"].test(r, 3))
        r.set_reading({"titled_only": True})
        self.assertFalse(cat["king_and_queen"].test(r, 0))  # the misreading the generator also checks
        r.set_reading({})
        r = reg_of(["Ann"], ["Bo"], ["Cy"])
        self.assertEqual([cat["odd_page"].test(r, i) for i in range(3)], [True, False, True])
        r = reg_of(["Mr Kite", "Zoe Kane", "Zoe"])
        self.assertTrue(cat["key_letter"].test(r, 1))       # key letter K: the title Mr is skipped
        self.assertFalse(cat["key_letter"].test(r, 2))

    def test_page_start_with_duplicate_names(self):
        r = reg_of(["Ann", "Bo"], ["Ann", "Cy", "Di"])
        self.assertEqual(r.page_start, [0, 2])
        self.assertEqual(r.first_index_on_page(1), 2)


class GeneratorTests(unittest.TestCase):
    def test_puzzle_has_exactly_two_suspects(self):
        reg, clues, sol = generate_any(range(1, 200), n_pages=10, per_page=(200, 225), n_chapters=3)
        for reading in READINGS:                             # the same answer whatever slip a solver makes
            self.assertEqual(len(solve(reg, clues, reading)[0]), 2, reading)
        alive, counts = solve(reg, clues)
        self.assertEqual(len(alive), 2)
        for s in sol["suspects"]:
            self.assertNotIn(words(s["name"])[0], PERSON_TITLES)
        self.assertEqual(sorted(reg.flat[i] for i in alive), sorted(s["name"] for s in sol["suspects"]))
        self.assertEqual({s["chapter"] for s in sol["suspects"]}.__len__(), 2)
        a, b = (len(letters(s["name"])) for s in sol["suspects"])
        self.assertNotEqual(a, b)
        self.assertEqual(len(letters(sol["killer"])), max(a, b))
        before = sol["total_names"]
        for after in counts:                                 # every clue does real work
            self.assertLessEqual(after, before * 0.97)
            before = after

    def test_landmarks_survive_placement(self):
        reg = build_register(random.Random(5), n_pages=12, per_page=(200, 225), n_chapters=3)
        self.assertEqual(reg.flat.count("Hansel"), 1)
        self.assertEqual(reg.flat.count("Gretel"), 1)
        self.assertGreaterEqual(reg.flat.count("Big Bad Wolf"), 2)

    def test_titles_match_first_names(self):
        rng = random.Random(1)
        for _ in range(5000):
            w = words(random_name(rng))
            if len(w) == 3 and w[0] in MALE_TITLES:
                self.assertNotIn(w[1], FEMALE)
            if len(w) == 3 and w[0] in FEMALE_TITLES:
                self.assertNotIn(w[1], MALE)


try:
    import reportlab  # noqa: F401
    HAVE_REPORTLAB = True
except ImportError:
    HAVE_REPORTLAB = False


@unittest.skipUnless(HAVE_REPORTLAB, "reportlab not installed")
class RenderTests(unittest.TestCase):
    def test_renders_sample(self):
        from whodunit.render import render
        reg, clues, sol = generate_any(range(1, 200), n_pages=10, per_page=(200, 225), n_chapters=3)
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "s.pdf")
            n = render(reg, clues, sol, path)
            self.assertTrue(os.path.getsize(path) > 10000)
            with open(path, "rb") as fh:
                pdf = fh.read()
            self.assertIn(b"/FontFile2", pdf)                    # fonts embedded, as KDP requires
            for base14 in (b"/Helvetica", b"/Times-Roman", b"/Times-Bold"):
                self.assertNotIn(base14, pdf)
            self.assertGreater(n, 10)


if __name__ == "__main__":
    unittest.main()

import os
import random
import tempfile
import unittest

from village.book import (LETTER_BY_KEY, READINGS, THEMES, Ledger, chain_clue, generate_case, hunt_clues, signature,
                          solve, survivors_all_readings, validate, verdicts)


def led(*pages, chapters=None):
    return Ledger([list(p) for p in pages], chapters or [("A", 0)]).index()


class ClueTests(unittest.TestCase):
    def test_letter_clues(self):
        expect = {
            "odd_consonants": {"Ian Scott": True, "Rosa": False},
            "even_consonants": {"Rosa": True, "Ian Scott": False},
            "ends_consonant": {"Mark": True, "Rosa": False},
            "ends_vowel": {"Rosa": True, "Ian Scott": False},
            "double_letter": {"Nora Bell": True, "Cara Anders": False},
            "no_double_letter": {"Cara Anders": True, "Nora Bell": False},
            "a_to_m": {"Ada": True, "Nora": False},
            "n_to_z": {"Nora": True, "Ada": False},
            "even_vowels": {"Rosa": True, "Rob": False},
            "odd_vowels": {"Rob": True, "Rosa": False},
            "full_name": {"Ada Finch": True, "Rosa": False},
        }
        for key, cases in expect.items():
            for name, want in cases.items():
                self.assertEqual(verdicts(LETTER_BY_KEY[key], name), {want}, (key, name))
        # Y is a consonant, but the misreading that treats it as a vowel is tracked, so names ending in Y
        # are never safe examples or safe answers for these clues
        self.assertEqual(verdicts(LETTER_BY_KEY["ends_consonant"], "Lucy"), {True, False})

    def test_hunt_clues(self):
        t = THEMES[0]
        h = {c.key: c for c in hunt_clues(t)}
        pages = [["Ann", "Romeo", "Tom Sawyer"], ["Meg", "Jo", "Anne Shirley", "Gilbert Blythe"],
                 ["Beth", "Amy", "Athos"], ["Di", "Anne Shirley"], ["Ed", "Juliet"]]
        l = led(*pages, chapters=[("A", 0), ("B", 2)])
        on = lambda key, r={}: sorted({l.page_of[i] for i, v in enumerate(h[key].test(l, r)) if v})
        self.assertEqual(on("near_page"), [0, 1])
        self.assertEqual(on("near_page", {"near_page_only": True}), [0])
        self.assertEqual(on("group"), [0, 1, 2, 3, 4])
        self.assertEqual(on("between"), [1, 2, 3])
        self.assertEqual(on("between", {"between_inclusive": True}), [0, 1, 2, 3, 4])
        self.assertEqual(on("pair"), [1])
        self.assertEqual(on("pair", {"pair_either": True}), [1, 3])
        near = h["scattered"].test(l, {"window": -9})
        self.assertEqual([l.flat[i] for i, v in enumerate(near) if v], ["Amy", "Di"])

    def test_chain_clue(self):
        c = chain_clue(THEMES[0], "Ralph Moon")
        self.assertIn("bookstore killer", c.text)
        self.assertEqual(verdicts(c, "Anna North"), {True})
        self.assertEqual(verdicts(c, "Ada Lee"), {False})


class CaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for seed in range(10):
            try:
                cls.case = generate_case(THEMES[1], random.Random(seed), "H")
            except ValueError:
                continue
            if not validate(cls.case):
                return
        raise AssertionError("no valid case")

    def test_one_killer_under_every_reading(self):
        c = self.case
        for r in READINGS:
            self.assertEqual(solve(c.ledger, c.clues, r), [c.killer])
        self.assertTrue(c.ledger.flat[c.killer].startswith("H"))

    def test_check_line(self):
        c = self.case
        self.assertEqual(signature(c.ledger.flat[c.killer]), c.check)
        for cl in c.clues:
            near = survivors_all_readings(c.ledger, c.clues, skip=cl.key) - {c.killer}
            self.assertFalse([i for i in near if signature(c.ledger.flat[i]) == c.check])


@unittest.skipUnless(os.environ.get("BOOK_PDF"), "set BOOK_PDF to a rendered book to check it")
class RenderedBookTests(unittest.TestCase):
    def test_book_pdf(self):
        from village.check_book import main
        self.assertEqual(main(os.environ["BOOK_PDF"]), 0)


if __name__ == "__main__":
    unittest.main()

import os
import tempfile
import unittest

from village.case import (BEATLES, CLUES, MARCH, READINGS, RESERVED, Ledger, generate_valid, signature, solve,
                          survivors_all_readings, validate)


def led(*pages, chapters=None):
    return Ledger([list(p) for p in pages], chapters or [("The Tea Tent", 0)]).index()


def by_key(key):
    return next(c for c in CLUES if c.key == key)


class ClueTests(unittest.TestCase):
    def test_letter_clues(self):
        l = led(["Hope", "Lucy", "Rosa", "Jade", "Nora", "Cody"])
        self.assertEqual(by_key("ends_vowel").test(l, {}), [True, False, True, True, True, False])
        self.assertEqual(by_key("ends_vowel").test(l, {"y_vowel": True})[1], True)   # the misreading
        self.assertEqual(by_key("even_vowels").test(l, {}), [True, False, True, True, True, False])
        self.assertEqual(by_key("no_jam").test(l, {}), [True, True, False, False, False, True])
        self.assertEqual(by_key("first_a_to_m").test(l, {}), [True, True, False, True, False, True])

    def test_hunt_clues(self):
        pages = [["Ann", "Charlotte", "Emily", "Anne"], ["Bo", "John", "Paul", "George", "Ringo"],
                 ["Cy", "Athos"], ["Di", "Meg", "Jo", "Beth", "Amy"], ["Ed", "Bonnie", "Clyde"]]
        l = led(*pages, chapters=[("A", 0), ("B", 2)])
        beatles = by_key("beatles").test(l, {})
        self.assertTrue(all(beatles[:9]) and not any(beatles[9:]))          # chapter A only
        sisters = by_key("sisters").test(l, {})
        self.assertEqual([l.page_of[i] for i, v in enumerate(sisters) if v], [1] * 5 + [2] * 2)
        inclusive = by_key("sisters").test(l, {"between_inclusive": True})
        self.assertEqual(sum(inclusive), len(l.flat) - 3)                    # all but the last page
        outlaws = by_key("outlaws").test(l, {})
        self.assertEqual({l.page_of[i] for i, v in enumerate(outlaws) if v}, {3, 4})
        musk = by_key("musketeers").test(l, {"window": -9})                  # within 1 name
        self.assertEqual([l.flat[i] for i, v in enumerate(musk) if v], ["Cy", "Di"])  # across a page break


class GenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.case = generate_valid()

    def test_one_answer_under_every_reading(self):
        c = self.case
        for r in READINGS:
            self.assertEqual(solve(c.ledger, CLUES, r), [c.killer])
        self.assertEqual(validate(c), [])

    def test_check_line_confirms_only_the_killer(self):
        c = self.case
        self.assertEqual(signature(c.ledger.flat[c.killer]), c.check)
        for cl in CLUES:
            near = survivors_all_readings(c.ledger, skip=cl.key) - {c.killer}
            self.assertFalse([i for i in near if signature(c.ledger.flat[i]) == c.check], cl.key)

    def test_landmarks(self):
        l = self.case.ledger
        self.assertEqual(len(l.runs(BEATLES)), 2)
        self.assertEqual(len(l.runs(MARCH)), 1)
        self.assertNotIn(l.flat[self.case.killer], RESERVED)
        self.assertTrue(all(n.isalpha() for n in l.flat))                    # plain A-Z names only

    def test_no_knockout_hunt_clue(self):
        alone = self.case.stats["alone"]
        for key in ("beatles", "sisters", "outlaws"):
            self.assertTrue(0.3 <= alone[key] <= 0.7, (key, alone[key]))


try:
    import pymupdf  # noqa: F401
    import reportlab  # noqa: F401
    HAVE_PDF = True
except ImportError:
    HAVE_PDF = False


@unittest.skipUnless(HAVE_PDF, "reportlab and pymupdf not installed")
class PdfTests(unittest.TestCase):
    def test_pdf_solves_from_its_own_text(self):
        from village.__main__ import main as build
        from village.check_pdf import main as check
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "case.pdf")
            build([out])
            self.assertEqual(check(out), 0)


if __name__ == "__main__":
    unittest.main()

import os
import tempfile
import unittest

from village.case import (CLUES, LANDMARKS, READINGS, Ledger, generate_valid, letters, signature, solve,
                          survivors_all_readings, validate)


def led(*pages, chapters=None):
    return Ledger([list(p) for p in pages], chapters or [("The Tea Tent", 0)]).index()


def by_key(key):
    return next(c for c in CLUES if c.key == key)


class ClueTests(unittest.TestCase):
    def test_letter_clues(self):
        l = led(["Ian Scott", "Lucy", "Rosa", "Ada Finch", "Nora Bell"])
        self.assertEqual(by_key("odd_consonants").test(l, {}), [True, True, False, True, True])
        self.assertEqual(by_key("odd_consonants").test(l, {"y_vowel": True})[1], False)   # the misreading
        self.assertEqual(by_key("ends_consonant").test(l, {}), [True, True, False, True, True])
        self.assertEqual(by_key("double_letter").test(l, {}), [True, False, False, False, True])
        self.assertFalse(by_key("double_letter").test(led(["Cara Anders"]), {})[0])   # split by a space
        self.assertEqual(by_key("a_to_m").test(l, {}), [True, True, False, True, False])

    def test_hunt_clues(self):
        pages = [["Ann", "Romeo", "Robin Hood"], ["John", "Paul", "Bonnie", "Clyde"], ["George", "Ringo", "Athos"],
                 ["Di", "Bonnie"], ["Ed", "Juliet"]]
        l = led(*pages, chapters=[("A", 0), ("B", 2)])
        on = lambda key, r={}: sorted({l.page_of[i] for i, v in enumerate(by_key(key).test(l, r)) if v})
        self.assertEqual(on("robin"), [0, 1])
        self.assertEqual(on("robin", {"robin_page_only": True}), [0])
        self.assertEqual(on("beatles"), [0, 1, 2, 3, 4])                  # neither chapter has all four
        self.assertEqual(on("romeo_juliet"), [1, 2, 3])
        self.assertEqual(on("romeo_juliet", {"between_inclusive": True}), [0, 1, 2, 3, 4])
        self.assertEqual(on("bonnie_clyde"), [1])
        self.assertEqual(on("bonnie_clyde", {"bonnie_or_clyde": True}), [1, 3])
        near = by_key("musketeers").test(l, {"window": -9})                # within 1 name
        self.assertEqual([l.flat[i] for i, v in enumerate(near) if v], ["Ringo", "Di"])   # across a page break
        l2 = led(["John", "Paul", "George", "Ringo"], ["Ann"], chapters=[("A", 0), ("B", 1)])
        self.assertEqual(by_key("beatles").test(l2, {}), [False] * 4 + [True])


class GenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.case = generate_valid()

    def test_two_suspects_under_every_reading(self):
        c = self.case
        for r in READINGS:
            self.assertEqual(solve(c.ledger, CLUES, r), sorted([c.killer, c.innocent]))
        self.assertEqual(validate(c), [])

    def test_final_deduction_and_check_line(self):
        c, l = self.case, self.case.ledger
        self.assertGreaterEqual(len(letters(l.flat[c.killer])) - len(letters(l.flat[c.innocent])), 2)
        self.assertEqual(signature(l.flat[c.killer]), c.check)
        for cl in CLUES:
            near = survivors_all_readings(l, skip=cl.key) - {c.killer}
            self.assertFalse([i for i in near if signature(l.flat[i]) == c.check], cl.key)

    def test_suspects(self):
        c, l = self.case, self.case.ledger
        a, b = l.flat[c.killer], l.flat[c.innocent]
        self.assertNotIn(a, LANDMARKS)
        self.assertFalse(set(a.split()) & set(b.split()))                  # no shared first name or surname
        self.assertNotEqual(l.chapter_of_page[l.page_of[c.killer]], l.chapter_of_page[l.page_of[c.innocent]])


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

import os
import tempfile
import unittest

from village.case import (CLUES, LANDMARKS, READINGS, Ledger, generate_valid, signature, solve,
                          survivors_all_readings, validate)


def led(*pages, chapters=None):
    return Ledger([list(p) for p in pages], chapters or [("Mystery & Crime", 0)]).index()


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
        pages = [["Ann", "Romeo", "Tom Sawyer"], ["Meg", "Jo", "Anne Shirley", "Gilbert Blythe"],
                 ["Beth", "Amy", "Athos"], ["Di", "Anne Shirley"], ["Ed", "Juliet"]]
        l = led(*pages, chapters=[("A", 0), ("B", 2)])
        on = lambda key, r={}: sorted({l.page_of[i] for i, v in enumerate(by_key(key).test(l, r)) if v})
        self.assertEqual(on("tom"), [0, 1])
        self.assertEqual(on("tom", {"tom_page_only": True}), [0])
        self.assertEqual(on("march"), [0, 1, 2, 3, 4])                    # neither chapter has all four
        self.assertEqual(on("romeo_juliet"), [1, 2, 3])
        self.assertEqual(on("romeo_juliet", {"between_inclusive": True}), [0, 1, 2, 3, 4])
        self.assertEqual(on("anne_gilbert"), [1])
        self.assertEqual(on("anne_gilbert", {"anne_or_gilbert": True}), [1, 3])
        near = by_key("musketeers").test(l, {"window": -9})                # within 1 name
        self.assertEqual([l.flat[i] for i, v in enumerate(near) if v], ["Amy", "Di"])   # across a page break
        l2 = led(["Meg", "Jo", "Beth", "Amy"], ["Ann"], chapters=[("A", 0), ("B", 1)])
        self.assertEqual(by_key("march").test(l2, {}), [False] * 4 + [True])


class GenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.case = generate_valid()

    def test_one_killer_under_every_reading(self):
        c = self.case
        for r in READINGS:
            self.assertEqual(solve(c.ledger, CLUES, r), [c.killer])
        self.assertEqual(validate(c), [])

    def test_check_line_confirms_only_the_killer(self):
        c, l = self.case, self.case.ledger
        self.assertEqual(signature(l.flat[c.killer]), c.check)
        for cl in CLUES:
            near = survivors_all_readings(l, skip=cl.key) - {c.killer}
            self.assertFalse([i for i in near if signature(l.flat[i]) == c.check], cl.key)

    def test_killer_is_an_ordinary_customer(self):
        self.assertNotIn(self.case.ledger.flat[self.case.killer], LANDMARKS)


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

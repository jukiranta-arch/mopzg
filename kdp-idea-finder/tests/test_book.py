import os
import random
import unittest

from village import clues as C
from village.book import (READINGS, Ledger, generate_case, landmark_risks, signature, solve, survivors_all_readings,
                          validate, verdicts)
from village.namepool import FIRST_NAMES, SURNAMES
from village.plans import PLANS


def led(*pages, chapters=None, first_page_no=1):
    return Ledger([list(p) for p in pages], chapters or [("A", 0)], first_page_no).index()


def on(clue, l, r=None):
    return sorted({l.page_of[i] for i, v in enumerate(clue.test(l, r or {})) if v})


class WordClueTests(unittest.TestCase):
    def check(self, clue, yes, no):
        for n in yes:
            self.assertEqual(verdicts(clue, n), {True}, (clue.key, n))
        for n in no:
            self.assertEqual(verdicts(clue, n), {False}, (clue.key, n))

    def test_word_clues(self):
        self.check(C.odd_consonants(), ["Ian Scott"], ["Rosa"])
        self.check(C.ends_consonant(), ["Mark"], ["Rosa"])
        self.check(C.double_letter(), ["Nora Bell"], ["Cara Anders"])
        self.check(C.no_double_letter("first"), ["Nora Bell"], ["Bella Cruz"])
        self.check(C.last_two_in_order(), ["Marlow"], ["Bella", "Ann"])
        self.check(C.none_of("JQ"), ["Ada Finch"], ["Jo Smith"])
        self.check(C.contains("R"), ["Rosa"], ["Ada"])
        self.check(C.surname_longer(), ["Ada Finchley"], ["Rosalind Cole", "Rosa"])
        self.check(C.first_at_least(5), ["Rosie Lee"], ["Ada Lovelace"])
        self.check(C.whole_at_most(13), ["Ada Finch"], ["Bartholomew Smith"])
        self.check(C.initial_in_surname(), ["Ada Baker"], ["Ada Finch", "Ada"])
        self.check(C.repeated_letter("surname"), ["Ada Ellison"], ["Ada Finch"])
        self.check(C.all_letters_different(), ["Ruth Long"], ["Ada"])
        self.check(C.at_least_vowels(4), ["Amelia"], ["Rosa"])
        self.check(C.surname_begins_consonant(), ["Ada Finch"], ["Ada Ellison", "Ada"])
        self.check(C.alphabet_neighbours(), ["Stella", "Edith"], ["Rosa"])
        self.check(C.even_length(), ["Rosa"], ["Ada"])
        # names ending in Y are never safe either way: one misreading treats Y as a vowel
        self.assertEqual(verdicts(C.ends_consonant(), "Lucy"), {True, False})

    def test_chain_clues(self):
        self.check(C.chain_last_letter("bookstore", "Ralph Moon"), ["Anna North"], ["Ada Lee"])
        self.check(C.chain_first_letter_of_surname("bakery", "Ada Moon"), ["Emma"], ["Ada"])
        self.check(C.chain_same_first_length("diner", "Rosa Lee"), ["Ruth Long"], ["Ada Long"])
        self.check(C.chain_shares_no_letter("inn", "Ada"), ["Rosa Long"], ["Rosa Baker", "Rosa"])


class HuntClueTests(unittest.TestCase):
    def test_page_clues(self):
        l = led(["Romeo", "Tom Sawyer"], ["Ann"], ["Bo"], ["Cy", "Juliet"], chapters=[("A", 0), ("B", 2)])
        self.assertEqual(on(C.near_page("Tom Sawyer"), l), [0, 1])
        self.assertEqual(on(C.near_page("Tom Sawyer"), l, {"near_page_only": True}), [0])
        self.assertEqual(on(C.between("Romeo", "Juliet"), l), [1, 2])
        self.assertEqual(on(C.between("Romeo", "Juliet"), l, {"between_inclusive": True}), [0, 1, 2, 3])
        self.assertEqual(on(C.within_pages("Romeo", 2), l), [0, 1, 2])
        self.assertEqual(on(C.beyond_pages("Romeo", 2), l), [3])

    def test_facing_and_before(self):
        # pages numbered 1-4: page 1 faces nothing, 2 faces 3
        l = led(["Ann"], ["Queen"], ["Bo"], ["Cy"])
        self.assertEqual(on(C.facing_page("Queen"), l), [2])
        self.assertEqual(on(C.page_before(("Queen",), "a Queen"), l), [2])
        self.assertEqual(on(C.page_before(("Queen",), "a Queen"), l, {"before_after_flip": True}), [0])

    def test_chapter_clues(self):
        l = led(["Lewis", "Ann"], ["Bo", "Clark"], ["Cy", "Ben"], ["Ben", "Di"], chapters=[("A", 0), ("B", 2)])
        self.assertEqual(on(C.duo_chapters_not((("Lewis", "Clark"),), "a pair"), l), [2, 3])
        self.assertEqual(on(C.chapter_exactly_twice("Ben"), l), [2, 3])
        self.assertEqual(on(C.in_chapter_with("Clark"), l), [0, 1])
        self.assertEqual(on(C.not_chapter_edge(), led(*[["x"]] * 4, chapters=[("A", 0)])), [1, 2])

    def test_spot_clues(self):
        l = led(["Kim", "Mark", "Ann", "Zed"])
        self.assertEqual(C.first_letter_of_page().test(l, {}), [True, True, False, False])
        self.assertEqual(C.flank().test(l, {}), [False, False, True, False])   # Mark < Zed around Ann
        self.assertEqual(C.initial_of_page_last().test(l, {}), [False, False, False, True])
        self.assertEqual(C.no_letter_with_page_first().test(l, {}), [False, False, True, True])   # Mark shares M with Kim

    def test_one_not_both(self):
        l = led(["Napoleon"], ["Napoleon", "Josephine"], ["Josephine"], ["Ann"])
        self.assertEqual(on(C.one_not_both("Napoleon", "Josephine"), l), [0, 2])
        self.assertEqual(on(C.one_not_both("Napoleon", "Josephine"), l, {"xor_inclusive": True}), [0, 1, 2])


class PlanTests(unittest.TestCase):
    def test_no_famous_name_can_survive(self):
        for plan in PLANS:
            self.assertEqual(landmark_risks(plan), [], plan.key)

    def test_clue_kinds_vary_across_cases(self):
        kinds = [{c.key.split("_")[0] if c.word else c.key for c, _, _ in p.clues} for p in PLANS]
        for a in range(len(kinds)):
            for b in range(a + 1, len(kinds)):
                self.assertLessEqual(len(kinds[a] & kinds[b]), 2, (PLANS[a].key, PLANS[b].key, kinds[a] & kinds[b]))

    def test_every_clue_has_a_story(self):
        for plan in PLANS:
            for c, title, story in plan.clues:
                self.assertTrue(title and len(story) > 40, (plan.key, c.key))

    def test_name_pools(self):
        self.assertGreater(len(FIRST_NAMES), 5000)
        self.assertGreater(len(SURNAMES), 15000)


class CaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for seed in range(10):
            try:
                cls.case = generate_case(PLANS[1], random.Random(seed), "H", 21)
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

    def test_names_vary_like_the_winners(self):
        flat = self.case.ledger.flat
        self.assertGreater(len(set(flat)) / len(flat), 0.85)


@unittest.skipUnless(os.environ.get("BOOK_PDF"), "set BOOK_PDF to a rendered book to check it")
class RenderedBookTests(unittest.TestCase):
    def test_book_pdf(self):
        from village.check_book import main
        self.assertEqual(main(os.environ["BOOK_PDF"]), 0)


if __name__ == "__main__":
    unittest.main()

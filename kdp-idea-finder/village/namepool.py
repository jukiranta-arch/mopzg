"""Name pools for the lists: US Census first names and surnames (village/data/SOURCE.txt).

The winners' lists rarely repeat a name: in the Mr Darcy sample 84% of 5,151 entries are different, with about
3,000 first names and 1,800 surnames; in The Autumn Killer 98% are different. Drawing first names in a shuffled
cycle from 5,000+ and surnames from 20,000 gives the same feel.
"""

import itertools
import os

_DIR = os.path.join(os.path.dirname(__file__), "data")


def _read(name):
    with open(os.path.join(_DIR, name), encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip()]


FIRST_NAMES = _read("first_names.txt")
SURNAMES = _read("surnames.txt")


def pools(exclude):
    """First names and surnames, minus every word of the famous names in a list."""
    return [n for n in FIRST_NAMES if n not in exclude], [n for n in SURNAMES if n not in exclude]


def entry_maker(rng, firsts, lasts, full_share):
    """Entries in the style of the winners: first names drawn in a shuffled cycle, some with a surname."""
    order = firsts[:]
    rng.shuffle(order)
    cycle = itertools.cycle(order)

    def entry(full=None):
        f = next(cycle)
        return f + " " + rng.choice(lasts) if rng.random() < (full_share if full is None else full) else f
    return entry

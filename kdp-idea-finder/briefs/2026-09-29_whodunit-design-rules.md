# Design rules for find-the-killer puzzles

Sources:
- Juho's test solve of the first *Who Killed Prince Charming?* sample, 2026-09-29.
- What readers of competing books say online. Search results only: Goodreads, the publisher sites and review blogs block direct fetching from here.

Amazon's own reviews of the competitors come next, through the new review capture (see "Next" below).

## What went wrong in the first sample

Juho finished with **5 names instead of 2**. The puzzle checked out by the generator's reading of the rules. A human reading it differently got a different answer, and that makes the puzzle broken.

| Problem | What happened | Fix |
|---|---|---|
| "King" as a surname | Page 3 had "Robin King" (page 2 even had "Sir King"). The clue counted only names *beginning* with the title King. Juho counted Robin King, so four page-3 guests survived. | "King" is removed from surnames. A King is now **any name with the word King in it**, so Old King Cole and the Frog King count too. |
| Titles counted in letter clues | "Miss Carla Briggs" had an odd number of consonants only because of "Miss". Juho left the title out, as most readers would, and ruled out the real suspect. | **Titles don't count** (Queen Mabel is checked as Mabel), and suspects never have a title. |
| "Clever Gretel" | A character whose name contains Gretel, next to a clue built on Gretel appearing once. | Removed. |
| Counting 200 names on a page | "An even number of names on the page" means counting 200 tiny names by hand: slow and error-prone. | Replaced with "on an odd-numbered page". |

**The general fix: robustness to misreadings.** Every puzzle is now also solved under 6 plausible misreadings:
- counting titles;
- treating Y as a vowel;
- "within 12 names" read one too many or one too few;
- counting Hansel's and Gretel's own pages;
- counting only titled Kings and Queens.

A puzzle is accepted only if all of them leave the same two suspects (`whodunit/model.py` READINGS). The sample was also re-solved from the text of the PDF by separate code, under each misreading and under two of them combined.

## What readers of competitors say

**The Killer Isn't Alice** (46,600 suspects, 18 clues; indie, then Little, Brown):
- **It has a public corrections page.** Some names appear twice in a list at the back by mistake. The first print run dropped lowercase "j" and "é" from some names. ([corrections](https://www.thekillerisntalice.com/corrections))
  - *Our rule:* embed every font (done: Liberation Serif, embedded and tested) and use plain A–Z names only.
- **It has a clue-clarification page.** "Jill is a very common mistaken three-letter name because it looks so short." ([clues](https://thekillerisntalice.com/clues))
  - *Our rule:* a worked example in every clue box, chosen to give the same verdict under every reading.
- **Duplicate names felt like a deliberate trap.** ([review](https://www.twinandtine.com/book-reviews/the-killer-isnt-alice-book-review-a-puzzle-that-humbles-you-one-name-at-a-time/))
  - *Our rule:* the rules page now says "Some names appear more than once. Each one is a different guest."
- **Solvers use the clues out of order,** with highlighters, sticky notes and page tallies. Some cross out names with an early clue, then realise a later clue needed them. ([tips](https://www.tiktok.com/@bethanygking/video/7661307547952876814), [clue order](https://mimihasalife.com/the-killer-isnt-alice-clue-order/))
  - *Our rule:* the clues are order-independent by construction, and the rules page says so. Consider printing a suggested order, plus a tally page.
- **Solving takes 3–4 weeks,** and people treat that as a plus. ([Mimi Has A Life](https://mimihasalife.com/my-the-killer-isnt-alice-saga-tips/))
- **The ending is thin: "the mystery ends with an arrest, not a narrative resolution."**
  - *Our rule:* give the reveal a real story payoff.
- **The answer is checked online, not printed.** The same goes for *Do No Harm* (Ada Nightingale, 3 volumes): "no printed answer in the book, with answers verified online to avoid accidental spoilers… the complete account of why the murderer did it is revealed exclusively online".
  - *Worth copying:* no spoiler risk, a story reward, and an email list for the next book. For now our sample prints the solution after a Notes buffer page.

## Next

Capture Amazon reviews, critical ones first, of the direct competitors. Paste these into the **Book reviews** box of the KDP Capture panel (signed in to Amazon, for the critical-review pages):

```
B0GQ2VXKY7  The Killer Isn't Alice (indie edition, 1,902 reviews)
B0H4TDT6GF  The Killer Was On The Guest List (159)
B0H6TW12GP  Murder City (197)
B0H4X2W7NN  Do No Harm (107)
B0H7FCXP4V  The Killer Never Checked In (60)
B0H99P249X  The Killer Is in This Book (59)
B0H8KKF2D8  Find the Spy (58)
B0HF14P1RZ  The Killer on Ruby's List (52)
B0H4LPZ1XB  The Lottery Killer Volume 2 (64)
B0HDFLLT2V  NOT ALONE (44)
B0H7S181HY  Kill Grid Volume 1 (44)
B0H9PBXJSZ  Who Killed Mr Darcy? (6)
```

Read them with `python -m kdpfinder reviews --max-stars 3`.

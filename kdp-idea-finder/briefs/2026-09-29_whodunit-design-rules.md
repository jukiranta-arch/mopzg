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

**The Killer Isn't Alice on amazon.co.uk** (Century edition, BSR 11, 1,807 ratings; the page as a signed-out visitor sees it, 2026-09-29):
- **Stars:** 80% 5-star, 8% 4-star, 5% 3-star, 1% 2-star, **6% 1-star**. For a bestseller, that 1-star share points to people who got stuck or felt cheated.
- **Amazon's "Customers say" summary:** "highly addictive and entertaining… mixed feedback about its clues, with some finding them great while others find them awful… several customers mention getting bogged down in the sheer number of names."
  - Its topic counts: Engaging 39, Content 37, Difficulty 13, Number of names 8, Clues 7, Plot 6.
- **"Your interpretation of the clues along the way will affect your progress… If you get to a point where you have multiple pages & names left then your interpretation of the clues is off."** This is exactly what happened in our first sample.
  - *Our rule:* robustness to misreadings (above).
- **A Belgian reader: "1 clue is wrong I think, found the killer thanks to an extra hint."** Online hints rescue solvers.
  - *Worth copying:* a hint page or site.
- **Praise:**
  - better focus and "limit screen time";
  - Easter eggs: "famous names and characters strategically placed together. A great touch!";
  - good paper: highlighter doesn't bleed through;
  - "I thought I had it many times, only to find the name didn't meet one criteria! Frustratingly fun".
- **"A bit of a grind… tedious at times."** Readers who realise the clues can be used in any order, and that some clues clear thousands of names at once, enjoy it more.
  - *Our rule:* say so on the rules page (done). Consider a "where to start" tip.
- **Bought together:** *Murdoku*, *The Killer Never Checked In* and **erasable highlighters** (Legami). Buyers use highlighters.
  - *Paper:* KDP's paper is thinner than a trade publisher's. Test highlighter bleed on a proof copy, and suggest pencils or erasable highlighters in the book.
- **A crowded, fast-growing lane:** *What If She's Innocent? (47,500 suspects)*, *The Sealed Verdict*, *The Flight Deduction*, *Detective Verdict* and *The Killer Is… Board* all appear in "customers also viewed". A theme that stands out matters even more.

## Amazon reviews of 12 competitors (amazon.co.uk, 2026-09-29)

These are 67 reviews shown on the book pages, plus each page's star breakdown and "Customers say" summary. Captured with KDP Capture, stored in `captures/inbox/reviews-*.json`. Read them with `python -m kdpfinder reviews`.

| Book | Names | 1-star | 5-star | What the low ratings say |
|---|---|---|---|---|
| The Killer Isn't Alice | 46,600 | 6% | 80% | a bit of a grind; one clue seemed wrong |
| The Lottery Killer Vol. 2 | ? | 2% | 82% | none: "perfect balance of hunt and find" |
| Kill Grid Vol. 1 | cases | 0% | 74% | pages came loose from the binding |
| Find the Spy | 180 | 0% | 66% | answers become guessable, repetitive |
| Who Killed Mr Darcy? | 31,830 | 0% | 79% | none so far |
| The Killer Never Checked In | 3,000 | 8% | 62% | too easy: "after 6 clues only 17 left"; no thinking needed |
| Murder City | buildings | 16% | 45% | **wrong answer**; the QR check **shows the answer even when you're wrong** |
| The Killer Was On The Guest List | 48,319 | 24% | 41% | "no story, just names"; clues at the back, **no page numbers**; letter clues on 20,000 names |
| **Do No Harm** | 40,700 | **45%** | 36% | **too easy**: "one clue narrows it to two chapters instantly", done in 20–60 minutes; an inaccurate clue; the site spoils the answer |
| **The Killer Is in This Book** | 51,200 | **44%** | 22% | **letter clues on every name**: "eliminating every name with a double letter, which would take weeks"; names you can't eliminate; tiny print; names run into the fold |

### The five ways these books fail

1. **Too easy.** One clue wipes out most of the book, or there's a handful of names left after a few clues. That gets 1 star from people who came from *Alice*.
2. **Letter work on huge lists.** Checking every one of 20,000–50,000 names for a letter pattern gets called "weeks", "mind-numbing", "feels like AI". Hunting for specific names that clear whole pages is what people enjoy. One reader asked for more "rare" finds (Rosalba, Ezekiel): "those kinds of finds keep me motivated".
3. **Wrong or ambiguous clues.** A wrong answer is fatal: "2 books whose answer we can't work out". Ambiguity lands you with "multiple pages & names left".
4. **Spoiled answers.** QR or web checks that reveal the killer to a wrong guess, or that don't work. Praise goes to "the answer is in the book but not where you can accidentally read it" (*Never Checked In*) and "the end part in code" (*Mr Darcy*).
5. **Just names, no story.** A reader wrote: "I expected clues about these characters, not just clues about their names." The praise goes to "a story that continues after you solve the crime" and "Easter eggs: famous names strategically placed together".

Physical complaints: 12 pt names running into the fold, tiny print that needs a magnifying glass, pages coming loose, missing page numbers, clues at the back. Praised: clues at the front, a tear-out clue card ("no flipping back and forth"), paper that highlighter doesn't bleed through.

### Targets for *Who Killed Prince Charming?*

Checked by the generator where it can be; the "now" figures are from the current book preset, seed 1.

| Rule | Target | Now |
|---|---|---|
| No clue is a knockout: readers use the clues in any order, so each is measured alone | every clue alone keeps **≥ 30%** of names | Hansel & Gretel alone keeps **20.8%** (fails) |
| Page-level clues (hunt for names, cross off pages) come first, letter clues only on what is left | after all page-level clues, **3–10%** of names remain (about 1,000–3,000) | **207 names on 6 pages (0.7%)**: letter clues then take minutes, so the puzzle is too easy |
| Hunting beats trawling | at least 6 clues about *where* a name is or *which characters are near it* | 7 |
| Exactly one answer, whatever the reading | already enforced (READINGS) | ✓ |
| Answer protected but in the book | the killer's name is printed only in code, decoded with the two suspects' page numbers | printed in plain text after a Notes page |
| A story | a short scene opens each chapter; a proper ending after the reveal | a one-page setup only |
| Self-checks without spoilers | "checkpoint" page: how many *pages* should still be open after each clue group | counts are only on the solution page |
| Print | 10 pt names, **wider inner margin (0.85")** so nothing runs into the fold; page numbers on every register page; clues at the front plus a tear-out clue card at the back | 10 pt ✓; inner 0.70"; numbers ✓; front ✓; no card |

## Next

Done 2026-09-29 (above). To widen the sample, run the same list on amazon.com, whose book pages show a different set of top reviews. Run KDP Capture in a private tab (no sign-in) and paste these into the **Book reviews** box:

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

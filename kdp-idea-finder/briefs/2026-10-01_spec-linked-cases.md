# Spec (draft for approval): five linked cases, every answer checked in the book

Status: **draft, 2026-10-01**. No code until Juho approves. The evidence is in `2026-09-30_name-list-sweet-spot.md` and `2026-09-29_winners-samples.md`.

## The promise (cover and subtitle)

> **5 murders · 25,000 suspects · 1 mastermind.**
> Every answer checks itself: no website, no QR code, no spoilers.

## What we keep from the genre (so the crowd recognises it)

| Element | Taken from |
|---|---|
| Crossing out names in printed lists | *Alice*, *Darcy*, the whole lane |
| Famous names hidden among ordinary ones, groups placed together | *Alice* (Beatles, presidents), *Darcy* |
| A clue mix of landmark hunts, page and position clues, and letter clues last | *Darcy*'s 15 clues, *Autumn Killer*'s 18 |
| A precise rules page: exact spelling, Y is a consonant, a crossed-out name still counts for later clues, what "facing page" means | *Find the Killer*, *Autumn Killer* |
| A worked example in every clue | *Never Checked In*, *Darcy* |
| Clues at the front of each case; a story line from a witness, then the plain rule | *Never Checked In*, *Guest List* |
| Final story and answer at the back, behind a divider, printed upside down | *Never Checked In*, *Darcy* |

## What is ours (so the book gets picked up instead of buried)

1. **Five linked cases of about 5,000 names each.** Each case takes an evening or two: "smaller categories so it's not overwhelming" (*Eliminate*), "several days, not a month" (*Coroner*). It is the opposite of the 46,000–51,000-name pile.
2. **A check after every case.** One line under the case's last clue:
   > *Check: the killer's name has 6 letters, and its letters add up to 64 (A = 1 … Z = 26).*
   - **It confirms without revealing.** Many names in the book add up to 64, but only one is still standing at the end of the case.
   - **The generator guarantees it:** no name left standing under any misreading (the READINGS from the Prince Charming generator) passes the check.
   - **It catches a wrong answer or a mistake at once,** not at the end of the book. *Eliminate*'s worst review is about exactly that.
   - **No competitor checks answers in the book:** they use websites, QR codes, or the answer printed at the back.
3. **A chain.** Each case has one clue that uses the last killer ("tonight's killer shares no letter with last night's"). The cases belong together, and the check makes sure you carry a correct answer forward.
4. **A finale that is a puzzle, not just a reveal.**
   - The first letters of the five killers spell the mastermind's first name.
   - That name appears several times in a short final list. Five last clues, one per case, pick out the right one.
   - The finale also has a check line.
5. **The story is in the book.** Each case opens with 1–2 pages of story. The finale gives the motive and how the five killers connect. No website (Juho's rule).
6. **A book you can hold:** about 160 pages, not 400.

## Clue rules (from the reviews and from Juho's test solves)

- **Per case:** 10–12 clues.
  - 3–4 hunt clues (find a landmark or group; pages between two landmarks; within N names of a landmark).
  - 2–3 page and position clues (facing page, the name before or after, the first name on the page).
  - 3–4 letter clues, meant for the few hundred names left.
  - 1 chain clue.
- **No knockout clue:** no clue on its own removes more than 70% of a case. The complaint: "instantly knocked off half the book."
- **Hunt first, letters last:** the hunt and page clues leave about 5–10% of the names, so letter work is never done on thousands.
- **Robust to misreadings:** every case must give the same answer under each misreading the generator models (reused from `whodunit/model.py`).
- **Never** italicise landmarks, list them in a Who's Who, give their page numbers in hints, or print checkpoints that need counting hundreds of names. These are Juho's lessons from Prince Charming.
- **The clues work in any order,** and the rules page says so.

## Layout

- **Names:** bare first names, plain A–Z, no titles, no odd capitals. About 200–230 a page, at least 10 pt, inner margin at least 0.85".
- **Every page shows** the case and page number at the top ("Case 2 · page 14 of 22").
- **Each case has 2–4 chapters** named for places in its setting, so chapter clues have something to use.
- **Trim:** 8 × 10 in or 8.5 × 11 in, decided on a printed proof.
- **Paper:** recommend pencils or erasable highlighters on the rules page. KDP paper is thin; a reader complained that highlighters bled through.

**Size:**

| Part | Pages |
|---|---|
| Registers: 5 × ~5,000 names | ~110 |
| Case openings, story and clues: 5 × ~4 | ~20 |
| Front matter: rules, how to play, worked example | ~8 |
| Finale | ~6 |
| Solutions and story ending | ~8 |
| **Total** | **about 150–160** |

## Setting (Juho's call)

It needs a reason for five murders in five different crowds, plus a mastermind behind them. The data does not separate settings: a setting alone never sells a book. Two options:

- **A. Five nights of a village festival** (cozy tone).
  - For: cozy sells in murder word searches (*Murder Among the Stacks* 33/day, *Murder for Breakfast* 14/day).
  - Against: cozy name-list books are appearing (*Kittering St Mary*, six connected cases; *Murder, Tea, and Cat Hair*), with no sales data yet.
- **B. Five days on an ocean liner** (classic Golden Age tone): a passenger list per deck or class. Nothing in our data either way.

**Landmark pool:** famous first-name groups and pairs from history, books and public life: John Paul George Ringo; Charlotte Emily Anne; Meg Jo Beth Amy; Orville Wilbur; Romeo Juliet; Bonnie Clyde… First names only, never brand or band names on the cover. The pool runs to hundreds, not the 60 fairy-tale names that sank Prince Charming.

## Title options (AI draft; Juho finishes)

1. *The Mastermind Is Among Them: 5 Linked Murder Mystery Cases, 25,000 Suspects, 1 Mastermind. A Find-the-Killer Puzzle Book Where Every Answer Checks Itself*
2. *Five Nights, Five Killers: A Murder Mystery Puzzle Book with 25,000 Suspects and 1 Mastermind. No Website, No Spoilers: Every Answer Checks Itself*
3. *Who Sent the Killers?: A Linked-Case Murder Mystery Puzzle Book. 5 Cases, 25,000 Suspects, 1 Mastermind*

Keywords for the subtitle and backend: find the killer, murder mystery puzzle book, elimination puzzle, cross out names, whodunit for adults.

## Package and price

| Item | Plan |
|---|---|
| Price | **$11.99**, below the $13–17 pile. *Never Checked In* sells 49/day at $6.99. Royalty at $11.99 and ~160 pages is about $4. |
| Format | paperback only (puzzle book) |
| Near-copy rule | every list is generated and unique |
| Trademarks | check every title word; no "Alice", no band names |
| Volume two | same format, a new setting and a new mastermind |

## Risks

- **The structure is becoming common.** *Eliminate*, *Autumn Killer* and small new books all link sections or cases. Our edge is the in-book check plus quality, not a format nobody has seen.
- **We compete with *Eliminate* for the same buyer.** It is a strong series with three volumes.
- **The check might feel like a hint.** It only appears after the last clue, and it confirms rather than points.

## Before any code: a paper prototype

1. **One case, by hand:** its opening page, its clue page, two register pages and the check line. Checked by script, sent to Juho as a PDF to test solve.
2. **Only after that test,** adapt the generator. Reuse READINGS, the independent PDF checker and the font embedding from `whodunit/`.

## Decisions for Juho

1. Approve or change the structure: five cases, a check after each case, the chain, the mastermind finale.
2. The setting: A, B, or another.
3. A working title, which can change later.

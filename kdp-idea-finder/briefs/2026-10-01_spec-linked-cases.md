# Spec (draft for approval): five linked cases, every answer checked in the book

Status: **draft, 2026-10-01**. No code until Juho approves. The evidence is in `2026-09-30_name-list-sweet-spot.md` and `2026-09-29_winners-samples.md`.

## The promise (cover and subtitle)

> **25,000 suspects · 1 mastermind.** Five murders, one summer, one village.
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

**What the data says about setting** (2026-10-01; murder-mystery puzzle books on amazon.com, grouped by setting words in the title):

| Setting | Books | Total sales/day | Selling at least 3/day | Newcomers selling at least 3/day |
|---|---|---|---|---|
| Cozy (village, bookshop, bakery, tea…) | 81 | 117 | 10 | 8 |
| Dark (serial killer, forensic, true crime) | 90 | 82 | 7 | 4 |
| Hotel | 16 | 65 | 4 | 4 |
| Manor or period (*Darcy*, *Vex Manor*) | 32 | 50 | 4 | 3 |
| Train or flight | 12 | 1 | 0 | 0 |
| **Ship, cruise or liner** | **9** | **1** | **0** | **0** |

- **Correction to option B:** "nothing in our data either way" was wrong. Of 21 ship, train and flight books, none sells. Some are large print or for children, but the signal is still negative.
- **Where the cozy sales come from:** almost all are word-search books. Cozy *name-list* books exist (*The Killer Borrowed a Book*, *Just One Murder Before Tea*, *Who Killed Lady Hawthorn?*, *Kittering St Mary*, *Murder, Tea, and Cat Hair*), but their pages weren't read, so their sales are unknown. Next searches: `cozy murder mystery puzzle book` and `cozy find the killer`.

**The cozy searches** (2026-10-01; `cozy find the killer`, `cozy murder mystery puzzle book`; the capture read the first 16 books of each):
- **Cozy is proven for story-plus-word-search books, not yet for name lists.**
  - The cozy sellers are word-search story books: *Murder Among the Stacks* 30/day, *Murder for Breakfast* 15/day, *Murder, She Searched* 13/day.
  - The name-list sellers in the same results are not cozy: *Alice*, *Darcy*, *Never Checked In*, *Eliminate*.
  - The cozy name-list books (*The Killer Borrowed a Book*, *Just One Murder Before Tea*, *Lady Hawthorn*, *Murder, Tea, and Cat Hair*, *The Bookstore Killer*) all sit below the first 16 results, where ranks weren't read. Amazon orders search results largely by sales, so they are probably weaker, but this is not proven.
- **A warning about the structure.** The *Find the Killer Mystery Files* series sells **0.1/day per book**, across four books (Ski Lodge, Superyacht, Casino, and one more), each with about 10 reviews at about 2 months. Each book is "Five 555-Suspect Murder Mystery Logic Puzzles", so it reads as five small separate puzzles. Compare:
  - *Eliminate* (15 sections, 15/day) and *Autumn Killer* (3 trails, 10/day) sell. Both present **one big case** with one killer, and the sections are just how you get there.
  - **So the cover and title must sell one big case:** "25,000 suspects, 1 mastermind". "Five linked murders" is how you play, not the headline. Never "5 puzzles".
- **Setting decision (data-led):** an English village with a light, classic tone (Christie, not gore).
  - It is the cozy buyer's world, and it is close to the most successful tone in our format (*Darcy*, *Alice*).
  - The title uses the name-list lane's words (suspects, killer, mastermind) rather than "cozy word search", so the book shows up where name-list buyers look.
  - Ship, train and flight are ruled out.

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

## Prototype, second version (2026-10-01): laid out like *Who Killed Mr Darcy?*

Juho rejected the first version:
- the answer check was printed before the names, so it gave away the killer's letter count;
- I had invented rules ("standing together", "famous names") that he couldn't follow;
- a line of story before every clue cluttered the clue pages.

The second version follows Darcy's order and wording:
1. the story;
2. The Case;
3. The Clues ("Each suspect's name…", "Both suspects are within one page of a Robin Hood"), each with how it works and an example;
4. Before You Start: what a name is, exact spelling only, letters, vowels, names don't break across rows, tips;
5. the ledger: names separated by dots, first names and full names mixed, famous names unmarked, pages numbered from 1;
6. at the back: the final deduction (two suspects; the longer name is the killer), the check line, a Stop page, and the solution upside down on its back.

The case has 9 clues, 4,367 names on 20 pages, and leaves 223 names after the hunt clues. `python -m village.check_pdf` re-solves it from the PDF under all 7 misreadings.

## Setting, re-checked (2026-10-01): the village fête was not supported by data

Juho: "I have no clue what an Ashcombe Raffle or a summer fête is." Our buyers are on amazon.com (US), where "fête" means little. Murder-mystery puzzle books on amazon.com, grouped by setting words in the title:

| Setting | Books | Sales/day | Selling 3+/day | Hit rate |
|---|---|---|---|---|
| Ticket or big event (*Killer Bought a Ticket*, *Lottery Killer*, *Murder City*) | 11 | 31 | 4 | 36% |
| Hotel, inn or guest list (*Never Checked In*, *Guest List*) | 18 | 61 | 5 | 28% |
| Famous names (*Alice*, *Darcy*) | 20 | 479 | 5 | 25% |
| Village or small town (mostly cozy word searches) | 56 | 84 | 9 | 16% |
| Christmas or holiday | 124 | 96 | 11 | 9% |
| Manor or castle | 26 | 27 | 2 | 8% |
| **Fair, festival or market** | **17** | **2** | **0** | **0%** |
| Ship, train or plane | 21 | 2 | 0 | 0% |

**What the winners do about the answer:** *Alice*, *Never Checked In*, *Find the Killer*, *Guest List*, *Eliminate* and *Autumn Killer* all end with **one** killer. Only *Darcy* ends with two suspects and a final deduction, and its sample doesn't show what that deduction is. **Decision:** the clues end at one killer, and the answer and check line go at the back.

### The setting searches (2026-10-01): copies of a setting flop; the cozy small town is empty in our format

**Hotel.** *Never Checked In* sells 36/day. The hotel name-list books that came after it sell almost nothing:

| Book | Sales/day | Age |
|---|---|---|
| *Murder Hotel* (10 cases, 4,980 rooms) | 1.6 | 23 days |
| *Murder at the Blackwood Hotel* (48,000 suspects) | 0.3 | |
| ***The Wakeford Hotel Mysteries*** **(7 nights, 498 rooms)** | **0.2** | |
| *The Moonholt Hotel Murder* | 0 | |

*The Wakeford Hotel Mysteries* is close to our "five nights" idea, and it doesn't sell.

**Ticket or event.** *The Killer Bought a Ticket* sells 10/day. The books that came after it don't:

| Book | Sales/day | Age |
|---|---|---|
| *A Ticket to Murder* (47,000 fans, 26 reviews) | 0.6 | 20 days |
| *Murder at a Stadium Concert: The Killer Had a Ticket* | 0.1 | |
| *The Killer Took the Ticket* | 0 | |

**Small town.**
- The sellers are cozy word-search story books set in American small-town shops:
  - *Murder Among the Stacks* (bookstore) 29/day;
  - *Murder by Muffin* (bakery) 7.4/day;
  - *Murder on Vacation* (B&B) 4.3/day;
  - *Murder at the Antique Shop* 4.7/day;
  - *Small Town Murders* 3.0/day.
- *Murder for Breakfast* (15/day) is the same kind of book.
- **No name-list book appears among the small-town results.** The readers are proven; our format hasn't been tried with them.

**Conclusion.** In this lane, a setting doesn't sell on its own. The first strong book in a setting sells, and the copies that follow flop. Copying the hotel or the ticket means joining a pile of failures. The cozy American small town is the one big audience with no name-list book.

**Setting decision (proposed):**
- A cozy American small town.
- Each case is one local shop, and its list of names is that shop's own record:
  - the bookstore's customer list;
  - the bakery's order book;
  - the diner's tabs;
  - the inn's guest book;
  - the library's borrowers.
- These are exactly the shops the selling cozy books use.
- The title keeps the name-list lane's words: suspects, killer, mastermind.

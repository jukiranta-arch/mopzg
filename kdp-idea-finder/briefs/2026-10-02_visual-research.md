# How the winners look, and the design of Murder in Juniper Falls

Sources:
- the "Read sample" pages of eight find-the-killer books that Juho saved, looked at page by page (contact sheets in the scratchpad);
- KDP's image guidelines and OpenAI's notes on its image model, as far as search results show them (openai.com and its developer site are blocked by this environment's network policy).

## What each winner's interior looks like

| Book | Sales | Type | Layout | Pictures |
|---|---|---|---|---|
| The Killer Isn't Alice | US rank 63 | Book serif (credited "Typeset in Kelvinch", a Charter-style face); bold geometric sans for the title | Names justified edge to edge, no separators, about 9 a row; small capitals running head; "Chapter 1." over a large chapter name | None. An ink splatter in page corners, title page in two greys |
| Who Killed Mr Darcy? | about 17/day | Times-style serif | Names justified with "·"; each clue's rule in a grey box; chapter label in capitals over a quoted line | None inside |
| Eliminate! | 15–17/day per volume | Condensed sans headings (Roboto Condensed style), plain sans text | Two- or three-column lists; clues on a drawn spiral notebook | Many greyscale AI illustrations: desk scenes, a case photo, folder, phone message; full-page textured section dividers |
| The Autumn Killer | 10/day | Merriweather-style text; flared capital headings (Cinzel style) | Names justified; grey step boxes and tables; leaf icon beside every heading | A leaf emblem, a tree on the welcome page |
| The Killer Was On The Guest List | rank 9,069 | Book serif | Clues as running text; lists in columns | Large ink-and-pencil drawings: the invitation, the hall, the gate |
| The Killer Never Checked In | rank 1,303 | Condensed sans headings, serif text | Contents page, hotel map, character ID cards | Photo-real greyscale portraits and scenes, handwritten notes, a phone message |
| Find the Killer (Midnight Murder) | rank 16,013 | Plain sans | Numbered names in columns | None |
| The Lottery Killer 2 | UK 4,728 | Serif | Photo cards 16 a page | Hundreds of photo portraits |

### What follows from the table

- **Typesetting matters more than illustration.** The best seller, Alice, has no pictures, but it is set like a real book:
  - a good text face;
  - justified rows;
  - a running head;
  - quiet chapter openers;
  - generous margins.
- Its title page and first chapter page are what the sample shows, and they look professional.
- **Illustration is common among the newer winners,** at the openings of sections rather than on the list pages:
  - Eliminate, Guest List and Checked In all use it there;
  - the list pages stay plain everywhere.
- **Small recurring touches signal care:**
  - Autumn's leaf beside each heading;
  - Darcy's and Autumn's grey rule boxes;
  - Checked In's contents page and map.
- **Nobody uses colour inside.** All are black ink on white, which is also the cheapest print option.
- **Legibility is a review topic.** One Alice reviewer added "the always helpful magnifying glass for when my eyes get tired", so the names must be easy to read.

## What our first build got wrong

- **Liberation Serif** (a Times clone) everywhere, and bold Times headings: it looks like a Word document.
- **Uneven name rows:** rows were filled greedily, so a row of a few long names had huge gaps around its dots.
- **No page furniture:** no running head and no contents page.
- **Ragged list pages:** pages ended at different heights, some a quarter-page short.

## The design now (village/design.py)

- **Text and names: Charis SIL.**
  - It is a Charter-style face like Alice's, the most legible of five faces set side by side with our own names.
  - Names are 10 pt; body text is 10.5 pt.
- **Headings: Playfair Display,** a classic cozy-mystery display serif.
- **Licence:** both fonts are under the SIL Open Font License, with the licence text in `village/fonts/`, and both are embedded in the PDF.
- **Name rows are balanced.** The page uses the same number of rows as greedy filling, but the breaks are chosen so the spare space in every row is as even as possible.
  - The spare space goes around the dots, never inside a name.
  - Dots are grey, so names stand out.
  - The puzzle doesn't change: which names are on which page is fixed; only the rows move.
- **List pages fill to the foot.** Each page opens its line spacing between 14 and 15.8 pt; the last page of a list is left as it falls.
- **Running heads:** the book's title on left-hand pages and the section ("Case One · The Bookstore") on right-hand pages, in small spaced capitals.
- **Chapter openers:** "Chapter One" in italic over the chapter name, with a divider.
- **Clue pages:** "CLUE 1" and a title, the witness line in italic, and the **Rule in a 12% grey box**. KDP asks for at least 10% for a grey fill to print. The spacing tightens in steps until a case's clues fit on two pages, so no blank pages are needed.
- **Case openings:** label, name and date line, then a picture, then the story with a drop capital.
  - The picture takes whatever room the story leaves, between 1.6 and 2.9 in tall.
- **New front matter** (keeps every case opening on a left-hand page, facing its clues):
  - a title page with a picture;
  - a contents page listing each case's list pages;
  - a full-page town map facing the introduction.
- **Answer pages:**
  - write-in lines;
  - the check in a ruled box;
  - each case's evidence (the bookmark stamped 1, the ribbon marked 2…) drawn below.
- **Size:** 142 pages, one blank (the last), 6 × 9 in.

## Pictures

There are 13 slots: title, map, six case scenes and five evidence objects, plus an optional ornament.
- `books/juniper-falls/art/PROMPTS.md` has the style block and one prompt per picture for ChatGPT.
- **Style:** black-ink pen-and-ink drawing on white, like a mid-century American book illustration. It prints crisply in black ink, unlike grey wash or photo styles, which go muddy on uncoated paper.
- **Scale:** dozens of pictures, not thousands, all made by Juho in ChatGPT. Every one is checked here before it goes in.
- **The build handles each picture:**
  - trims white margins;
  - flattens transparency onto white;
  - converts to greyscale;
  - reports each picture's printed DPI in `qa.md`.
- `--final` refuses to build while a picture is missing or prints below 300 DPI.

### The image model (as far as search results show)

- **Version:** ChatGPT Images 2.5 / GPT-Image-2.5, released September 2026. Its strength is text rendering, so signs and map labels are realistic.
- **Sizes:**
  - standard: 1024×1024, 1536×1024 and 1024×1536;
  - larger, up to 3840 px on the long edge (2560×1440, 3840×2160), marked experimental above 2560×1440.
- **What this means for us:**
  - a 3:2 scene printed about 4.5 in wide needs 1350 px, so 1536 is enough;
  - the full-page map needs about 1400 × 2100 px, so it must use a 2K or 4K portrait size.

## The cover (next step)

- **What competitors' covers share:**
  - a huge bold title;
  - the suspect count in a banner ("31,830 NAMES · 15 CLUES · 1 KILLER");
  - a crossed-out name list or a circled name.
- **Juho makes the cover in ChatGPT.**
- **KDP size for 142 pages:**
  - spine 0.320 in on white paper (0.002252 in a page) or 0.355 in on cream (0.0025 in a page);
  - full wrap with 0.125 in bleed on every side: 12.57 × 9.25 in on white, or about 3,771 × 2,775 px at 300 DPI.
- **Next:** work out the exact numbers when the paper colour is chosen.

# A+ content: research and prompt pack

## What the five best sellers do

| | Alice | Never Checked In | Mr Darcy | Guest List | Murdoku |
|---|---|---|---|---|---|
| Panels | 4 | 4 + gift text | 3 | 4 | 3 (tall) |
| Look | the cover's flat graphics | AI scenes in the cover's world | AI scenes + a photo | AI scenes, one consistent set | flat illustrations |
| Numbers headline | ✓ | ✓ | ✓ | ✓ | – |
| Story hook panel | ✓ | ✓ | ✓ | ✓ | ✓ (a cartoon detective) |
| How it works in steps | – | ✓ (4 steps) | ✓ (real clues) | ✓ (3 steps) | ✓ (a full worked example) |
| Real inside content | – | mock-up | **2 real clues, word for word** | mock-up | **a whole mini puzzle, solved** |
| The book in the picture | – | 3D book | **held in hands** | 3D book in every panel | 3D book |
| Reassurance | – | "checkpoints", "only one false guest remains" | "no trivia, no guessing" | "no guessing, no tricks", cipher answer key | – |
| Gift / audience | – | a text list (mom, dad, teens) | – | badges | – |

**Look: follow *Mr Darcy*, not *Guest List*.** The person's call (2026-10-04): *Darcy* feels the least AI-made, and *Guest List* the most.
- **Darcy:** a flat, bright, matte background; few props; real typeset clue text; photographic hands holding the real cover; one panel that is pure typography.
- **Guest List:** glossy marble, chandeliers, cinematic glow, ornate gold frames and crowded props. Avoid all of it.

**Patterns:**
- one idea per panel;
- a big headline in the cover's type;
- 10–30 words per image;
- the same world in every panel;
- the book visible;
- the game explained by showing it, not describing it.

The books with few reviews (*Darcy*, *Never Checked In*) lean hardest on showing how it works and on reassurance.

## Our five panels

Each uses KDP's "Image Header with Text" module: a 970 × 600 image, plus a headline and a short paragraph under it.

| # | Panel | Answers the review complaint |
|---|---|---|
| 1 | Story hook + the book + the five tokens | "no story, just names" |
| 2 | Five case files, not one endless list | "worked on it for a month", "bogged down in names" |
| 3 | How to crack a case, in 4 steps (incl. the check) | "the QR code spoiled it", "how does it work?" |
| 4 | Try a mini case (unsolved, so the shopper plays) | proof the game is real and fair (*Darcy*, *Murdoku*) |
| 5 | The book in hands + reassurance badges + call to action | gift buyers, "one answer only" |

## Instructions for the image agent

- Generate each image in **landscape 3:2**. Claude crops it to 970 × 600, so keep the top and bottom 6% plain background.
- Attach `cover_front.png` and `cover_back.png` to the first message only, as a style reference.

### Common block (send first)

```
You'll make 5 images for the A+ content ("From the Publisher" section) of the paperback "Who Sent the Killers?" by Nora Clewes. The attached images are the book's front and back covers.

Match their world exactly: the deep aubergine-purple desk seen from straight above, worn cream case-file paper, antique gold accents, soft even light from above, layered hand-made paper textures, and the covers' typefaces (tall condensed high-contrast serif capitals for headlines, a classic readable book serif for small text). Don't copy the covers' layouts.

Look: like a real photograph taken on a desk in daylight, or a cleanly designed printed layout. Matte paper, natural soft light, only a few props, and generous empty space. Avoid anything that looks AI-made: no glossy shine, no glow or light rays, no ornate gold frames or filigree, no chandeliers or candles, no cinematic drama, no floating shiny 3D objects, no clutter.

Rules for every image:
- Landscape 3:2. Keep the top 6% and bottom 6% plain purple background with nothing important in it (the image will be cropped).
- Text must be big and readable on a phone. Spell every word exactly as given, letter by letter, and add no other words anywhere.
- No prices, no ratings or reviews, no "bestseller", no other book titles, nothing seasonal (no snow, no autumn leaves, no holidays).
- If any word comes out wrong, generate the image again from the prompt instead of editing it.
I'll send the five image prompts one at a time.
```

### Image 1: the hook

```
IMAGE 1 OF 5. THE HOOK.
LEFT 45%, on the purple desk:
- Headline in cream condensed serif capitals, two lines: "NOTHING EVER HAPPENS" / "IN JUNIPER FALLS." (J-U-N-I-P-E-R F-A-L-L-S, full stop at the end)
- Under it, one line in antique-gold italic serif: "This autumn, it happened five times."
- Under that, smaller cream serif: "Five killers. One person behind them all."
RIGHT 55%: the paperback book, its front cover exactly as the attached front cover, standing at a slight angle on the desk, photographed like a real product. In front of it, the five evidence tokens in a loose row: a purple tasselled bookmark tag "1", a purple-and-gold prize rosette "2", a cream diner order ticket "3", a brass room key with a purple teardrop tag "4", a cream library card "5", and a sealed cream envelope with a typed note peeking out reading "ONE OF FIVE".
```

### Image 2: five cases

```
IMAGE 2 OF 5. FIVE CASES, NOT ONE ENDLESS LIST.
TOP, centred: headline in condensed serif capitals: "FIVE CASES." in cream, then "NOT ONE ENDLESS LIST." in antique gold.
MIDDLE: six plain manila case files lying flat side by side on the purple desk, slightly overlapping, photographed from straight above. Each has a typed cream label, and five of them have their matching token resting on them (simple, matte, no shine):
1. "CASE 1 · THE BOOKSTORE" with the bookmark tag "1"
2. "CASE 2 · THE BAKERY" with the rosette "2"
3. "CASE 3 · THE DINER" with the order ticket "3"
4. "CASE 4 · THE INN" with the room key and tag "4"
5. "CASE 5 · THE LIBRARY" with the library card "5"
6. the last file is darker purple, stamped in faded gold: "FINAL CASE · THE MASTERMIND"
BOTTOM, centred, cream serif: "Solve one. Check it. Close the file. Then open the next."
```

### Image 3: how it works, with real pages (option 2: ChatGPT draws the attached pages)

Attach `pages/page008-case1-opening.png`, `pages/page009-case1-clues.png` and `pages/page011-case1-list.png` with this prompt.

```
IMAGE 3 OF 5. HOW IT WORKS, SHOWN WITH REAL PAGES.
The three attached images are real pages from the book: (A) the opening page of Case One, (B) the clue page, (C) a page of names. Show them as real printed pages, reproduced as faithfully as you can: same layout, same headings, same black-and-white cut-paper picture, same thin rules and grey clue boxes. Do not redesign them.

TOP, centred: headline in cream condensed serif capitals: "HOW TO CRACK A CASE"
MIDDLE: the three pages lying flat on the purple desk side by side, each slightly rotated (a few degrees), with soft natural shadows, photographed from straight above in daylight. Above each page, a simple numbered circle and a short title in cream capitals, with one small line of cream serif under it:
1. Above page A: "READ THE CASE" / "Who died, where, and who was there."
2. Above page B: "WORK THE CLUES" / "8 or 9 clues per case."
3. Above page C: "CROSS OUT NAMES" / "Strike every name a clue rules out." On page C, about a third of the names are neatly struck through in pencil, and a pencil lies across the corner of the page.
To the right of page C, a small cream card with a gold tick in a circle and the words "CHECK YOUR ANSWER" and, under it, "without seeing the name".
BOTTOM, a cream paper strip with deep purple condensed capitals: "18,000 SUSPECTS · 5 CASES · 1 MASTERMIND"
The headings on the pages must read exactly: page A "CASE ONE", "The Bookstore", "October, the Midnight Sale"; page B "The Clues"; page C "Chapter One", "Mystery & Crime". Keep the pages' small text tidy and realistic: no smudged or melted letters.
```

### Image 4: try a mini case

```
IMAGE 4 OF 5. TRY A MINI CASE.
TOP LEFT: headline in cream condensed serif capitals: "TRY A MINI CASE"
LEFT HALF: a typed cream page of exactly nine names in three columns, NONE crossed out, in a typewriter face:
Column 1: "Walter Price", "June Hollis", "Arthur Bell"
Column 2: "Mabel Crane", "Henry Dale", "Edna Foster"
Column 3: "Clyde Moss", "Peggy Lowe", "Frank Hale"
A sharpened pencil lies beside the page.
RIGHT HALF: three cream clue cards stacked slightly offset, each with a small gold "CLUE" label and the clue in a readable serif:
"CLUE 1 — The killer's first name has five letters."
"CLUE 2 — The killer's last name has four letters."
"CLUE 3 — The killer's last name has a double letter."
BOTTOM, centred, antique-gold serif: "Only one name fits all three. Can you find it?"
Spell all nine names exactly as written. Nothing is circled or crossed out: the reader solves it.
```

(Answer: Clyde Moss. Clue 1 leaves Mabel, Henry, Clyde, Peggy and Frank. Clue 2 leaves Dale, Moss, Lowe and Hale. Clue 3 leaves Moss.)

### Image 5: the call to action

```
IMAGE 5 OF 5. THE CALL TO ACTION.
RIGHT 55%: a real-looking photo of two hands holding the paperback towards the viewer, its front cover exactly as the attached front cover, over the purple desk, with a pencil beside it. Natural daylight, like a phone photo, not a glossy render.
LEFT 45%:
- Headline in condensed serif capitals, three lines: "CAN YOU FIND OUT" in cream, "WHO SENT" in cream, "THE KILLERS?" in antique gold.
- Under it, four small flat badges in a 2×2 grid (simple outlined circles in muted gold, not shiny), each with a simple line icon and a short cream label: "BRING A PENCIL" (pencil), "SCREEN-FREE" (crossed-out phone), "ONE ANSWER PER CASE" (a single tick), "CHECK AS YOU GO" (magnifying glass).
```

## Text under each image (KDP module headline + body)

1. **Nothing ever happens in Juniper Falls. This autumn, it happened five times.**

   Five of the town's best-loved people die in five of its best-loved places: the bookstore, the bakery, the diner, the inn and the library. Each time, the doors were locked and every visitor's name was written down. Each time, a numbered token was left behind. Five killers, one person behind them all. Sheriff Ruth Ambrose has the lists. She needs you to read them.

2. **Five cases, not one endless list**

   No month-long slog through 50,000 names. Each case is its own puzzle of 2,800 to 3,700 names with 8 or 9 clues. Solve it, check it, close the file, and the next case is waiting. Do one a weekend, or all five at once. Together they make one mystery.

3. **How to crack a case**

   Read the chapter, work the clues, and cross out every name a clue rules out until only one is left. A quick check after each case (the name's length and letter total) tells you if you're right without showing the name. No QR code, no website, and the full solutions stay hidden at the very back. Your five answers unlock the final case at the Town Meeting.

4. **Try a mini case**

   Every case in the book works like this, just bigger: thousands of names and 8 or 9 clues. Each case is tested so that exactly one name survives every clue. No second possible killer, no names the clues can't rule out.

5. **A screen-free mystery to solve yourself**

   A gift for the mystery lover who has read everything, the puzzler who has finished every ordinary puzzle book, or two people who want a screen-free evening together. Bring a pencil.

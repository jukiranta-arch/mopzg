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

### Image 3: how it works, inside the real book (v2)

The flat-pages version looked like a cheap flyer. Attach `pages/spread-p008-p009-case1.png`.

```
IMAGE 3 OF 5. INSIDE THE BOOK.
Goal: the best-looking A+ module you can make, showing a shopper exactly what they get inside. It should look like a professional publisher's product photo, the kind a big publisher would use, not a template or a flyer.

The attached image is a real two-page spread from the book (pages 8 and 9): on the left, the opening page of Case One with its black-and-white cut-paper illustration of a bookstore and the start of the story; on the right, the first page of clues, facing it.

THE HERO (about 60% of the image, right side): a realistic photograph of the paperback lying open on the deep purple desk at exactly this spread, seen from slightly above at a gentle angle. The pages curve softly into the gutter, as an open paperback does, with a soft shadow down the middle. Reproduce both pages as faithfully as possible: the layout, the headings "CASE ONE", "The Bookstore", "October, the Midnight Sale" and "The Clues", the illustration, the grey clue boxes. It is a thin 142-page paperback (about 8 mm thick), so show only a thin page block. A pencil rests across the bottom of the right page; the purple tasselled bookmark tag "1" lies on the desk beside the book. Soft natural daylight, matte paper, nothing glossy.

THE TEXT (left side, about 40%, on the purple desk, set like elegant book-jacket typography, not icons or a diagram):
- Headline in cream condensed serif capitals: "HOW TO CRACK A CASE"
- Then three short steps, each a bold antique-gold numeral and a cream line:
  "1  Read the case: who died, where, and who was there."
  "2  Work the clues: 8 or 9 per case."
  "3  Cross out every name they rule out, until one is left."
- At the bottom, smaller cream italic serif: "Then check your answer without seeing the name."

Spell every word exactly as written above. No arrows, no boxes around the steps, no badges.
```

### Image 4: cross out, then check (v3)

v2 was too plain, and the "dashes" read as stray lines. v3 sets it in the world: the sheriff's desk at night, with Juniper Falls outside the window. Attach `pages/spread-p030-p031-case1-list-answer.png`.

```
IMAGE 4 OF 5. CROSS OUT. THEN CHECK.
Goal: a rich, atmospheric, professional publisher's product photo, classy rather than busy.

SCENE: Sheriff Ruth Ambrose's desk in Juniper Falls at night (no people). Upper right: a tall old window; through it, the misty town at night in the same layered cut-paper style as the book's front cover: dark evergreen pines, a few warm lit windows, and the town hall clock tower with one lit window. A brass desk lamp casts a warm pool of light on the desk. The desk is deep aubergine-purple leather and wood; the wall is dark purple.

HERO (lower half, about 55% of the width): the thin paperback (about 8 mm thick) lying open in the lamplight at exactly the attached spread (pages 30 and 31: the last page of names on the left, the "Your Answer" page with its "Check your answer" box on the right). Reproduce both pages as faithfully as possible. About a quarter of the names on the left page are neatly struck through in pencil. A pencil lies beside it, and the brass room key with its purple teardrop tag "4" lies near the book.

TEXT (upper left, on the dark wall, elegant book-jacket typography; plain lines of text only, with no dashes, bullets, icons, boxes or arrows):
- Headline in cream condensed serif capitals: "CROSS OUT. THEN CHECK."
- Two lines of cream serif, one under the other:
  "Names in clean, even rows, well clear of the spine."
  "A quick check tells you if you're right, without showing the name."
- Smaller cream italic serif: "No QR codes. No websites. No spoilers."

Spell every word exactly as written. Matte, natural, not glossy.
```

### Image 5: the case board (v2; replaces the book in hands)

This is the panel no competitor can make: our own town, art and linked cases. Attach `map.png`, `case_bookstore.png`, `case_bakery.png`, `case_diner.png`, `case_inn.png` and `case_library.png`.

```
IMAGE 5 OF 5. THE CASE BOARD.
Goal: the richest, most memorable panel of the set; classy, atmospheric, professional.

SCENE: the corkboard on the wall of the sheriff's office in Juniper Falls, photographed straight on, lit by a warm desk lamp from below left. The board is framed in dark wood; the wall around it is deep purple.
ON THE BOARD:
- In the centre, pinned: the attached black-and-white cut-paper town map of Juniper Falls, printed on cream paper.
- Around it, pinned in a loose ring: the five attached black-and-white cut-paper pictures (the bookstore, the bakery, the diner, the inn, the library), each printed on cream paper like an evidence photo, each with a small typed cream card under it: "1 · THE BOOKSTORE", "2 · THE BAKERY", "3 · THE DINER", "4 · THE INN", "5 · THE LIBRARY".
- From each of the five pictures, a deep plum-red thread runs to a single cream card pinned at the top of the board, with a large question mark "?" drawn on it in pencil.
- One or two of the evidence tokens pinned beside their pictures (the bookmark tag "1", the room key and tag "4").
BOTTOM, on a dark wood ledge under the board: the thin paperback (about 8 mm thick) lying face up, its cover exactly as the attached front cover from the first message.
TEXT (top, above the board, or on a cream strip across the bottom of the board; your choice of the most elegant placement):
- Headline in condensed serif capitals: "CAN YOU FIND OUT" in cream, "WHO SENT THE KILLERS?" in antique gold.
- Under it, a cream paper strip with deep purple condensed capitals: "18,000 SUSPECTS · 5 CASES · 1 MASTERMIND"

Spell every word exactly as written. Matte, natural, not glossy; the pictures are black-and-white cut paper, as attached.
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

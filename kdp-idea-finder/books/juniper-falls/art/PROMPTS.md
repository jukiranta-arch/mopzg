# Pictures for Murder in Juniper Falls: the cut-paper silhouette prompts (final, v2)

The style is chosen: **Style C, cut-paper silhouette**. The bookstore picture (`bookstore-C-cut-paper.png`, in the book as `case_bookstore.png`) is done.

**Why version 1 failed:** given the bookstore picture as an input, the image model copied its whole layout, not just its style: the same tree on the left, shop building, sign, lamp post and sandwich board. So:
- **No reference image.** The bookstore itself was made from the text alone, and the style block below reproduces the medium reliably.
- **Every picture has its own composition:** a different viewpoint, framing and props. Each one also lists what it must **not** contain.

## Instructions for the image agent

1. **Do not attach any image** to the generation requests. Do not use `bookstore-C-cut-paper.png` or any earlier output as an input or reference.
2. **Prompt:** for each picture, send the **style block** plus that picture's **subject** (its composition and its "do not include" list).
3. **Shape:** landscape 3:2 unless the subject says square or portrait. Use the largest size the tool returns.
4. **Check before saving.** Compare each picture with the pictures already made, and regenerate if:
   - it repeats an earlier picture's layout or props: a tree framing one side, a lamp post, a sandwich board, flower barrels, pumpkins, a bicycle, a shop sign above a big window;
   - a word is misspelled, or there are extra words;
   - there are grey tones or gradients;
   - faces have features;
   - lines are drawn on top of the black;
   - it looks like smooth vector clip art.

   One or two retries per picture is normal.
5. **Save as PNG** with exactly the file name given, in `outputs/`. Don't upscale, crop, recolour or edit the files.
6. **Report:** list each file with its pixel size.

## Style block (send with every picture)

> A picture for the interior of a printed black-and-white mystery puzzle book set in Juniper Falls, a small American town in the 1950s. The mood is cozy and quietly mysterious, never gory: no bodies, no blood, no weapons in use.
>
> MEDIUM: a hand-cut black paper silhouette mounted on white paper, in the tradition of 1920s silhouette art. Everything is solid black paper. Detail is shown only by shapes cut out of the black, so the white paper shows through: lit windows are white openings with black outlines of people and objects inside; lettering is cut out of black signs. Scissor edges are slightly irregular, with fine delicate cutting in places and bold simple shapes elsewhere.
>
> NOT ALLOWED: grey, gradients, lines drawn on top, facial features, glow, smooth vector clip-art edges, a frame or border, any words other than the ones asked for.
>
> SIMPLICITY: one focal point. People are pure profile silhouettes, recognisable only by their outlines. Leave a plain white margin around the silhouette.
>
> COMPOSITION AND SUBJECT: …

## The pictures

| # | File | Shape | Composition |
|---|---|---|---|
| 1 | `case_bookstore.png` | done | street-level shop front |
| 2 | `case_bakery.png` | landscape 3:2 | **inside** the shop, looking down the room |
| 3 | `case_diner.png` | landscape 3:2 | long, low **side view** across a snowy lot |
| 4 | `case_inn.png` | landscape 3:2 | **three-quarter view** of a big house on a rise, firs and snow |
| 5 | `case_library.png` | landscape 3:2 | **symmetrical facade**, seen from the foot of the steps |
| 6 | `case_finale.png` | landscape 3:2 | **crowd from behind** in the foreground, town hall beyond |
| 7 | `title.png` | landscape 3:2 | **panorama** of the town from a hill |
| 8 | `map.png` | portrait 2:3 | **top-down** map |
| 9–13 | `evidence_*.png` | square | **one object**, centred, close up |
| 14 | `ornament.png` | landscape 3:2 | a small sprig |

### Subjects

**`case_bakery.png`.** COMPOSITION: an interior, seen from inside Rosie's Bakery, looking down the length of the room. We are indoors; the street is not shown except through one window at the far end.
- **Foreground:** the long contest table runs from the front of the picture into the room, covered with pies on cake stands, each with a little numbered card.
- **Overhead:** paper bunting zigzags across the ceiling, and two pendant lamps hang down.
- **Right:** three children in nursery-rhyme costumes in profile, a shepherdess with a crook, a little queen with a crown carrying a tray of tarts, and a boy holding a pie.
- **Left:** the judge's chair stands empty at the head of the table.
- **Back wall:** shelves of bread loaves, and a window showing a few falling leaves.
- **Lettering:** a hanging banner across the room lettered "HARVEST PIE CONTEST". Spell it exactly: H-A-R-V-E-S-T P-I-E C-O-N-T-E-S-T. No other words.
- **Do not include:** a shop front, an awning, a tree, a lamp post, a sandwich board, flowers, pumpkins, a bicycle.

**`case_diner.png`.** COMPOSITION: a long, low, side-on view across a snowy parking lot at dawn. Lou's Diner, a classic American diner car with rounded ends, stretches across most of the width, low in the frame, under a big empty sky with a thin crescent moon cut out of it.
- **Windows:** one long band of white cut-out windows runs along the car, showing the counter, stools, a coffee pot, and two or three customers in profile, one in a tall stovepipe hat.
- **Roof:** a tall sign on the roof lettered "LOU'S DINER", and steam curling from a vent.
- **Foreground:** a 1950s pickup truck parked at the left end, and tyre tracks in the snow.
- **Lettering:** spell it exactly: L-O-U-'-S D-I-N-E-R. No other words.
- **Do not include:** a tree, a lamp post, a sandwich board, flowers, pumpkins, a bicycle, a shop sign above a window.

**`case_inn.png`.** COMPOSITION: a three-quarter view, from below and to the left, of The Juniper Inn, a big old three-storey wooden inn with a steep roof, gables and a wraparound porch, standing on a rise.
- **Approach:** a curving drive with a horse-drawn sleigh and its driver in silhouette at the bottom right.
- **Setting:** tall dark fir trees (evergreens, not leafy trees) behind the house; falling snow as many small white cut-out flakes across the black night sky; a full moon.
- **Windows:** many tall white windows. In the biggest, two masked dancers in profile and a small winged Cupid figure.
- **Sign:** on the porch, a hanging sign lettered "THE JUNIPER INN". Spell it exactly: T-H-E J-U-N-I-P-E-R I-N-N. No other words.
- **Do not include:** a lamp post, a sandwich board, flowers, pumpkins, a bicycle, a leafy tree framing the side.

**`case_library.png`.** COMPOSITION: perfectly symmetrical and centred. The Juniper Falls Public Library seen head-on from the foot of its stone steps, looking slightly up.
- **Building:** a small classical building with two tall columns, a triangular pediment, and a tall arched window on each side of the door. The door is open, and in the white opening a long table of books wrapped in paper and string is visible, with one reader in profile choosing a book.
- **Lettering:** a banner hangs between the columns, lettered "BLIND DATE WITH A BOOK"; letters cut into the pediment read "PUBLIC LIBRARY".
- **Grounds:** two clipped round bushes topped with snow on either side of the steps, and a winter night sky with a few cut-out stars.
- **Spelling:** B-L-I-N-D D-A-T-E W-I-T-H A B-O-O-K and P-U-B-L-I-C L-I-B-R-A-R-Y. No other words.
- **Do not include:** a tree, a lamp post, a sandwich board, flowers, pumpkins, a bicycle.

**`case_finale.png`.** COMPOSITION: in the foreground, filling the bottom third, a crowd of townspeople seen from behind as large black silhouettes: hats, coats, scarves, one child on a shoulder. They face the Juniper Falls Town Hall in the middle distance.
- **Town hall:** a white clapboard building with a tall clock tower against a pale winter evening sky, shown as a black silhouette with white cut-out windows and a white clock face reading seven o'clock.
- **Background:** behind the town, a small dam and the flat line of a reservoir.
- **Lettering:** a notice board on the steps lettered "TOWN MEETING TONIGHT". Spell it exactly: T-O-W-N M-E-E-T-I-N-G T-O-N-I-G-H-T. No other words.
- **Do not include:** a tree framing the side, a lamp post, a sandwich board, flowers, pumpkins, a bicycle.

**`title.png`.** COMPOSITION: a wide panorama of Juniper Falls seen from a hill, as one long horizontal cut-paper silhouette.
- **Town:** a short Main Street of storefronts, a church steeple, a water tower and the town hall clock tower.
- **Landscape:** wooded hills behind, and a small waterfall on the river at the right edge of town, the falling water as white cut-out lines. Late autumn.
- **Light:** one single lit window, a white cut-out, in an otherwise dark street.
- **Lettering:** none at all.

**`map.png`** (portrait 2:3). COMPOSITION: a top-down illustrated town map of Juniper Falls as a cut-paper silhouette.
- **Ground and water:** the land is black paper; the river and the streets are white cut-outs. A small waterfall on the river is labelled "Juniper Falls"; upstream, a reservoir behind a dam is labelled "Hollow Creek Reservoir".
- **Streets**, labelled along them: "Main Street", "Maple Avenue", "Church Lane", "River Road".
- **Buildings:** small building silhouettes with labels: "Pell's Books", "Rosie's Bakery" and "Lou's Diner" (all on Main Street), and "The Juniper Inn", "Public Library", "Town Hall" and "Sheriff's Office".
- **Extras:** a few trees, a church, a compass rose, and a cut-out title banner at the top lettered "JUNIPER FALLS".
- **Lettering:** labels are white letters on small black banners, large enough to read. Spell every label exactly as given, and add no other words.

**`evidence_bookstore.png`** (square). COMPOSITION: one object, close up, centred. A single paper bookmark with a tassel, as a black silhouette, with a big numeral "1" cut out of it in white. No other words.

**`evidence_bakery.png`** (square). One object, close up, centred. A single prize rosette with two ribbon tails, as a black silhouette, with a big numeral "2" cut out of the centre in white. No other words.

**`evidence_diner.png`** (square). One object, close up, centred. A single diner order ticket held in a metal clip, as a black silhouette, with a big numeral "3" cut out of the ticket in white. No other words.

**`evidence_inn.png`** (square). One object, close up, centred. A single old hotel room key on a teardrop key tag, as a black silhouette, with a big numeral "4" cut out of the tag in white. No other words.

**`evidence_library.png`** (square). One object, close up, centred. A single old library borrower's card with a date grid cut into it, as a black silhouette, with a big numeral "5" cut out in white where the date stamp would be. No other words.

**`ornament.png`.** A small horizontal juniper sprig as a delicate black paper cut: a short twig with needles and three round berries, centred, with lots of white around it. No words.

## What the book's build does with each picture

- trims white margins;
- snaps to pure black and white, cut at double resolution so edges stay smooth;
- checks the resolution.

The map is the tight spot (1024 × 1536 from the tool), which is why its labels must be large.

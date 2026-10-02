# Pictures for Murder in Juniper Falls: the cut-paper silhouette prompts (final)

The style is chosen: **Style C, cut-paper silhouette**. The reference picture is the bookstore (`bookstore-C-cut-paper.png`, saved in the book as `case_bookstore.png`). Every other picture must look like it was cut by the same hand from the same black paper.

## Instructions for the image agent

1. **Attach the reference:** use `bookstore-C-cut-paper.png` as the **style reference image** for every picture. Take its medium, line weight, level of detail and the way white cut-outs show light. Take nothing else from it: no shop, no figures, no signs.
2. **Prompt:** for each picture, send the **style block** below plus that picture's **subject**.
3. **Shape:** landscape 3:2 unless the subject says square or portrait. Use the largest size the tool returns.
4. **Check before saving.** Regenerate if:
   - a word is misspelled;
   - there are extra words;
   - there are grey tones;
   - faces have features;
   - lines are drawn on top of the black;
   - it looks like smooth vector clip art.

   One or two retries per picture is normal.
5. **Save as PNG** with exactly the file name given, e.g. `case_bakery.png`, in `outputs/`. Don't upscale, crop, recolour or edit the files; the book's build does all of that.
6. **Report:** list each file with its pixel size.

## Style block (send with every picture)

> A picture for the interior of a printed black-and-white mystery puzzle book set in Juniper Falls, a small American town. The mood is cozy and quietly mysterious, never gory: no bodies, no blood, no weapons in use.
>
> STYLE REFERENCE: the attached image. Match its medium exactly: a hand-cut black paper silhouette mounted on white paper. Match its line weight, its level of detail, its slightly irregular scissor edges, and the way lit windows and lettering are white openings cut out of the black. Take nothing else from the reference image.
>
> MEDIUM: everything is solid black paper. Detail is shown only by shapes cut out of the black, so the white paper shows through.
>
> NOT ALLOWED: grey, gradients, lines drawn on top, facial features, glow, smooth vector clip-art edges, a frame or border, any words other than the ones asked for.
>
> SIMPLICITY: one focal point. People are pure profile silhouettes, recognisable only by their outlines. Leave a plain white margin around the silhouette.
>
> SUBJECT: …

## The pictures

| # | File | Shape | Where it goes |
|---|---|---|---|
| 1 | `case_bookstore.png` | done | Case One opening page |
| 2 | `case_bakery.png` | landscape 3:2 | Case Two opening page |
| 3 | `case_diner.png` | landscape 3:2 | Case Three opening page |
| 4 | `case_inn.png` | landscape 3:2 | Case Four opening page |
| 5 | `case_library.png` | landscape 3:2 | Case Five opening page |
| 6 | `case_finale.png` | landscape 3:2 | The Town Meeting opening page |
| 7 | `title.png` | landscape 3:2 | Title page, above the title |
| 8 | `map.png` | portrait 2:3 | Full page facing the introduction |
| 9–13 | `evidence_bookstore.png` … `evidence_library.png` | square | Each case's answer page |
| 14 | `ornament.png` | landscape 3:2 | The small divider under headings |

### Subjects

**`case_bakery.png`.** Rosie's Bakery on a November evening, seen from the sidewalk. The shop front fills the picture:
- **The window** is a big white cut-out showing a long table of pies on cake stands under paper bunting.
- **Figures:** three children in nursery-rhyme costumes in profile: a shepherdess with a crook, a little queen with a crown carrying a tray of tarts, a boy holding a pie.
- **Signs:** an awning over the window; a sign above it lettered "ROSIE'S BAKERY"; a chalkboard by the door lettered "HARVEST PIE CONTEST".
- **Extras:** a bicycle leaning on the wall, a few fallen leaves.
- **Lettering:** spell it exactly: R-O-S-I-E-'-S B-A-K-E-R-Y and H-A-R-V-E-S-T P-I-E C-O-N-T-E-S-T. No other words.

**`case_diner.png`.** Lou's Diner at dawn in December: a classic American roadside diner car with rounded ends, seen from the side.
- **Windows:** a row of white cut-out windows showing the counter, stools, a coffee pot, and two or three customers in profile, one in a tall stovepipe hat and one in a three-cornered hat.
- **Signs:** a tall sign on the roof lettered "LOU'S DINER"; a window sign lettered "PANCAKE BREAKFAST".
- **Extras:** snow on the roof and curb as white cut shapes; a curl of steam from a vent; a parked 1950s pickup truck.
- **Lettering:** spell it exactly: L-O-U-'-S D-I-N-E-R and P-A-N-C-A-K-E B-R-E-A-K-F-A-S-T. No other words.

**`case_inn.png`.** The Juniper Inn on New Year's Eve: a big old wooden country inn with a wraparound porch and a steep roof.
- **Snow:** falling snow as small white cut-out flakes against the black night.
- **Windows:** tall white cut-out windows showing two masked dancers in profile, a figure with small wings (a Cupid), and the curve of a grand staircase.
- **Porch:** lanterns, and a wreath on the door.
- **Sign:** a hanging sign lettered "THE JUNIPER INN". Spell it exactly: T-H-E J-U-N-I-P-E-R I-N-N. No other words.

**`case_library.png`.** The Juniper Falls Public Library on a February night: a small brick library with stone steps, two columns and a pediment.
- **Window:** one large white cut-out window shows a long table of books wrapped in paper and tied with string, and a reader in profile choosing one.
- **Lettering:** a banner over the door lettered "BLIND DATE WITH A BOOK"; the stone above the columns lettered "PUBLIC LIBRARY".
- **Grounds:** bare trees, and old snow on the lawn as white cut shapes.
- **Spelling:** B-L-I-N-D D-A-T-E W-I-T-H A B-O-O-K and P-U-B-L-I-C L-I-B-R-A-R-Y. No other words.

**`case_finale.png`.** Juniper Falls Town Hall on a winter evening: a white clapboard town hall with a clock tower, drawn as a black silhouette with white cut-out windows and clock face.
- **People:** townspeople in coats and hats climb the steps, in profile and from behind.
- **Notice board:** lettered "TOWN MEETING TONIGHT". Spell it exactly: T-O-W-N M-E-E-T-I-N-G T-O-N-I-G-H-T. No other words.
- **Background:** a small dam and the flat line of a reservoir under a pale sky.

**`title.png`.** Juniper Falls seen from a hill, as a wide panoramic cut-paper silhouette:
- a short Main Street of storefronts;
- a church steeple, a water tower and the town hall clock tower;
- wooded hills behind;
- a small waterfall on the river at the edge of town, the falling water as white cut-out lines;
- late autumn trees with a few leaves.

One single lit window, a white cut-out, in an otherwise dark street. No lettering at all.

**`map.png`** (portrait 2:3). An illustrated town map of Juniper Falls seen from above, as a cut-paper silhouette.
- **Ground and water:** the land is black paper; the river and the streets are white cut-outs. A small waterfall on the river is labelled "Juniper Falls". Upstream, a reservoir behind a dam is labelled "Hollow Creek Reservoir".
- **Streets**, labelled along them: "Main Street", "Maple Avenue", "Church Lane", "River Road".
- **Buildings:** small building silhouettes with labels: "Pell's Books", "Rosie's Bakery" and "Lou's Diner" (all on Main Street), and "The Juniper Inn", "Public Library", "Town Hall" and "Sheriff's Office".
- **Extras:** a few trees, a church, a compass rose, and a cut-out title banner at the top lettered "JUNIPER FALLS".
- **Lettering:** labels are white letters on small black banners, large enough to read. Spell every label exactly as given, and add no other words.

**`evidence_bookstore.png`** (square). A single paper bookmark with a tassel, large and centred, as a black silhouette, with a big numeral "1" cut out of it in white. No other words.

**`evidence_bakery.png`** (square). A single prize rosette with two ribbon tails, large and centred, as a black silhouette, with a big numeral "2" cut out of the centre in white. No other words.

**`evidence_diner.png`** (square). A single diner order ticket held in a metal clip, large and centred, as a black silhouette, with a big numeral "3" cut out of the ticket in white. No other words.

**`evidence_inn.png`** (square). A single old hotel room key on a teardrop key tag, large and centred, as a black silhouette, with a big numeral "4" cut out of the tag in white. No other words.

**`evidence_library.png`** (square). A single old library borrower's card with a date grid cut into it, large and centred, as a black silhouette, with a big numeral "5" cut out in white where the date stamp would be. No other words.

**`ornament.png`.** A small horizontal juniper sprig as a delicate black paper cut: a short twig with needles and three round berries, centred, with lots of white around it. No words.

## What happens to each picture in the book's build

- trims white margins;
- snaps every picture to pure black and white, cut at double resolution so the edges stay smooth;
- checks it prints at 300 DPI or more.

The map is the one tight spot: a full page needs about 1400 × 2100 px, and the tool returns 1024 × 1536. Because the map is pure black and white, re-cutting it at double size still prints crisp; only the smallest lettering would suffer, which is why the labels must be large.

# Cover prompt pack: *Who Sent the Killers?*

For the image agent. Read this whole file before generating anything.

## 0. Your job

Make **front covers** for a paperback puzzle book in three directions (A, B, C below).
- Make 2–3 versions of each and keep the best of each.
- Then compare the winners at Amazon search-result size and recommend one, with reasons.
- The person you work for picks the final cover; give them clear options.

**First, read OpenAI's own prompting guide for the image model** if you can reach it, and follow it:
- https://developers.openai.com/api/docs/guides/image-prompting
- https://developers.openai.com/cookbook/examples/multimodal/image-gen-models-prompting-guide
- a copy on GitHub: https://github.com/openai/openai-cookbook/blob/main/examples/multimodal/image-gen-models-prompting-guide.ipynb

If you can't reach them, the main points are in section 3.

## 1. The book

- **Title:** Who Sent the Killers?
- **Author:** Nora Clewes
- **What it is:** a find-the-killer murder mystery puzzle book for adults. The reader crosses names out of long printed lists of suspects, using clues, until one name is left.
- **The story:**
  - Juniper Falls is a cozy small American town.
  - Five people are murdered in five beloved places (a bookstore, a bakery, a diner, an inn, a library), each by a different killer.
  - All five killers were sent by one hidden mastermind.
  - In all: 18,000 suspects, 5 killers, 1 mastermind.
- **Buyers:** mostly women 40+ who love cozy mysteries and logic puzzles, plus gift buyers.
- **Interior art style:** hand-cut black paper silhouettes (1920s silhouette art). The cover should belong to the same family.

## 2. What the best-selling covers in this niche do (keep this) and where we stand out

Eight best sellers were studied: *The Killer Isn't Alice*, *The Killer Never Checked In*, *Who Killed Mr Darcy?*, *Eliminate!*, *The Killer Was On The Guest List*, *The Autumn Killer*, *The Lottery Killer*, *Find the Killer*.

**Keep, because buyers use these to recognise the genre:**
1. **The title is the picture.** Huge, heavy, condensed capitals fill 40–60% of the cover, stacked on 2–4 lines, with one word in an accent colour. It must be readable when the cover is 150 px wide.
2. **The game is shown:** a list of names with some neatly struck through and one circled.
3. **A silhouette.**
4. **The numbers line** in a strip or ribbon, e.g. "3,000 ENTRIES. 24 CLUES. 1 KILLER."

**Stand out, because the shelf is all the same:**
- **Colours:** 5 of the 8 are cream paper with black and red. The #1 seller stands out only because it is hot magenta. **Don't use cream-with-red, magenta, or orange-leaf autumn.**
- **Picture:** every winner shows a person or a document. **None shows a place.** Our town is our picture.
- **Silhouette:** ours is hand-cut paper (irregular scissor edges, delicate cut details), never flat vector clip art.

## 3. How to prompt the image model (from OpenAI's guide)

- **Structure every prompt in labelled parts**, in this order: the intended use, the scene or background, the subject, the key details, the text, the constraints.
- **Say what it is for:** "the front cover of a paperback puzzle book". That sets the level of polish.
- **Lettering:**
  - Put every word that must appear in quotes, in capitals.
  - Spell the tricky ones letter by letter.
  - Say the typeface style, size, colour and placement.
  - Say "no other text".
  - Use the highest quality setting, because cover text must be perfect.
- **Name the medium concretely:** hand-cut black paper, slightly irregular scissor edges, flat colours with no gradients. Avoid words that invite a glossy digital look.
- **Layout:** say where things go ("title fills the top half", "ribbon across the lower third").
- **Constraints:** state them plainly: no extra text, no watermark, no logos, no real brands, no gradients or glow, no faces with features.
- **Iterate in small single changes:** "keep everything the same, only make the title larger". Repeat what must not change on each round.
- **Don't feed an earlier cover back in as a reference** unless you want its layout copied. When images were given as style references for the interior pictures, the model copied the layout too.

## 4. Technical

- **Shape:** portrait 2:3, at the highest resolution available. The front panel prints at 6.125 × 9.25 in, including bleed.
- **Safe area:**
  - Keep all lettering at least 5% of the width away from every edge; KDP trims 1/8 in.
  - Keep the bottom 4% free of anything important.
- **No spine or back cover yet.** Front only.

## 5. The exact text (use exactly these words, spelled exactly)

| Element | Text |
|---|---|
| Title | "WHO SENT THE KILLERS?" (W-H-O S-E-N-T T-H-E K-I-L-L-E-R-S, then a question mark) |
| Numbers line | "18,000 SUSPECTS · 5 KILLERS · 1 MASTERMIND" |
| Genre line | "A FIND-THE-KILLER MURDER MYSTERY PUZZLE BOOK" |
| Author | "NORA CLEWES" (N-O-R-A C-L-E-W-E-S) |
| Small top line (optional) | "A JUNIPER FALLS MYSTERY" |

Any names in a list must be ordinary first names (Ruth, Harold, Joan, Walter, June, Arthur, Peggy, Frank, Edna, Louis…), legible but small. No other words anywhere.

## 6. The three directions

### A. "Five Lit Windows"

> USE: the front cover of a paperback murder-mystery puzzle book, to be seen as a small thumbnail on Amazon; bold and instantly readable.
>
> BACKGROUND: a deep midnight-blue night sky filling the cover, flat colour, no gradient.
>
> SUBJECT: across the bottom third, the small American town of Juniper Falls as a hand-cut black paper silhouette:
> - a Main Street of old storefronts;
> - a church steeple and a water tower;
> - in the centre, the town hall with a clock tower.
>
> KEY DETAILS:
> - Exactly five windows in the town glow warm gold, one in each of five buildings: a bookstore, a bakery, a diner, a big wooden inn, a library with columns.
> - One more small window high in the clock tower glows gold: the mastermind.
> - Every other window is dark.
> - Faint pale names drift across the sky like a list, a few neatly struck through, one circled in gold.
>
> TEXT:
> - Top half: "WHO SENT THE KILLERS?" in huge heavy condensed capitals, stacked on three lines (WHO SENT / THE / KILLERS?). The first two lines are cream; "KILLERS?" is warm gold.
> - Across the lower third, above the town: a cream ribbon reading "18,000 SUSPECTS · 5 KILLERS · 1 MASTERMIND" in dark blue condensed capitals.
> - Small cream capitals under the title: "A FIND-THE-KILLER MURDER MYSTERY PUZZLE BOOK".
> - At the bottom, on the dark ground: "NORA CLEWES" in cream capitals.
> - No other text.
>
> STYLE: hand-cut paper with slightly irregular scissor edges and flat colours only (midnight blue, black, cream, gold); no gradients, glow, light rays, photo texture or 3D. The gold windows are flat cut paper, not glowing.

### B. "Case File"

> USE: the front cover of a paperback murder-mystery puzzle book, to be seen as a small Amazon thumbnail.
>
> BACKGROUND: a manila case-file folder seen flat, filling the cover, with two small index tabs on the right edge, on a deep juniper-green desk border that frames it.
>
> SUBJECT:
> - Across the middle of the folder, a wide strip of the small American town of Juniper Falls as a hand-cut black paper silhouette, like a photo pinned to the file: storefronts, a church steeple, a water tower, a town hall with a clock tower.
> - Exactly five windows are cut out and lit gold.
>
> KEY DETAILS: below the strip, a typed list of ordinary first names in three columns. Several are struck through with neat pencil lines, and one is circled in red pencil.
>
> TEXT:
> - Top: "WHO SENT THE KILLERS?" in huge heavy black condensed capitals on three lines, with "KILLERS?" in deep juniper green.
> - A green band at the very top: "18,000 SUSPECTS · 5 KILLERS · 1 MASTERMIND" in cream capitals.
> - Under the title, small: "A FIND-THE-KILLER MURDER MYSTERY PUZZLE BOOK".
> - At the bottom, on a typed label stuck to the folder: "NORA CLEWES".
> - No other text.
>
> STYLE: flat, clean paper materials; the town is black cut paper with irregular scissor edges. No blood, no gradients, no glow, no photo realism. Accent colour green, not red.

### C. "The Five Tokens"

> USE: the front cover of a paperback murder-mystery puzzle book, to be seen as a small Amazon thumbnail.
>
> BACKGROUND: a deep teal ground, flat colour, no gradient.
>
> SUBJECT: across the middle, six cut-paper evidence tags in a neat row, like an evidence lineup. Each is a cream paper tag with a black cut-paper silhouette object and a large number:
> - 1: a bookmark with a tassel;
> - 2: a prize rosette;
> - 3: a diner order ticket on a clip;
> - 4: an old room key on a teardrop key tag;
> - 5: a library card.
> - The sixth tag is empty except for a large gold "?".
>
> KEY DETAILS:
> - Below the row, a small hand-cut black silhouette of a small-town skyline with a clock tower, along the bottom edge.
> - Faint names in the teal background, a few struck through.
>
> TEXT:
> - Top half: "WHO SENT THE KILLERS?" in huge heavy cream condensed capitals on three lines, with "KILLERS?" in gold.
> - A gold ribbon below the tags: "18,000 SUSPECTS · 5 KILLERS · 1 MASTERMIND" in dark teal capitals.
> - Small cream capitals under the title: "A FIND-THE-KILLER MURDER MYSTERY PUZZLE BOOK".
> - At the bottom: "NORA CLEWES" in cream capitals.
> - The numerals 1–5 and "?" on the tags.
> - No other text.
>
> STYLE: hand-cut paper, slightly irregular scissor edges, flat colours (teal, cream, black, gold). No gradients, glow, photo realism or 3D.

## 7. Checking each cover before keeping it

1. **Spelling:** read every word letter by letter against section 5. Any typo means regenerate.
2. **Thumbnail test:** shrink the cover to 150 px wide. The title must still be readable, and the cover should still read as "murder mystery puzzle book".
3. **Shelf test:** place the 150 px cover next to small versions of typical competitors (cream paper, black and red type, a magnifying glass, a silhouette). It should stand out, but still look like it belongs to the same shelf.
4. **No AI tells:** no glow, no gradients, no waxy faces, no garbled small text, no extra words, no plastic 3D look.
5. **Safe area:** nothing important within 5% of the edges.

## 8. What to hand back

- **The covers:**
  - the best cover of each direction: `cover_A.png`, `cover_B.png`, `cover_C.png`;
  - any runner-up worth seeing: `cover_A2.png` and so on.
- **One comparison image:** the three winners side by side at full size, and again at 150 px wide.
- **A short note,** for each cover: what works, what doesn't, how it did in the thumbnail and shelf tests, and which one you recommend and why.

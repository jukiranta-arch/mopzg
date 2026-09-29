# Brief: a "find the killer" murder mystery puzzle book

> **Correction, 2026-09-29.** The Amazon sample of *Who Killed Mr Darcy?* shows it is **not** a Regency or Austen book. It is set at "a film convention of fictional characters and their fans":
> - The register holds 31,830 names, mixing ordinary names with famous screen characters used under an "unofficial" disclaimer.
> - Chapter titles are film quotes.
> - The puzzle has 15 clues, each true of two suspects, and a final deduction at the back.
>
> What sells is a famous victim in the title, plus a world full of names readers recognize, plus a clean mechanic. The Regency angle below is withdrawn. The current lead is a **public-domain fairy-tale world**: *Who Killed Prince Charming?* Alternatives are *Who Killed Ebenezer Scrooge?* (Christmas, needs a mid-October launch) and *Who Killed Sherlock Holmes?* (trademark risk). The rest of this brief (format evidence, package, price, generator plan) still applies.

> **Decision, 2026-09-29: *Who Killed Prince Charming?*** Three fairy-tale searches ("who killed prince charming", "fairy tale murder mystery", "fairy tale puzzle book for adults", 113 results, `captures/inbox/*2026-09-29.json`) found:
> - **No find-the-killer puzzle book with a fairy-tale theme.** Every "killer" title in those results is a novel.
> - **Fairy-tale puzzle buyers exist:** *Dark Fairy Tales* coloring is at BSR 11,696 and *Enchanted Fantasy Puzzles* (hidden objects) at BSR 20,800.
> - **Avoid plain fairy-tale word searches:** 18 of them and almost all have 0 reviews.
>
> Generator: `whodunit/` (`python -m whodunit sample|book OUT.pdf`, needs reportlab).
> - It builds a guest register at the Happily Ever After Ball: ordinary names plus public-domain fairy-tale and nursery characters as landmarks (the Big Bad Wolf, Hansel, Gretel, the three bears, Kings and Queens).
> - It picks 13 clues and repairs the register until exactly two guests survive. The final deduction (the longer name is the killer) picks between them.
> - **Book preset:** 31,500 names, 13 clues, about 160 pages in 10 pt print.
> - **Sample case:** `briefs/samples/who-killed-prince-charming_sample.pdf`. It was checked by reading the names back out of the PDF and solving it with separate code.
>
> Execution risk: *Who Killed Count Dracula!* and *Who Killed Mr Danny?* use the same format and flopped. The theme has to be obvious on the cover and in the names, and the puzzle has to be fun to solve.

Captured on amazon.com, 2026-09-28. BSR = Best Sellers Rank on that day. All sales figures are estimates from BSR.

## In one line
Use the fastest-growing puzzle format on Amazon, "find the killer among thousands of suspects", in an original Regency-society setting. That setting is the one literary theme where buyers are proven to show up.

## Who buys and why
The buyers are women aged 35–70 who read Jane Austen, Regency romance and cozy mysteries. Some have just finished one of these puzzle books and want the next one. Others are looking for a gift for a reader in their life. Puzzle books get used up, so a buyer who liked one comes back for another.

## Evidence

**The format is booming, and newcomers win in it:**
- *The Killer Isn't Alice*, an indie book from February 2026, was picked up by Little, Brown. The new edition ranks **63**.
- *The Killer Never Checked In*: 88 days old, BSR 1,303, 60 reviews.
- *Kill Grid Vol. 1*: 84 days old, BSR 721.
- 30 of the 34 selling murder mystery puzzle books are under a year old.

**The Regency / Austen theme sells on its own:**
- *Who Killed Mr Darcy?* (B0H9PBXJSZ): 71 days old, BSR 5,380, about 17 a day, with only **6 reviews**.
- *Who Killed Mr Danny?*, apparently from the same publisher: same format, generic theme. It's 42 days old at BSR 441,676 with 0 reviews. **The theme made the difference.**
- *The Jane Austen Escape Room Book* (Andrews McMeel): BSR 12,679, 234 reviews.

**The other literary worlds are worse:**
- **Dracula** has been tried and failed. *Who Killed Count Dracula!* is 56 days old at BSR 369,100. *Bitten by Dracula* ranks 1,109,293.
- **Sherlock Holmes** puzzle books sell modestly (BSR 20,000–300,000), and the name carries trademark risk.
- **Gatsby** has no puzzle books with a rank and no proof of demand.

## The angle
- **An original Regency cast and story** instead of Austen's own characters. It stays out of *Mr Darcy*'s lane and lets you build a series with your own world and recurring detective.
- **Clues arrive as period documents:** society-page gossip, dance cards, letters and wills. This is the story-plus-puzzle mix that works for the cozy word-search mysteries (the *Cranberry Creek* series sells 5–41 a day per book).
- **A clear promise in the subtitle:** number of suspects, number of clues, one killer, and no guessing.

## Title options
The promise comes first and the keyword sits in the subtitle.
1. **Who Killed the Duke?** A Regency Murder Mystery Puzzle Book: Find the Killer Among 20,000 Guests With 18 Clues
2. **Murder at the Midnight Ball:** A Regency Whodunit Puzzle Book for Adults: 20,000 Suspects, 18 Clues, 1 Killer
3. **The Duke Is Dead:** A Find-the-Killer Murder Mystery Puzzle Book Set in Regency England
4. **Scandal, Sabotage & Murder:** A Regency Society Murder Mystery Puzzle Book for Adults

## The winning package
- **What the top sellers look like:**
  - *Mr Darcy*: 209 pages, $11.99.
  - *The Killer Isn't Alice*: 211–224 pages, $13.95–15.18.
  - *The Killer Never Checked In*: 178 pages, $6.99.
- **Recommended:** a 6×9 paperback with a black-and-white interior, about 200 pages, at **$12.99**.
- **Royalty:** about $4.40 per copy (60% of $12.99, minus about $3.40 printing).
- **Second book:** *Who Poisoned the Countess?* Winners here are series. Plan three titles from the start.

## Viability checks
- **Can it be made to a high standard?** Yes. The suspect lists and clues can be generated by code, and code can check that each puzzle has exactly one solution. Claude can write the story chapters in period voice.
- **Trademarks:** don't use "Bridgerton", "Lady Whistledown", "Murdle" or "Murdoku". Search the final title words in USPTO TESS before publishing.
- **Amazon's near-copy rule:** original characters, story and clue design keep it clearly distinct from *Mr Darcy*.
- **Not a health topic,** so there are no claims to avoid.

## Predicted outcome
Based on comparable books, not a guarantee.

| Case | Sales | About |
|---|---|---|
| Bad | about 0.3 a day | $40 a month |
| Average | about 3 a day | $400 a month |
| Good (performs like *Mr Darcy*) | about 15 a day | $2,000 a month |

Confidence: medium to high. The format is proven. The theme is proven by one title, now with a two-month sales history that keeps rising.

## Risks and unknowns
- The *Mr Darcy* publisher may bring out more Regency titles.
- Copycat waves hit this format fast, so publish soon and plan the series.
- ~~Only one day of rank data.~~ **Checked 2026-09-29** in the BookBeam rank history for *Mr Darcy*, published 2026-07-19:
  - **August:** first ranked around 40,000, then swung between 20,000 and 60,000.
  - **Late August:** climbed to 12,000–20,000.
  - **Since 10 September:** a steady climb to 5,000–7,000, now 5,702.
  - **Price:** raised from $12 to $13 in early August without hurting the climb, then returned to $11.99.
  - **Reading:** sales have grown steadily for two months on 6 reviews. That points to buyers finding it through search, not a launch spike, so the demand is real and still growing.

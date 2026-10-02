"""The words of the book: the town, each case's story, and the endings.

{killer} and {mastermind} are filled in from the generated book. The victims
are the five people who sat on the 1996 town council that voted to flood
Hollow Creek for the reservoir; the mastermind's family farm went under the
water.
"""

TITLE = "Murder in Juniper Falls"
SUBTITLE = ("Over 20,000 Suspects · 5 Linked Cases · 1 Mastermind · A Find-the-Killer Murder Mystery "
            "Puzzle Book")

COPYRIGHT = [
    "Copyright © 2026. All rights reserved.",
    "No part of this book may be reproduced in any form without written permission from the publisher, except "
    "for brief quotations in reviews.",
    "This is a work of fiction. Juniper Falls and everyone who lives there are imaginary. Any resemblance to real "
    "people, places or events is coincidental. Famous names in the lists are used only as puzzle landmarks.",
]

INTRO = [
    "Juniper Falls is the kind of town where everybody knows your name, your order at the diner, and which "
    "library books you never returned. Nothing much happens here. That is the point of the place.",
    "This autumn, something happened five times.",
    "Five people died in five of the town's best-loved places: the bookstore, the bakery, the diner, the inn and "
    "the library. Each time, on a crowded night, with the doors locked and every visitor's name written down. "
    "Each time, a small numbered token was left behind: 1, then 2, then 3. And on the back of the first one, in "
    "neat capitals: ONE OF FIVE.",
    "Five killers. One person behind them all.",
    "Sheriff Ruth Ambrose has the lists. She needs you to read them.",
]

HOW = [
    ("Five cases.", "Each case is one night in one place, with its own story, its own clues and its own list of "
     "names. Solve them in order."),
    ("One killer per case.", "Every clue in a case is true of that case's killer. Cross out every name a clue "
     "rules out. When all the clues are used, one name is left."),
    ("Check as you go.", "After each list there is an answer page with a check: the killer's name length and "
     "letter total. It tells you whether you are right without giving the name away. Get it right before you "
     "move on, because later cases need earlier answers."),
    ("The mastermind.", "The five killers were all sent their orders by the same person. The last chapter, The "
     "Town Meeting, uses all five of your answers to find them."),
    ("The solutions", "are at the very back of the book, upside down, behind a Stop page."),
]

BEFORE = [
    ("What is a name.", "A name is everything between two dots in a list: a single name (Rosa), a full name "
     "(Ada Finch), or a famous name (Oliver Twist). Each name is one person. Names repeat; each Rosa is a "
     "different Rosa."),
    ("Exact spelling only.", "When a clue names someone, only that exact name qualifies, on its own. Tom Sawyer "
     "is Tom Sawyer, not Tom Baker; Beth is Beth, not Beth Lowe; Juliet is Juliet, not Julie."),
    ("Letters in a name.", "When a clue looks at the letters in a name, count every letter of the whole name, "
     "A to Z. Spaces don't count: Ada Finch has eight letters."),
    ("Vowels and consonants.", "The vowels are A, E, I, O and U. Every other letter is a consonant, and Y is "
     "always a consonant."),
    ("Names don't break across rows.", "Every name sits whole on a row, as the dot at the end of each row shows."),
    ("Within a page, within ten names.", "“Within one page” means the page before, the same page or "
     "the page after. “Within 10 names” is counted in reading order, and the count carries on onto "
     "the previous or next page."),
    ("A few tips.", "The clues don't need to be tackled in the order they're given; read them all first and start "
     "with the ones that give you the biggest head start. Work in pencil, in case you change your mind."),
]

CASES = {
    "bookstore": dict(
        when="October",
        event="the Midnight Sale",
        list_name="the Midnight Sale sheets",
        story=[
            "For thirty years the heart of Main Street has been Pell's Books. Every October it holds its Midnight "
            "Sale: hot cider, half-price hardcovers, and a raffle for anyone who signs the sale sheet in the "
            "section where they shop. This year the whole town came.",
            "At five past midnight, Harriet Pell, who had owned the store since before most of her customers could "
            "read, was found slumped over the register. Doc Whitaker said it was her heart, until he smelled bitter "
            "almonds in her cup of cider.",
            "Tucked into the book on the counter was a bookmark nobody had seen before, stamped with a single "
            "number: 1. On the back, in neat capitals: ONE OF FIVE.",
            "Sheriff Ambrose locked the front door at a quarter past twelve. Nobody had left.",
        ],
        token="a bookmark stamped 1",
        ending="When Sheriff Ambrose read the name aloud, {killer} set down a paper cup of cider and said nothing at "
               "all. In {killer}'s coat pocket was a stamp pad and four blank bookmarks.",
    ),
    "bakery": dict(
        when="November",
        event="the Harvest Pie Contest",
        list_name="the tasting tickets",
        story=[
            "Rosie's Bakery has hosted the Harvest Pie Contest every November since 1979. For one evening the whole "
            "town crowds between the bread shelves and the coffee bar, signing a tasting ticket at each table they "
            "visit.",
            "The judge for twenty-five years was Walter Brandt, retired mayor and a man who could tell a lard crust "
            "from a butter crust with his eyes shut. At nine o'clock he tasted the last pie, said “remarkable”, "
            "and did not get up again.",
            "Under his plate was a blue ribbon, the kind the bakery gives for first prize. Someone had written a "
            "number on it: 2.",
            "Sheriff Ambrose had the doors locked before the ribbon was out of its envelope. She had seen a number "
            "like that before.",
        ],
        token="a prize ribbon marked 2",
        ending="{killer} was still holding a fork when Sheriff Ambrose sat down at the same table. “I baked "
               "it the way the letter said,” {killer} said quietly. “Almond, it said. Plenty of almond.”",
    ),
    "diner": dict(
        when="December",
        event="the Pancake Breakfast",
        list_name="the breakfast sign-up sheets",
        story=[
            "Every December, Lou's Diner opens at dawn for the Pancake Breakfast. Every plate raises money for the "
            "fire department, and every diner writes their name on the sign-up sheet by their table so Lou can "
            "thank them in the paper.",
            "Lou Castellano had flipped pancakes on that griddle for forty-one years. At half past seven, he poured "
            "himself his first coffee of the day. He never finished it.",
            "Clipped to the order wheel, among the tickets, was one nobody had written: no table, no order, just a "
            "number. 3.",
            "Sheriff Ambrose stood in the doorway and looked at the frosted windows, the full booths, the line at "
            "the takeout counter. “Nobody leaves,” she said. Nobody argued.",
        ],
        token="an order ticket marked 3",
        ending="{killer} had paid for breakfast with exact change and left no tip. Lou would have noticed that. "
               "In {killer}'s wallet the sheriff found a newspaper clipping from 1996, folded small.",
    ),
    "inn": dict(
        when="New Year's Eve",
        event="the New Year's Eve Ball",
        list_name="the ball's guest book",
        story=[
            "The Juniper Inn has thrown a New Year's Eve Ball since the night it opened. Guests sign the guest book "
            "in whichever room they ring in the new year, and the book goes back on the shelf with all the others.",
            "Margaret Ashby, the innkeeper, always watched the countdown from the top of the grand staircase. At "
            "midnight the room cheered, the band played, and Margaret was found at the bottom of the stairs.",
            "In her hand was a brass room key on a tag marked 4. The inn has no Room 4. It never has.",
            "The snow had started at eleven. By the time Sheriff Ambrose arrived, no one could have left if they "
            "had tried.",
        ],
        token="a room key tagged 4",
        ending="{killer} was the only guest who had not raised a glass at midnight. “She was on the council,” "
               "{killer} said, before the sheriff asked anything. “They all were. That's what the letter said.”",
    ),
    "library": dict(
        when="February",
        event="Blind Date with a Book night",
        list_name="the library's sign-in sheets",
        story=[
            "On the second Saturday of February, the Juniper Falls Public Library wraps a thousand books in brown "
            "paper for Blind Date with a Book night. Every reader signs in at the room where they pick their date.",
            "Arthur Quill, who had been town clerk for thirty years and a library volunteer for ten, went down to "
            "the local archive at eight o'clock to fetch more string. He did not come back up.",
            "On the archive table, beside him, lay a borrower's card with a single date stamp. Where the date "
            "should have been, it read: 5.",
            "Sheriff Ambrose had four killers in her cells and four letters burned to ash. She locked the library "
            "and sat down with the sign-in sheets. “The last one,” she said. “Then whoever sent "
            "them.”",
        ],
        token="a borrower's card stamped 5",
        ending="{killer} handed over the last letter unburned. It was not signed. But it was typed on the old "
               "council typewriter, the one that sits in the corner of the Town Hall to this day.",
    ),
}

FINALE = dict(
    story=[
        "Five victims: a bookseller, a judge, a cook, an innkeeper and a clerk. Sheriff Ambrose spread their "
        "names across her desk and saw what they shared.",
        "In 1996 they were the Juniper Falls town council. That spring they voted, five to none, to dam Hollow "
        "Creek for the new reservoir. Eleven farms went under the water. One family never forgave them.",
        "Every killer had been sent a letter. Every letter knew a secret that only someone in town could know. "
        "The mastermind lives here still.",
        "The sheriff called a Town Meeting, and the whole town came. Everyone signed the town register by the "
        "street they live on.",
        "Your five answers are all you need.",
    ],
    ending=[
        "The mastermind is {mastermind}.",
        "{mastermind} was nine years old when the water rose over Hollow Creek. The farmhouse is still down there, "
        "under forty feet of reservoir; on a dry summer you can see the top of the chimney.",
        "Thirty years is a long time to wait. Long enough to learn every secret in a small town, and to choose five "
        "people who would do anything to keep theirs.",
        "“I never touched any of them,” {mastermind} told Sheriff Ambrose. “I only wrote letters.”",
        "The sheriff put the old council typewriter in an evidence bag. Juniper Falls is quiet again. It is the "
        "kind of town where everybody knows your name, and now, everybody knows theirs.",
    ],
)

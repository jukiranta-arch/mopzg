"""What each case asks: its place, its famous names and its clues, each with a title and a witness line.

Every case uses different kinds of clue (village/clues.py), so no two cases play alike. Each night was a costume
night, which is why famous names turn up in the lists: book characters at the bookstore, nursery-rhyme characters
at the bakery, famous Americans at the diner, lovers and gods at the masked ball, authors at the library.

A plan's `chain` entry is filled in with the previous case's answer when the book is generated.
"""

from dataclasses import dataclass, field

from . import clues as C


@dataclass
class Plan:
    key: str
    number: str
    shop: str            # "The Bookstore"
    label: str           # how later clues refer to this case: "bookstore"
    place: str           # "Pell's Books"
    noun: str            # who signed the list
    chapters: list
    full_share: float    # share of ordinary entries with a surname
    clues: list          # (clue, title, story); a "chain" string marks the chain clue's slot
    chain: tuple = None  # (factory, title, story)
    eggs: list = field(default_factory=list)


PLANS = [
    Plan("bookstore", "One", "The Bookstore", "bookstore", "Pell's Books", "customer",
         ["Mystery & Crime", "Romance", "Cookbooks", "The Children's Corner", "The Reading Café"], 0.45, [
             (C.near_page("Tom Sawyer"), "The Straw Hats",
              "Three boys came as Tom Sawyer, straw hats and all. Harriet's assistant June saw the killer browsing "
              "close to one of them all night."),
             (C.odd_consonants(), "The Raffle Stub",
              "The killer bought a raffle ticket, and June wrote the name on the stub. She counted the consonants "
              "while the ink dried, as she always does: an odd number."),
             (C.group_chapter_not(("Meg", "Jo", "Beth", "Amy"), "March sisters",
                                  "the four sisters of Little Women"), "Little Women",
              "Four girls came as the March sisters and went everywhere together. Wherever all four of them signed, "
              "the killer didn't."),
             (C.near_group(("Athos", "Porthos", "Aramis"), "a Musketeer", "The Musketeers"), "All for One",
              "The fencing club came as the Three Musketeers and kept waving cardboard swords. One of them signed "
              "within ten names of the killer."),
             (C.ends_consonant(), "A Hard Stop",
              "When the killer gave a name at the till, June says, it ended with a hard stop, not trailing away on "
              "a vowel."),
             (C.between("Romeo", "Juliet"), "Star-Crossed",
              "Romeo and Juliet signed at opposite ends of the store and spent the night looking for each other. "
              "The killer signed somewhere between them."),
             (C.double_letter(), "The Spelling Bee",
              "Mr Pell's nephew checks every sale sheet for spelling. He remembers the killer's name for one "
              "reason: a double letter."),
             (C.pair_page("Marilla Cuthbert", "Gilbert Blythe"), "Green Gables",
              "Two of the Green Gables crowd, Marilla Cuthbert and Gilbert Blythe, kept ending up on the same sale "
              "sheet. The killer's sheet had both of them."),
             (C.last_two_in_order(), "The Label",
              "Doc Whitaker found a torn label in the trash: the last two letters of a name, in the killer's hand. "
              "They run in alphabetical order."),
         ],
         eggs=["Huckleberry Finn", "Ichabod Crane", "Rip Van Winkle", "Hester Prynne", "Jay Gatsby", "Captain Ahab",
               "Oliver Twist", "Ebenezer Scrooge", "Jane Eyre", "Phileas Fogg", "Dorian Gray", "Captain Nemo"]),

    Plan("bakery", "Two", "The Bakery", "bakery", "Rosie's Bakery", "taster",
         ["The Bread Shelves", "The Pie Table", "The Cake Counter", "The Cookie Jar", "The Coffee Bar"], 1.0, [
             (C.within_pages("Simple Simon", 2), "The Pieman",
              "The children's choir came in nursery-rhyme costumes. Simple Simon, looking for the pieman, signed "
              "only once, and the killer's ticket is filed within two pages of his."),
             (C.none_of("JQ"), "The Broken Stamp",
              "Rosie's ticket stamp lost its J and its Q years ago. The killer's ticket came out perfectly, so "
              "neither letter is in the name."),
             (C.facing_page("Queen of Hearts"), "She Made Some Tarts",
              "The Queen of Hearts guarded the tart table all evening. In the bound ticket book, the page facing "
              "the killer's page has her name on it."),
             (C.surname_longer(), "The Prize Slip",
              "Rosie writes out every prize slip by hand. She remembers the killer's surname running on longer than "
              "the first name."),
             (C.page_before(("Little Bo Peep", "Little Boy Blue", "Little Miss Muffet"), "one of the Littles"),
              "Lost Sheep",
              "Little Bo Peep, Little Boy Blue and Little Miss Muffet roamed the bakery all night. One of them "
              "signed the page just before the killer's."),
             (C.no_double_letter("first"), "Piped in Icing",
              "The killer won a slice of the raffle cake with their first name piped on it. The decorator never had "
              "to pipe the same letter twice in a row."),
             (C.not_chapter_edge(), "The Middle of the Pile",
              "Each table's tickets were stacked four pages deep. The killer's ticket was somewhere in the middle "
              "of a stack, never on top and never at the bottom."),
             (C.initial_in_surname(), "Front and Back",
              "Walter Brandt's last note, found under his plate, said only: “same letter, front and back.” "
              "The first letter of the killer's first name turns up again in the surname."),
         ],
         chain=(C.chain_last_letter, "The Torn Bookmark",
                "Pinned to the ribbon was a scrap of bookmark from Pell's. It links the two nights: this killer's "
                "name contains the last letter of the bookstore killer's name."),
         eggs=["Peter Piper", "Mother Hubbard", "Jack Sprat", "Wee Willie Winkie", "Georgie Porgie",
               "Polly Flinders", "Doctor Foster", "Humpty Dumpty", "Mother Goose"]),

    Plan("diner", "Three", "The Diner", "diner", "Lou's Diner", "diner",
         ["The Counter", "The Booths", "The Window Tables", "The Back Room", "The Takeout Line"], 0.45, [
             (C.duo_chapters_not((("Meriwether Lewis", "William Clark"), ("Orville Wright", "Wilbur Wright"),
                                  ("Annie Oakley", "Buffalo Bill")), "a famous pair"), "Partners",
              "The history club came as famous Americans. Three famous pairs each claimed a part of the diner, one "
              "partner signing first on its sheets and the other signing last. The killer sat with none of them."),
             (C.contains("R"), "The Order Slip",
              "The waitress wrote the killer's name on an order slip. She remembers the R; she always loops her Rs."),
             (C.first_letter_of_page(), "First in Line",
              "Each sign-up sheet starts with whoever got there first. The killer's name contains the first letter "
              "of the name at the top of the killer's sheet."),
             (C.chapter_exactly_twice("Benjamin Franklin"), "Two Franklins",
              "Benjamin Franklin was a popular costume this year: a kite, a key and little round spectacles. The "
              "part of the diner where the killer sat had exactly two of him."),
             (C.at_least_vowels(4), "Called at the Pass",
              "Lou called the killer's order out loud at the pass. The name sounded long and open, he said: at "
              "least four vowels."),
             (C.flank(), "Squeezed In",
              "The sheriff noticed something about the names either side of the killer's on the sheet: the one "
              "before comes earlier in the alphabet than the one after."),
             (C.all_letters_different(), "The Check",
              "The killer paid by check. The bank clerk who cashed it says no letter in the name repeats."),
             (C.beyond_pages("Abraham Lincoln", 4), "Honest Abe",
              "Abraham Lincoln sat in the corner booth all morning and swears he saw nothing. The killer was never "
              "near him: more than four pages away."),
         ],
         chain=(C.chain_first_letter_of_surname, "From the Bakery",
                "Under the ticket marked 3 someone had pinned a tasting ticket from Rosie's: this killer's name "
                "contains the first letter of the bakery killer's surname."),
         eggs=["Betsy Ross", "Paul Revere", "Davy Crockett", "Johnny Appleseed", "Amelia Earhart", "Daniel Boone",
               "Calamity Jane", "Pecos Bill", "Thomas Jefferson", "George Washington"]),

    Plan("inn", "Four", "The Inn", "inn", "the Juniper Inn", "guest",
         ["The Ballroom", "The Bar", "The Grand Staircase", "The Garden Room", "The Library Lounge"], 1.0, [
             (C.one_not_both("Napoleon", "Josephine"), "Not Tonight",
              "It was a masked ball, and Napoleon and Josephine quarrelled at ten. On the killer's page of the guest "
              "book, one of them signed, but not both."),
             (C.first_at_least(5), "The Place Card",
              "The killer's place card was found by the punch bowl. The first name on it ran to five letters at "
              "least."),
             (C.in_chapter_with("Cupid"), "Cupid's Arrow",
              "Cupid flitted between two rooms all night with a bow and a quiver of paper hearts. The killer was in "
              "a room where Cupid signed."),
             (C.surname_begins_consonant(), "Announced at the Door",
              "The doorman announced every guest by surname. The killer's surname opened hard, on a consonant."),
             (C.no_letter_with_page_first(), "Strangers",
              "The first guest on each page of the guest book signed at the top. The killer had nothing in common "
              "with that guest: their first names share not one letter."),
             (C.repeated_letter("surname"), "The Monogram",
              "The killer's cloak had a monogrammed lining. The tailor recalls that the surname used one letter "
              "twice."),
             (C.near_group(("Zeus", "Hera", "Apollo", "Athena"), "a Greek god", "The Greek gods", 8), "Olympus",
              "The gods of Olympus held court by the champagne. One of them signed within eight names of the "
              "killer."),
             (C.whole_at_most(13), "The Name Tag",
              "Name tags at the ball had room for thirteen letters at most, and the killer's fitted without "
              "squeezing."),
         ],
         chain=(C.chain_same_first_length, "As Long as the Last",
                "The key tagged 4 came with a typed card: “as long as the last one.” This killer's first "
                "name has as many letters as the diner killer's first name."),
         eggs=["Lancelot", "Guinevere", "Tristan", "Isolde", "Orpheus", "Eurydice", "Antony", "Cleopatra",
               "Heathcliff", "Catherine Earnshaw"]),

    Plan("library", "Five", "The Library", "library", "the Juniper Falls Public Library", "reader",
         ["The Reading Room", "The Stacks", "The Reference Desk", "The Children's Library", "The Local Archive"],
         0.45, [
             (C.not_on_page_with(("Charlotte", "Emily", "Anne"), "the Brontë sisters"), "Three Sisters",
              "Readers came dressed as their favourite authors. The three Brontë sisters kept the killer at a "
              "distance: no sister signed the killer's page."),
             (C.alphabet_neighbours(), "The Card Catalogue",
              "The librarian filed the killer's borrower card and noticed two letters side by side in the name "
              "that are also neighbours in the alphabet."),
             (C.between("Charles Dickens", "Edgar Allan Poe"), "A Tale of Two Authors",
              "Charles Dickens and Edgar Allan Poe each signed once, at opposite ends of the building. The killer "
              "signed somewhere between them."),
             (C.even_length(), "The Typewriter",
              "The killer's name was typed on a sign-up card. The typist remembers an even number of letters."),
             (C.even_page(), "Left-Hand Pages",
              "Every sign-in sheet was bound into a book. The killer's sheet is on the left of an open spread: an "
              "even-numbered page."),
             (C.contains("E"), "The Stamp",
              "The date stamp on the killer's book smudged across an E in the name."),
             (C.initial_of_page_last(), "Last to Sign",
              "Whoever signed last on each sheet matters here: the killer's name begins with the same letter as the "
              "last name on the killer's sheet."),
         ],
         chain=(C.chain_shares_no_letter, "Nothing in Common",
                "The borrower card stamped 5 had a pencilled note: this killer's surname shares no letter with the "
                "inn killer's first name."),
         eggs=["Herman Melville", "Victor Hugo", "Virginia Woolf", "Louisa May Alcott", "Jules Verne",
               "Mark Twain", "Walt Whitman", "Robert Frost"]),
]

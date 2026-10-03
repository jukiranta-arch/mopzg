"""Name pools for the register. Ordinary names fill most of it; public-domain
fairy-tale and nursery-rhyme characters are the landmarks and Easter eggs."""

FIRST = """Aaron Abigail Ada Adam Adrian Agnes Aiden Alan Albert Alec Alexa Alfie Alice Alina Allison Alma
Amber Amelia Amir Amos Amy Ana Andre Andrea Angela Anita Ann Annie Anton Archie Ariel Arlo Arthur
Asha Audrey Austin Ava Barbara Barney Basil Beatrice Bella Ben Benedict Bernard Bess Beth Betty
Bianca Blake Bonnie Boris Brenda Brian Bridget Bruno Caleb Calvin Camille Carl Carla Carmen Carol
Caroline Carter Casey Cassie Cecil Cecily Celia Chad Charlie Chloe Clara Clarence Claude Clive Cody
Colin Connor Cora Craig Cyril Daisy Dale Damian Dana Daniel Daphne Darius Dawn Dean Delia Derek
Diana Dina Dolly Dominic Donald Dora Doris Dorothy Duncan Dylan Edgar Edith Edmund Edwin Eileen Elena
Eli Eliza Ella Ellis Elmer Elsa Elsie Emil Emma Enid Eric Erin Ernest Esme Ethan Eva Evan Evelyn
Fabian Faith Felix Fern Fiona Flora Floyd Frances Frank Freddie Freya Gail Gareth Gavin Gemma George
Gerald Gilbert Gina Glenn Gloria Gordon Grace Graham Greta Gus Gwen Hal Hannah Harold Harriet Harvey
Hazel Heath Hector Heidi Helen Henry Hilda Holly Horace Howard Hugh Hugo Ian Ida Imogen Ingrid Iris
Irma Isaac Isla Ivan Ivy Jack Jacob Jade Jake James Jane Jasmine Jason Jean Jeff Jenna Jerome Jess
Jill Joan Joel John Jonah Josie Joy Jude Julia Julian June Karen Karl Kate Keith Kelly Kenneth Kevin
Kim Kirk Kit Lana Lance Laura Leah Lena Leo Leon Leroy Lewis Liam Lila Linda Lionel Lisa Lloyd Lois
Lola Lorna Louis Lucy Luke Lydia Mabel Madge Maggie Malcolm Marcus Margo Maria Marian Mark Martha
Martin Mavis Max Maya Megan Mel Mia Miles Milly Miriam Molly Monty Muriel Myra Nadia Nancy Naomi Nate
Neil Nell Nia Nick Nina Noah Nora Norman Olive Oliver Omar Oscar Owen Paige Pam Pansy Patrick Paul
Pearl Peggy Penny Percy Peter Phil Phoebe Piper Polly Quentin Quinn Rachel Ralph Ray Rebecca Reggie
Rhoda Rhys Rita Robin Roger Rolf Rosa Rosalind Ross Roy Ruby Rufus Rupert Ruth Ryan Sadie Sally Sam
Sandra Sara Saul Scott Selma Seth Shane Sheila Sid Silas Simon Sofia Stan Stella Stuart Susan Sybil
Tamsin Tara Ted Tess Thea Theo Tilly Tim Tina Toby Todd Tom Trevor Trudy Una Ursula Val Vera Vic
Viola Violet Vivian Wade Wally Walter Wanda Wendy Wes Wilbur Will Willa Winnie Xavier Yara Yvonne
Zach Zara Zelda Zoe""".split()

LAST = """Abbott Acres Ainsley Alder Ashby Ashton Atwood Bailey Baker Banks Barlow Barnes Barton Baxter
Beck Bell Bennett Berry Birch Bishop Black Blake Bloom Booth Bower Boyd Bradley Brand Brewer Briggs
Brook Brooks Brown Buckley Bunting Burke Burns Butler Byrne Cage Caldwell Carr Carter Cary Chalk Chase
Clark Clay Cobb Cole Collins Cook Cooper Cotton Crane Croft Cross Crow Dale Dalton Dane Darby Davies
Day Dean Denton Dixon Doyle Drake Drew Duffy Dunn Eaton Elder Ellis Emery Evans Fairfax Farley Fenn
Finch Fisher Fleming Fletcher Flint Ford Forrest Foster Fox Frost Fuller Gale Gardner Garland Gibbs
Glass Glover Goode Gould Grant Gray Green Grove Hale Hall Hardy Harlow Harper Hart Hawkes Hayes Heath
Hill Hobbs Holland Holt Hood Hope Horne Hughes Hunt Hurst Ivory Jarvis Jenkins Keane Kemp Kent Kerr
Knight Lake Lamb Lane Lark Lawson Lea Lister Lock Long Lowe Lucas Lyle Mace Mann Marsh Mason May
Mercer Miles Miller Moon Moore Morrow Moss Nash Nightingale Noble North Norton Oakes Orchard Page
Palmer Parker Parr Payne Pearce Penn Perry Pike Pine Platt Pond Poole Potter Price Quill Quinn Rain
Ray Reed Rhodes Rich Ridley Rivers Robin Rook Rose Ross Rowe Rush Russell Sage Salter Sands Saxon
Scott Shaw Shepherd Silver Sloane Snow Sparrow Spencer Stark Steele Stone Swan Sykes Tate Temple
Thorne Todd Tower Tucker Turner Vance Vale Wade Walker Ward Warren Waters Webb Wells West Wheeler
White Wilde Winter Wolfe Wood Woods Wren Wright Yates York Young""".split()

# Titles that may start an ordinary entry ("Dr Ada Finch", "Mrs Lark").
TITLES = []   # no titles: guests are single first names, as in the best-selling books of this kind

# Public-domain fairy-tale and nursery-rhyme characters used as colour.
# (Grimm, Perrault, Andersen, Mother Goose. Nothing from later film versions.)
CHARACTERS = """Cinderella|Snow White|Rose Red|Rapunzel|Rumpelstiltskin|Little Red Riding Hood|Goldilocks|Tom Thumb|Thumbelina|Puss in Boots|Bluebeard|Briar Rose|Fairy Godmother|Little Bo Peep|Little Boy Blue|Jack Sprat|Mother Hubbard|Mother Goose|Humpty Dumpty|Georgie Porgie|Simple Simon|Wee Willie Winkie|Jack Horner|Mistress Mary|Tom Tom|Peter Piper|Lucy Locket|Kitty Fisher|Jack Frost|Mother Holle|Faithful John|Iron John|Ali Baba|Aladdin|Sinbad|Scheherazade|Ugly Duckling|Steadfast Tin Soldier|Little Match Girl|Twelve Huntsmen|Goose Girl|Brave Tailor|Pied Piper|Beauty|Beast|Huntsman|Woodcutter|Miller's Daughter|Golden Goose|Hans in Luck|Lazy Jack|Jack the Giant Killer|Tooth Fairy|Sandman""".replace("\n", "").split("|")

# Chapter titles: public-domain lines from the tales.
CHAPTER_QUOTES = [
    "Once upon a time…",
    "Mirror, mirror, on the wall",
    "Who’s been sleeping in my bed?",
    "All the better to see you with",
    "Rapunzel, Rapunzel, let down your hair",
    "Fee-fi-fo-fum",
    "Nibble, nibble, like a mouse",
    "Spin, spin, straw into gold",
    "I’ll huff, and I’ll puff",
    "Not by the hair of my chinny chin chin",
    "Humpty Dumpty sat on a wall",
    "And they all lived happily ever after",
]

# Royal guests: every name with King, Queen, Prince or Princess in it. All public-domain tales.
ROYALS = ["Snow Queen", "Frog King", "Frog Prince", "Old King Cole", "Evil Queen", "Queen of Hearts",
          "King of Hearts", "King Thrushbeard", "Mouse King", "Swan Princess", "Pea Princess", "Goose Princess"]
ROYAL_WORDS = {"King", "Queen", "Prince", "Princess"}

# Chapters are places in the palace: rooms inside, or places in the grounds. Each has its own scene.
PLACES_INDOOR = {
    "The Ballroom": "The orchestra had stopped mid-waltz. Six hundred pairs of dancing shoes had scuffed the floor, "
                    "and every guest swore they had been dancing with somebody else at midnight.",
    "The Grand Staircase": "The glass slipper was found on the eleventh step at five past twelve. It fitted nobody "
                           "the guards tried it on, which was a relief to Cinderella, who was wearing both of hers.",
    "The Kitchens": "Hansel and Gretel were found here, surrounded by gingerbread. They insisted they had followed a "
                    "trail of crumbs from the ballroom, laid by someone who did not want to be followed.",
    "The Library": "The Mirror had been moved to the library for safekeeping. Asked who was fairest, it answered at "
                   "once. Asked who had killed the Prince, it went quiet, and then very politely cracked.",
    "The Long Gallery": "Rumpelstiltskin refused to give his name, which was odd, since it was already in the "
                        "register. He spent the interview spinning straw into gold and muttering about a favour.",
    "The Throne Room": "The King and Queen held court until dawn. The Queen wanted to know who had touched the cake. "
                       "The King wanted to know who had eaten the rest of it.",
    "The Banqueting Hall": "The wedding cake stood seven tiers high. Mama Bear noticed that somebody had tasted all "
                           "three icings. Papa Bear noticed the Prince had not. Baby Bear noticed everything.",
    "The Wine Cellar": "Puss in Boots had a perfect alibi, a signed menu, and three witnesses who would swear to "
                       "anything for a sardine. The guards thanked him and crossed nothing off at all.",
    "The Tower Stair": "Rapunzel had watched the whole ball from the top of the tower. “Two guests went down the "
                       "servants’ stair at a quarter to twelve,” she said. “I could only see their hats.”",
    "The Mirror Hall": "A hundred mirrors lined the walls, and every one of them showed a different guest leaving at "
                       "midnight. The guards decided that mirrors do not make reliable witnesses.",
}
PLACES_OUTDOOR = {
    "The Palace Gates": "The gatekeeper swore that nobody had left since the first stroke of midnight. “Every guest "
                        "who came in is still here,” he said, “and every one of them is in your book.”",
    "The Rose Garden": "Little Red Riding Hood had watched the Big Bad Wolf by the rose bushes all evening. “He was "
                       "far too polite,” she said. “Wolves are never polite.”",
    "The Hedge Maze": "Three guests got lost in the maze at eleven and were found at dawn, still arguing about which "
                      "way was left. They were, at least, not suspects.",
    "The Carriage Yard": "Every pumpkin in the yard had been a carriage at some point that evening. The coachmen had "
                         "seen nothing, having been mice for most of the night.",
    "The Moat Bridge": "The Frog King sulked under the bridge. Someone had kissed him at a quarter to midnight and he "
                       "had stayed a frog. “That,” he said darkly, “was not a princess.”",
    "The Orchard": "The Snow Queen had frozen one corner of the orchard. The ice showed footprints heading back to "
                   "the palace: small, quick and, the guards agreed, in a great hurry.",
}

# The story layer of each clue card: what a witness says. The rule under it is what counts.
WITNESS = {
    "chapter_indoors": "“From my tower I could see the whole of the grounds,” says Rapunzel. “Nobody slipped out "
                       "into the gardens. Whoever it was stayed inside the palace.”",
    "three_bears": "“I saw them!” says Baby Bear, and for once somebody listens. The Three Bears were never far from "
                   "the killer all night.",
    "between_hansel_gretel": "“We came in separately,” says Gretel. “Hansel with the first guests, me with the last. "
                             "The killer arrived somewhere in between.”",
    "near_wolf": "“The Wolf was never far away,” says Little Red Riding Hood. “Wherever that guest went, he went too.”",
    "royal_on_page": "“A crown was reflected right beside them,” says the Mirror. It will not say whose.",
    "odd_page": "“I kept time all night,” says the Pied Piper. “They were always on the odd beat.”",
    "near_character": "“They stood close to someone out of a story,” says the Tooth Fairy. “Ten guests away, "
                      "no more. I counted teeth.”",
    "odd_consonants": "“Names are my business,” says Rumpelstiltskin. “That one had an odd number of consonants. "
                      "I counted them twice.”",
    "even_vowels": "“It was a name you could sing,” says the Pied Piper. “An even number of vowels in it.”",
    "ends_consonant": "“It ended hard,” says the Town Crier, who announced every guest. “On a consonant.”",
    "double_letter": "“There was a double letter in it,” says the Brave Tailor, who stitched every place card. "
                     "“Two of the same, side by side.”",
    "first_half": "“Early in the alphabet,” says Mother Goose, who wrote the invitations. “A to M, I’m certain.”",
    "last_two_rising": "“The last two letters were in order,” says the Fairy Godmother. “Like A then B. "
                       "I notice these things.”",
    "key_letter": "“They shared a letter with the first guest on their page,” says the Captain of the Guard, "
                  "who wrote the register.",
}

# The ending, printed upside down at the very back. The killer is always "they".
MOTIVES = [
    "Years ago the Prince had promised {killer} the last dance at his wedding, and tonight he had given it "
    "to somebody else.",
    "The Prince had borrowed {killer}’s best horse for a quest three summers ago and never brought it back.",
    "The Prince had once won a singing contest that {killer} was certain they should have won, and they had "
    "been practising their revenge ever since.",
    "The Prince had promised to marry {killer} in a letter, and then again in another letter, and then "
    "married someone else.",
]
ENDING = [
    "It was {killer}.",
    "When the Fairy Godmother saw the last two names she pointed at once to the longer one. {killer} had "
    "slipped away from the dance floor at a quarter to midnight, taken the servants’ stair down to the "
    "kitchens, and added something to the icing on the wedding cake.",
    "{motive}",
    "The other guest, {innocent}, had only stepped outside for some air, and was very embarrassed to have "
    "been suspected.",
    "The guards led {killer} away at dawn. The wedding cake was thrown in the moat, and the Big Bad Wolf, "
    "who had been blamed for everything all night, received a formal apology and a slice of something else.",
]

# More first names, for variety (the best sellers use thousands of different names) and so that
# enough names pass every letter clue.
FIRST += """Abbie Abel Addison Adele Adrienne Agatha Ainsley Alana Alastair Alba Alden Aldo Alexis Alfred
Alistair Allegra Alvin Amanda Ambrose Anders Angus Annabel Annika Ansel Antonia April Arabella Archer
Ardith Arnold Artie Ashley Astrid Aubrey Audra Augusta Aurelia Autumn Avery Axel Barnaby Barrett Beatrix
Beck Benny Bertram Bettina Beverly Billie Bjorn Blair Blanche Bobbie Bonita Bradley Bram Brandon Brenna
Brett Brooke Bryce Buddy Byron Callum Calvin Cameron Candace Carina Carlton Carrie Caspar Cassius Cecilia
Cedric Celeste Chandler Charity Chester Christa Ciara Clair Clancy Clement Cliff Cole Collette Conrad
Constance Cooper Corinne Cornelia Crispin Curtis Cynthia Dallas Damon Danielle Darby Darcy Darren Davina
Della Delphine Denise Dennis Desmond Dexter Dianne Dobbin Dolores Donna Dorian Douglas Drew Dudley Dustin
Earl Easton Eddie Edgar Edna Eleanor Elliott Eloise Elton Emery Emmett Enoch Esther Etta Eugene Eunice
Everett Ezra Fanny Felicity Fergus Finley Finn Fletcher Florence Forrest Francis Frederick Gabriel
Garrett Gemma Geneva Georgia Gideon Gillian Ginny Giles Gordon Greer Gregory Griffin Gustav Gwendolyn
Hamish Hank Hattie Hayden Heather Henrietta Herbert Hilary Hollis Hope Hubert Humphrey Ingram Irene
Isadora Isobel Jacqueline Jarrett Jasper Jemima Jennifer Jessamy Jethro Joanna Jocelyn Jolene Jordan
Josephine Judd Juliet Justin Kasper Katrina Keegan Kellan Kendall Kerry Kieran Kitty Kurt Lachlan Lara
Laurel Lawrence Leander Lenny Leonora Lester Lettie Lillian Linnea Lionel Lorenzo Loretta Lottie Louisa
Lowell Luther Lyle Mabel Maddox Magnus Mallory Marcella Margot Marlowe Marnie Matilda Maxwell Maynard
Melody Merrill Mervyn Millie Minnie Mitchell Morgan Morris Murray Nadine Nathaniel Nell Nessa Nigel
Noelle Norris Octavia Odette Ogden Olga Orson Otis Otto Pamela Parker Patience Perry Petra Philippa
Phyllis Pippa Porter Posy Prudence Quincy Raffles Rafferty Randall Reuben Rex Rhett Robbie Roland
Rollo Romilly Rosalie Roscoe Rowan Russell Sabrina Sallie Sawyer Scarlett Sebastian Serena Seymour
Shelby Sherman Sherry Sienna Sylvester Tabitha Tallulah Tanner Tatum Teddy Terrence Thaddeus Thomas
Tobias Trixie Tristan Truman Tucker Valentine Vaughn Verity Vernon Victor Vincent Virgil Wallis Warren
Wendell Wesley Whitney Wilfred Willard Willow Winston Wyatt Yolanda Yvette Zachary Zelda Zeke
Abbott Allegra Anneka Barrie Bessie Billy Carroll Cassie Cherry Chuck Dolly Ellie Emmy Essie Garry
Harry Holly Jenny Jimmy Johnny Kenny Kelsey Larry Libby Lizzie Maggie Matty Molly Nanny Neddy Olly
Peggy Penny Poppy Robby Sally Sammy Sonny Tammy Terry Tilly Tommy Wally Willy Winnie""".split()
FIRST = sorted(set(FIRST))

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
TITLES = ["Mr", "Mrs", "Miss", "Dr", "Sir", "Lady", "Dame", "Lord", "Captain", "Old", "Little"]

# Public-domain fairy-tale and nursery-rhyme characters used as colour.
# (Grimm, Perrault, Andersen, Mother Goose. Nothing from later film versions.)
CHARACTERS = """Cinderella|Snow White|Rose Red|Rapunzel|Rumpelstiltskin|Little Red Riding Hood|Goldilocks|
Tom Thumb|Thumbelina|Puss in Boots|Bluebeard|Briar Rose|Fairy Godmother|Evil Queen|Old King Cole|
Little Bo Peep|Little Boy Blue|Jack Sprat|Mother Hubbard|Mother Goose|Humpty Dumpty|Georgie Porgie|
Simple Simon|Wee Willie Winkie|Jack Horner|Mistress Mary|Tom Tom|Peter Piper|Lucy Locket|Kitty Fisher|
Jack Frost|Mother Holle|Faithful John|Iron John|Ali Baba|Aladdin|Sinbad|Scheherazade|
Snow Queen|Ugly Duckling|Steadfast Tin Soldier|Emperor|Little Match Girl|Twelve Huntsmen|Goose Girl|
Brave Tailor|Pied Piper|Beauty|Beast|Huntsman|Woodcutter|Miller|Miller's Daughter|Frog King|
Golden Goose|Hans in Luck|Lazy Jack|Jack the Giant Killer|Giant|Ogre|Troll|Tooth Fairy|Sandman""".replace("\n", "").split("|")

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

# Gendered titles only go with matching first names ("Queen Mabel", never "Queen Bruno").
MALE = set("""Aaron Adam Adrian Aiden Alan Albert Alec Alfie Amir Amos Andre Anton Archie Arlo Arthur Austin
Barney Basil Ben Benedict Bernard Boris Brian Bruno Caleb Calvin Carl Cecil Chad Clarence Claude Clive
Cody Colin Connor Craig Cyril Damian Daniel Darius Dean Derek Dominic Donald Duncan Dylan Edgar Edmund
Edwin Eli Elmer Emil Eric Ernest Ethan Evan Fabian Felix Floyd Frank Freddie Gareth Gavin George Gerald
Gilbert Glenn Gordon Graham Gus Hal Harold Harvey Heath Hector Henry Horace Howard Hugh Hugo Ian Isaac
Ivan Jack Jacob Jake James Jason Jeff Jerome Joel John Jonah Julian Karl Keith Kenneth Kevin Kirk Lance
Leo Leon Leroy Lewis Liam Lionel Lloyd Louis Luke Malcolm Marcus Mark Martin Max Miles Monty Nate Neil
Nick Noah Norman Oliver Omar Oscar Owen Patrick Paul Percy Peter Phil Quentin Ralph Ray Reggie Rhys
Roger Rolf Ross Roy Rufus Rupert Ryan Saul Scott Seth Shane Sid Silas Simon Stan Stuart Ted Theo Tim
Toby Todd Tom Trevor Vic Wade Wally Walter Wes Wilbur Will Xavier Zach""".split())
UNISEX = set("""Ariel Blake Carter Casey Charlie Dale Dana Ellis Jean Jess Jude Kelly Kim Kit Mel Quinn Robin
Sam Val Vivian""".split())
FEMALE = set(FIRST) - MALE - UNISEX
MALE_TITLES = {"Mr", "Sir", "Lord", "King"}
FEMALE_TITLES = {"Mrs", "Miss", "Lady", "Dame", "Queen"}

"""Layer library: the "who / what happened / how" pieces that turn a crowded
base niche into a book with no direct competitor.

A layer is matched against normalised titles with a regex. Each layer has a
category; a concept adds at most one layer per category, and never a category
the base keyword already covers.

Add your own layers in <data dir>/layers.json. A value is a regex, or
[regex, phrase template] where {} stands for the base keyword:
    {"buyer": {"for beekeepers": "beekeepers?|beekeeping"},
     "format": {"pocket size": ["pocket|travel size", "pocket {}"]}}
"""

import json
import os
import re

from .text import normalize

LIBRARY = {
    "buyer": {
        "for men": r"men|man|mens|male|guys?",
        "for women": r"women|woman|womens|female|ladies",
        "for moms": r"moms?|mothers?|mums?|mama|mommy",
        "for dads": r"dads?|fathers?|daddy|papa",
        "for new moms": r"new moms?|new mothers?|first time moms?|new mums?",
        "for new dads": r"new dads?|first time dads?|new fathers?",
        "for grandparents": r"grandparents?|grandmas?|grandpas?|grandmothers?|grandfathers?|nana|granny",
        "for teens": r"teens?|teenagers?|teen girls?|teen boys?|adolescents?",
        "for kids": r"kids?|children|childrens",
        "for toddlers": r"toddlers?|preschool|preschoolers?|ages? 2 4|ages? 3 5",
        "for seniors": r"seniors?|elderly|older adults?|over 60|over 70|aging",
        "for couples": r"couples?|marriage|married|husband and wife|partners",
        "for nurses": r"nurses?|nursing",
        "for teachers": r"teachers?|educators?",
        "for veterans": r"veterans?|military|soldiers?|army|navy",
        "for first responders": r"first responders?|firefighters?|paramedics?|police officers?|emt",
        "for caregivers": r"caregivers?|caregiving|carers?",
        "for students": r"students?|college|university",
        "for entrepreneurs": r"entrepreneurs?|small business|business owners?|side hustle",
        "for introverts": r"introverts?|introverted|highly sensitive",
        "for adults with adhd": r"adhd",
        "for dog owners": r"dogs?|puppy|puppies|dog owners?",
        "for cat owners": r"cats?|kitten|kittens|cat lovers?",
        "for horse lovers": r"horses?|equestrian|pony|ponies",
        "for gardeners": r"gardeners?|gardening",
        "for hunters": r"hunters?|hunting|deer",
        "for anglers": r"fishing|fishermen|anglers?",
        "for truckers": r"truckers?|truck drivers?|trucking",
        "for gamers": r"gamers?|gaming|video games?",
        "for nurses and doctors": r"doctors?|physicians?|medical students?",
        "for homeschoolers": r"homeschool|homeschooling",
        "for boys": r"boys?",
        "for girls": r"girls?",
    },
    # Situation layers read as "<base> <label>" unless a template says otherwise.
    "situation": {
        "after divorce": r"divorce|divorced|separation",
        "after a breakup": r"breakup|break up|heartbreak|broken heart",
        "for grief": r"grief|grieving|bereavement|loss of a loved one",
        "for pet loss": r"pet loss|loss of (?:a )?(?:dog|cat|pet)|rainbow bridge",
        "after miscarriage": r"miscarriage|pregnancy loss|baby loss|stillbirth|infant loss",
        "for pregnancy": r"pregnancy|pregnant|expecting|bump",
        "for a new baby": r"new baby|newborn|babys first|baby s first|first year of baby",
        "for retirement": r"retirement|retired|retiring|retiree",
        "for empty nesters": r"empty nest|empty nesters?",
        "for sobriety": r"sobriety|sober|recovery|addiction|12 steps?|alcohol free",
        "for anxiety": r"anxiety|anxious|worry|panic",
        "for chronic illness": r"chronic illness|chronic pain|fibromyalgia|lupus|spoonie|autoimmune",
        "for cancer patients": r"cancer|chemo|chemotherapy|oncology",
        "for dementia": r"dementia|alzheimers?|memory loss",
        "for moving house": r"moving|new home|relocation|house move",
        "for weddings": r"wedding|engaged|engagement|bride|bridal",
        "for newlyweds": r"newlyweds?|first year of marriage",
        "for a new job": r"new job|career change|first job|onboarding",
        "for college freshmen": r"freshman|dorm|starting college",
        "for military spouses": r"deployment|deployed|military spouse|milspouse",
        "for menopause": r"menopause|perimenopause",
        "for ivf": r"infertility|ivf|ttc|trying to conceive",
        "for adoption": r"adoption|adopted|foster",
        "for special needs parents": r"special needs|autism|autistic|disability",
        "for travel": r"travel|trip|vacation|road trip",
        "for sports": r"soccer|baseball|basketball|football|hockey|volleyball|softball",
        "for milestone birthdays": r"40th|50th|60th|70th|80th|milestone birthday",
        "for christmas": [r"christmas|advent|holiday season", "christmas {}"],
        "for halloween": [r"halloween|spooky", "halloween {}"],
        "for valentines day": [r"valentines?", "valentines {}"],
        "for mothers day": [r"mothers day", "{} mothers day gift"],
        "for fathers day": [r"fathers day", "{} fathers day gift"],
        "for graduation": [r"graduation|graduate|grad", "{} graduation gift"],
        "for new year": [r"new year|resolutions?", "new year {}"],
    },
    "format": {
        "guided": [r"guided|with prompts|prompt journal", "guided {}"],
        "workbook": [r"workbook|worksheets?|exercises", "{} workbook"],
        "with prompts": [r"prompts?", "{} with prompts"],
        "52-week": [r"52 weeks?", "52 week {}"],
        "one year": [r"365 days?|one year|1 year|a year of", "one year {}"],
        "90-day": [r"90 days?", "90 day {}"],
        "30-day": [r"30 days?", "30 day {}"],
        "5-minute": [r"5 minutes?|five minutes?|one line a day", "5 minute {}"],
        "log book": [r"log ?book|logbook|record book|tracker|tracking", "{} log book"],
        "planner": [r"planner|organizer|organiser", "{} planner"],
        "checklist": [r"checklists?", "{} checklist"],
        "activity book": [r"activity book|activities", "{} activity book"],
        "puzzle book": [r"word search|crossword|sudoku|puzzles?|word find|cryptogram", "{} word search"],
        "coloring book": [r"colou?ring", "{} coloring book"],
        "large print": [r"large print|big print|extra large print", "large print {}"],
        "fill in the blank": [r"fill in the blank|fill in|about me|all about", "fill in the blank {}"],
        "question book": [r"questions?|conversation starters?|would you rather", "{} questions"],
        "memory book": [r"memory book|keepsake|memories|legacy|tell me your story", "{} memory book"],
        "sketchbook": [r"sketchbook|sketch book|drawing pad", "{} sketchbook"],
    },
    # Angle layers read as "<label> <base>".
    "angle": {
        "funny": [r"funny|hilarious|humou?r|sarcastic|snarky|swear|sweary|gag", "funny {}"],
        "christian": [r"christian|bible|biblical|faith|prayer|devotional|scripture|jesus|god", "christian {}"],
        "catholic": [r"catholic|rosary|saints", "catholic {}"],
        "science-based": [r"science|evidence based|cbt|dbt|neuroscience|psychology", "science based {}"],
        "simple": [r"minimalist|simple|easy|no fuss", "simple {}"],
        "cozy": [r"cozy|cosy|hygge", "cozy {}"],
        "witchy": [r"gothic|goth|witch|witchy|occult|tarot", "witchy {}"],
        "aesthetic": [r"boho|aesthetic|cottagecore|vintage|retro", "aesthetic {}"],
        "mindful": [r"mindful|mindfulness|meditation|zen", "mindful {}"],
        "affirmations": [r"affirmations?|positive thinking|self love", "{} with affirmations"],
    },
}

# Product families. A layer proven in one family (e.g. "for toddlers" on activity
# books) is no evidence for another (murder mystery puzzle books).
FAMILIES = {
    "puzzle": r"word search|word find|crosswords?|sudoku|puzzles?|cryptograms?|logic|brain games?|mystery|find the killer",
    "activity": r"activity|activities|dot markers?|i spy|mazes?|tracing|cut and paste|scissor|sticker|workbook",
    "coloring": r"colou?ring",
    "journal": r"journals?|diary|diaries|notebooks?|prompts|guided|gratitude|devotional",
    "log": r"log ?books?|logbook|logs|tracker|record book|inspection|checklist|maintenance",
    "planner": r"planners?|organizers?|calendar",
    "baby": r"baby book|baby memory|baby shower|newborn|babys first|baby s first",
    "story": r"stories|story book|storybook|picture book|bedtime|read aloud",
}


def families(text):
    norm = normalize(text)
    return {name for name, pattern in FAMILIES.items() if _regex(pattern).search(norm)}


_COMPILED = {}
TEMPLATES = {}


def library(data_dir=None):
    """{category: {label: regex}} plus user layers. Phrase templates live in TEMPLATES."""
    raw = {cat: dict(items) for cat, items in LIBRARY.items()}
    if data_dir:
        path = os.path.join(data_dir, "layers.json")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                for cat, items in json.load(fh).items():
                    raw.setdefault(cat, {}).update(items)
    lib = {}
    for cat, items in raw.items():
        lib[cat] = {}
        for label, entry in items.items():
            if isinstance(entry, (list, tuple)):
                lib[cat][label] = entry[0]
                TEMPLATES[label] = entry[1]
            else:
                lib[cat][label] = entry
    return lib


def _regex(pattern):
    if pattern not in _COMPILED:
        _COMPILED[pattern] = re.compile(r"\b(?:%s)\b" % pattern)
    return _COMPILED[pattern]


def matches(pattern, text):
    return bool(_regex(pattern).search(normalize(text)))


def detect(text, lib):
    """Return {(category, label)} for every layer present in text."""
    norm = normalize(text)
    found = set()
    for cat, items in lib.items():
        for label, pattern in items.items():
            if _regex(pattern).search(norm):
                found.add((cat, label))
    return found


def strip(pattern, text):
    """text with every match of the layer removed."""
    return _regex(pattern).sub(" ", normalize(text))


def find(label, lib):
    """Look up a layer by label (case-insensitive); returns (category, label, pattern)."""
    wanted = normalize(label)
    for cat, items in lib.items():
        for lab, pattern in items.items():
            if normalize(lab) == wanted:
                return cat, lab, pattern
    return None


def search_phrase(base, label):
    """How to type the layered concept into Amazon search."""
    template = TEMPLATES.get(label, "{} " + label)
    return normalize(template.format(base))


library()      # load default phrase templates

"""Default settings. Override any key in <data dir>/config.json.

Every number here is an estimate meant to be calibrated against your own KDP
royalty reports (see README, "Calibrating"). Nothing here is official Amazon data.
"""

import copy
import json
import os

DEFAULTS = {
    "scoring_model": "v1",

    # BSR -> estimated copies sold per day for print books on amazon.com.
    # Log-log interpolation between anchors. Rough consensus of public BSR
    # calculators; replace with your own numbers once you have sales data.
    "bsr_anchors": [
        [1, 4000], [10, 1500], [100, 300], [1000, 60], [5000, 18], [10000, 10],
        [25000, 5], [50000, 2.5], [100000, 1.0], [200000, 0.5], [500000, 0.15],
        [1000000, 0.05], [3000000, 0.01],
    ],
    # Same BSR sells fewer copies in smaller stores.
    "store_multiplier": {
        "amazon.com": 1.0, "amazon.co.uk": 0.25, "amazon.de": 0.3, "amazon.ca": 0.1,
        "amazon.com.au": 0.06, "amazon.fr": 0.15, "amazon.es": 0.1, "amazon.it": 0.1,
    },
    "currency": {
        "amazon.com": "$", "amazon.co.uk": "£", "amazon.de": "€", "amazon.ca": "C$",
        "amazon.com.au": "A$", "amazon.fr": "€", "amazon.es": "€", "amazon.it": "€",
    },

    # Paperback royalty rules. Check the current KDP pricing pages; these change.
    "royalty": {
        "rate_high": 0.60,
        "rate_low": 0.50,
        # List prices below this earn rate_low instead of rate_high.
        "low_rate_below": {
            "amazon.com": 9.99, "amazon.co.uk": 7.99, "amazon.de": 9.99,
            "amazon.fr": 9.99, "amazon.es": 9.99, "amazon.it": 9.99,
            "amazon.ca": 13.99, "amazon.com.au": 14.99,
        },
        # Black-and-white paperback print cost: flat for short books, else fixed + per page.
        "print_cost_bw": {"short_max_pages": 108, "short_flat": 2.30,
                           "fixed": 1.00, "per_page": 0.012},
    },

    # A book "sells" when it is estimated to sell at least this many copies a day.
    "selling_daily": 1.0,
    # A book is "new" if published within this many days of the snapshot.
    "new_book_days": 60,
    "young_book_days": 180,
    # How many organic results of a search count as the niche's field.
    "field_size": 16,

    "score_weights": {"demand": 35, "gap": 35, "beatability": 15, "durability": 15},
    # How much a layer category changes the book. A new buyer or life situation
    # makes a different book; a format tweak on a crowded base is a thin layer,
    # so its idea score is discounted by how crowded the base is.
    "layer_weight": {"buyer": 1.0, "situation": 1.0, "angle": 0.8, "format": 0.6},
    "verdict": {"good": 70, "average": 50},

    # Words that often signal trademarks (block) or health claims (be careful).
    "trademark_words": [
        "disney", "marvel", "pokemon", "minecraft", "fortnite", "roblox", "lego",
        "barbie", "harry potter", "hogwarts", "star wars", "nfl", "nba", "taylor swift",
        "bluey", "peppa", "paw patrol", "hello kitty", "sanrio", "stanley", "cricut",
        "kindle", "amazon", "zelda", "mario", "nintendo", "playstation", "xbox",
        "squishmallow", "labubu", "stranger things",
    ],
    "health_words": [
        "cure", "heal", "diabetes", "cancer", "adhd", "autism", "anxiety", "depression",
        "ptsd", "diet", "weight loss", "keto", "blood pressure", "blood sugar",
        "menopause", "fertility", "ivf", "dementia", "alzheimer", "therapy", "cbt", "dbt",
    ],
}


def _merge(base, override):
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _merge(base[key], value)
        else:
            base[key] = value
    return base


def load(data_dir):
    cfg = copy.deepcopy(DEFAULTS)
    path = os.path.join(data_dir, "config.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            _merge(cfg, json.load(fh))
    return cfg

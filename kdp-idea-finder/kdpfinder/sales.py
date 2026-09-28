"""BSR -> sales and royalty estimates."""

import math


def daily_sales(bsr, store, cfg):
    """Estimated copies per day for a Books BSR in a store."""
    if not bsr or bsr <= 0:
        return 0.0
    anchors = cfg["bsr_anchors"]
    mult = cfg["store_multiplier"].get(store, 0.1)
    if bsr <= anchors[0][0]:
        return anchors[0][1] * mult
    for (r1, s1), (r2, s2) in zip(anchors, anchors[1:]):
        if r1 <= bsr <= r2:
            t = (math.log(bsr) - math.log(r1)) / (math.log(r2) - math.log(r1))
            return math.exp(math.log(s1) + t * (math.log(s2) - math.log(s1))) * mult
    return anchors[-1][1] * mult


def print_cost(pages, cfg):
    pc = cfg["royalty"]["print_cost_bw"]
    pages = pages or 120
    if pages <= pc["short_max_pages"]:
        return pc["short_flat"]
    return pc["fixed"] + pc["per_page"] * pages


def royalty_per_copy(price, pages, store, cfg):
    """Paperback royalty per copy (black-and-white interior)."""
    if not price:
        return 0.0
    r = cfg["royalty"]
    rate = r["rate_high"]
    if price < r["low_rate_below"].get(store, 0):
        rate = r["rate_low"]
    return max(0.0, price * rate - print_cost(pages, cfg))


def min_price_for_high_rate(store, cfg):
    return cfg["royalty"]["low_rate_below"].get(store)

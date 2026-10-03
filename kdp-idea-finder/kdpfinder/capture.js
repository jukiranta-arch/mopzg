/* KDP Capture bookmarklet.
 * Click it on an Amazon page you are looking at:
 *   - search results  -> opens the top organic results one by one (slowly) and
 *                        saves title, BSR, reviews, price, pages, publisher, date
 *   - a product page  -> saves that book
 *   - Best Sellers / Movers & Shakers / New Releases -> saves the list
 *   - any other Amazon page (e.g. the front page) -> Autopilot: finds popular
 *                        searches with autocomplete and captures them one by one
 * Copy data puts the result on the clipboard for the Capture Inbox page;
 * Save file downloads it as kdp_capture_*.json for `kdp import`.
 * Runs in your own browser at human pace; never touches your KDP account.
 * Only block comments in this file: it is turned into a javascript: URL.
 */
(function () {
  var PAGES = window.KDP_PAGES || 3;              /* search result pages to read */
  var MAX_RESULTS = window.KDP_MAX_RESULTS || 60;  /* books to open, across all pages */
  var TEST = window.__KDP_CAPTURE_TEST__ || null;
  var DELAY_MIN = TEST ? 0 : 2500, DELAY_MAX = TEST ? 10 : 5000;
  var AC_MIN = TEST ? 0 : 600, AC_MAX = TEST ? 5 : 1100;          /* autocomplete is light */
  var BETWEEN_MIN = TEST ? 0 : 15000, BETWEEN_MAX = TEST ? 5 : 30000;  /* rest between searches */
  var COOLDOWN_MIN = TEST ? 0 : (window.KDP_COOLDOWN_MIN || 60);     /* wait after a captcha */
  var REVIEW_PAGES = window.KDP_REVIEW_PAGES || 3;   /* pages of critical reviews per book (10 per page) */
  var STATE_KEY = 'kdp-autopilot-state';
  /* Suggestions that are rarely a book you could publish: not ticked by default. */
  var NOT_A_NICHE = /gift ?cards?|new books?|new releases?|kindle|audible|amazon|prime|\b20\d\d\b|\bby [a-z]+ [a-z]+$/;

  function loadState() { try { return JSON.parse(localStorage.getItem(STATE_KEY) || 'null'); } catch (e) { return null; } }
  function saveState(st) { try { localStorage.setItem(STATE_KEY, JSON.stringify(st)); } catch (e) { /* private window */ } }
  function clearState() { try { localStorage.removeItem(STATE_KEY); } catch (e) { /* private window */ } }

  /* Everything captured is kept here until you press Clear, so a download that
   * the browser blocked or dropped never loses data: Copy data works any time. */
  var DATA_KEY = 'kdp-autopilot-data';
  function emptyData() { return { captures: [], suggestions: [], startedAt: Date.now() }; }
  function loadData() {
    try {
      var d = JSON.parse(localStorage.getItem(DATA_KEY) || 'null');
      if (d) { return d; }
    } catch (e) { /* private window or blocked storage */ }
    return window.__KDP_DATA__ || emptyData();
  }
  function saveData(d) {
    window.__KDP_DATA__ = d;
    try { localStorage.setItem(DATA_KEY, JSON.stringify(d)); } catch (e) { /* full: kept in this tab only */ }
  }
  function clearData() {
    window.__KDP_DATA__ = null;
    try { localStorage.removeItem(DATA_KEY); } catch (e) { /* private window */ }
  }

  function clean(s) { return (s || '').replace(/[‎‏]/g, '').replace(/\s+/g, ' ').trim(); }
  /* Text of an element without the inline <script>/<style> Amazon mixes into some rows. */
  function text(el) {
    var copy = el.cloneNode(true);
    Array.prototype.forEach.call(copy.querySelectorAll('script, style'), function (x) { x.remove(); });
    return clean(copy.textContent);
  }
  function txt(root, sel) { var el = root.querySelector(sel); return el ? text(el) : ''; }
  function sleep(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }

  function storeOf(host) {
    var m = host.match(/amazon\.[a-z.]+$/);
    return m ? m[0] : host;
  }

  function asinFromUrl(url) {
    var m = String(url).match(/\/(?:dp|gp\/product|gp\/aw\/d)\/([A-Z0-9]{10})/);
    return m ? m[1] : null;
  }

  function saysNoResults(doc) {
    return /No results for|did not match any products/i.test(doc.body ? doc.body.textContent : '');
  }

  function isBlocked(doc) {
    var t = doc.body ? doc.body.textContent : '';
    return !!doc.querySelector('form[action*="validateCaptcha"]') ||
      /Enter the characters you see below|Type the characters you see in this image/i.test(t);
  }

  /* Some Amazon sites show their full review pages only to signed-in visitors. A page counts
   * as a sign-in wall only when it has a sign-in form (or redirected to one) and no reviews. */
  var SIGN_IN = 'form[name="signIn"], #ap_email, #ap_email_login';
  function needsSignIn(page) {
    return !parseReviews(page.doc).length && (!!page.doc.querySelector(SIGN_IN) || /\/ap\/signin/.test(page.url));
  }

  /* What a page looked like, so markup changes can be fixed from the captured data alone. */
  function reviewDiag(page, what) {
    var doc = page.doc, hooks = {}, ids = [], classes = {};
    Array.prototype.forEach.call(doc.querySelectorAll('[data-hook]'), function (e) {
      var h = e.getAttribute('data-hook');
      if (/review|cr|rating|star/i.test(h)) { hooks[h] = (hooks[h] || 0) + 1; }
    });
    Array.prototype.forEach.call(doc.querySelectorAll('[id]'), function (e) {
      if (/review|cr-|cm_cr|cm-cr/i.test(e.id) && ids.length < 30 && ids.indexOf(e.id) < 0) { ids.push(e.id); }
    });
    Array.prototype.forEach.call(doc.querySelectorAll('[class*="review"]'), function (e) {
      String(e.className).split(/\s+/).forEach(function (c) {
        if (/review/i.test(c)) { classes[c] = (classes[c] || 0) + 1; }
      });
    });
    var body = doc.body ? doc.body.textContent : '';
    return {
      what: what, status: page.status, url: page.url, title: clean(doc.title).slice(0, 120),
      sign_in_form: !!doc.querySelector(SIGN_IN), reviews_found: parseReviews(doc).length,
      stars_text: (body.match(/out of 5 stars/g) || []).length, hooks: hooks, ids: ids,
      classes: Object.keys(classes).slice(0, 30)
    };
  }

  /* ---------- reviews (product page or review list page) ---------- */
  /* Amazon has used two sets of names for the parts of a review (review-title / review-body,
   * and since 2026 reviewTitle / reviewText); both are read. */
  var R_STARS = '[data-hook="review-star-rating"], [data-hook="cmps-review-star-rating"]';
  var R_TITLE = '[data-hook="review-title"], [data-hook="reviewTitle"]';
  var R_BODY = '[data-hook="review-body"], [data-hook="reviewText"]';
  /* Screen-reader phrases Amazon wraps around review text. */
  function tidyReview(t) {
    return clean(t.replace(/(?:Brief|Full) content visible, double tap to read (?:full|brief) content\.?/g, ' ')
      .replace(/(?:\s*Read (?:more|less))+\s*$/i, ''));
  }

  function parseReviews(doc) {
    var out = [], seen = [];
    Array.prototype.forEach.call(doc.querySelectorAll('[data-hook="review"]'), function (r) {
      var box = r.closest('[data-hook="reviewContainer"]') || r;
      if (box !== r && !box.contains(r)) { box = r; }
      if (seen.indexOf(box) >= 0) { return; }
      seen.push(box);
      function find(sel) { return r.querySelector(sel) || box.querySelector(sel); }
      var starEl = find(R_STARS);
      var m = starEl ? text(starEl).match(/(\d(?:[.,]\d)?)/) : null;
      var stars = m ? parseFloat(m[1].replace(',', '.')) : null;
      if (stars === null && starEl) {
        var c = (starEl.className || '').match(/a-star-(\d)/);
        if (c) { stars = parseInt(c[1], 10); }
      }
      var titleEl = find(R_TITLE);
      var title = '';
      if (titleEl) {
        var copy = titleEl.cloneNode(true);
        Array.prototype.forEach.call(copy.querySelectorAll(R_STARS + ', .a-icon-alt, i'),
          function (x) { x.remove(); });
        title = text(copy).replace(/^\d(?:[.,]\d)? out of 5 stars\s*/i, '');
      }
      var bodyEl = find(R_BODY);
      var body = bodyEl ? tidyReview(text(bodyEl)) : '';
      if (!title && !body) { return; }
      var all = text(box);
      var helpful = txt(box, '[data-hook="helpful-vote-statement"]') ||
        ((all.match(/(?:\d[\d,]*|One) (?:people|person) found this helpful/i) || [''])[0]);
      out.push({
        id: r.id || box.id || '', stars: stars, title: title, body: body,
        date: clean((find('[data-hook="review-date"]') || {}).textContent || ''),
        verified: !!box.querySelector('[data-hook="avp-badge"], [data-hook="avp-badge-linkless"]') ||
          /Verified Purchase/i.test(all),
        helpful: helpful
      });
    });
    return out;
  }


  /* ---------- product page ---------- */
  function parseProduct(doc, asin) {
    var details = {};
    var rows = doc.querySelectorAll(
      '#detailBullets_feature_div li, #detailBulletsWrapper_feature_div li, ' +
      '#productDetails_detailBullets_sections1 tr, #productDetails_techSpec_section_1 tr, ' +
      '#productDetails_db_sections tr');
    Array.prototype.forEach.call(rows, function (row) {
      var label, value;
      var th = row.querySelector('th');
      var td = row.querySelector('td');
      if (th && td) {
        label = text(th); value = text(td);
      } else {
        var bold = row.querySelector('.a-text-bold');
        var full = text(row);
        if (bold) {
          label = text(bold).replace(/[:\s]+$/, '');
          value = clean(full.slice(full.indexOf(text(bold)) + text(bold).length));
        } else {
          var i = full.indexOf(':');
          if (i < 0) { return; }
          label = full.slice(0, i); value = full.slice(i + 1);
        }
      }
      label = clean(label).replace(/[:\s]+$/, '');
      value = clean(value).replace(/^[:\s]+/, '');
      if (label && !(label in details)) { details[label] = value; }
    });
    /* Newer "rich product information" carousel */
    Array.prototype.forEach.call(doc.querySelectorAll('[id^="rpi-attribute-"]'), function (el) {
      var label = txt(el, '.rpi-attribute-label');
      var value = txt(el, '.rpi-attribute-value');
      if (label && value && !(label in details)) { details[label] = value; }
    });

    var ranksText = '';
    var rankEl = doc.querySelector('#SalesRank, #detailBulletsWrapper_feature_div ul.zg_hrsr, #detailBullets_feature_div + ul');
    Object.keys(details).forEach(function (k) {
      if (/best ?sellers? rank|bestseller|classement|clasificaci|classifica/i.test(k)) { ranksText = details[k]; }
    });
    if (!ranksText && rankEl) { ranksText = text(rankEl); }
    if (!ranksText) {
      var all = doc.querySelectorAll('#detailBulletsWrapper_feature_div li, #prodDetails tr');
      Array.prototype.forEach.call(all, function (el) {
        var t = text(el);
        if (!ranksText && /Best Sellers Rank|Amazon Bestseller-Rang/i.test(t)) { ranksText = t; }
      });
    }

    /* The book description, with its line breaks, and its HTML (to see the bold, headings and bullets the
       seller used). The newer page wraps it in an expander; older pages use #productDescription. */
    var descEl = doc.querySelector('#bookDescription_feature_div .a-expander-content') ||
      doc.querySelector('#bookDescription_feature_div') || doc.querySelector('#productDescription');
    var description = '', descriptionHtml = '';
    if (descEl) {
      var dcopy = descEl.cloneNode(true);
      Array.prototype.forEach.call(dcopy.querySelectorAll('script, style, .a-expander-prompt, ' +
        '.a-expander-header'), function (x) { x.remove(); });
      descriptionHtml = dcopy.innerHTML.replace(/\s+/g, ' ').trim().slice(0, 12000);
      Array.prototype.forEach.call(dcopy.querySelectorAll('br'), function (x) { x.replaceWith('\n'); });
      Array.prototype.forEach.call(dcopy.querySelectorAll('p, li, ul, ol, div, h1, h2, h3, h4, h5, h6'),
        function (x) { x.before('\n'); x.append('\n'); });
      description = (dcopy.textContent || '').split('\n').map(clean)
        .filter(function (ln) { return ln; }).join('\n').slice(0, 6000);
    }
    /* "From the Publisher" (A+ Content) images under the description. */
    var hasAplus = !!doc.querySelector('#aplus_feature_div .aplus-v2, #aplus .aplus-v2, #aplus_feature_div img');

    var rating = doc.querySelector('#acrPopover');
    var author = doc.querySelector('#bylineInfo .author a, #bylineInfo a.contributorNameID, #bylineInfo a');
    var price = doc.querySelector(
      '#tmmSwatches .a-button-selected .slot-price, #tmmSwatches .selected .slot-price, ' +
      '#corePrice_feature_div .a-offscreen, #price, #newBuyBoxPrice, .a-price .a-offscreen');
    return {
      asin: asin || (doc.querySelector('#ASIN, input[name="ASIN"]') || {}).value || asinFromUrl(location.href),
      title: txt(doc, '#productTitle') || txt(doc, '#ebooksProductTitle'),
      author: author ? clean(author.textContent) : '',
      format_text: txt(doc, '#productSubtitle') || txt(doc, '#tmmSwatches .a-button-selected .slot-title') ||
        txt(doc, '#tmmSwatches .selected .slot-title'),
      price_text: price ? clean(price.textContent) : '',
      reviews_text: txt(doc, '#acrCustomerReviewText'),
      rating_text: rating ? clean(rating.getAttribute('title') || rating.textContent) : '',
      ranks_text: ranksText,
      description: description,
      description_html: descriptionHtml,
      has_aplus: hasAplus,
      details: details
    };
  }

  /* ---------- search results ---------- */
  function parseSearch(doc) {
    var items = [];
    var cards = doc.querySelectorAll('[data-component-type="s-search-result"][data-asin]');
    Array.prototype.forEach.call(cards, function (card) {
      var asin = card.getAttribute('data-asin');
      if (!asin) { return; }
      var sponsored = !!card.querySelector('.puis-sponsored-label-text, .s-sponsored-label-text, ' +
        '[aria-label="Sponsored"], a[href*="/sspa/"]') ||
        /(^|\s)Sponsored(\s|$)/.test(txt(card, '.puis-label-popover, .s-label-popover-default'));
      var h2 = card.querySelector('h2');
      if (h2 && /^Sponsored\b/i.test(clean(h2.getAttribute('aria-label') || h2.textContent))) { sponsored = true; }
      var reviews = card.querySelector('[aria-label$="ratings"], a[href*="#customerReviews"] span');
      var bought = text(card).match(/([\d.,]+[KkMm]?\+?)\s+bought in past month/);
      items.push({
        position: items.length + 1,
        asin: asin,
        sponsored: sponsored,
        title: h2 ? clean(h2.getAttribute('aria-label') || h2.textContent) : '',
        reviews: reviews ? clean(reviews.getAttribute('aria-label') || reviews.textContent) : '',
        bought_text: bought ? bought[0] : ''
      });
    });
    return items;
  }

  /* ---------- best seller style lists ---------- */
  function parseList(doc) {
    var byAsin = {}, order = [];
    Array.prototype.forEach.call(doc.querySelectorAll('a[href*="/dp/"]'), function (a) {
      var asin = asinFromUrl(a.getAttribute('href'));
      if (!asin) { return; }
      if (!byAsin[asin]) {
        byAsin[asin] = { asin: asin, title: '', reviews: '' };
        order.push(asin);
      }
      var t = clean(a.textContent);
      var img = a.querySelector('img');
      if (img && img.alt && clean(img.alt).length > t.length) { t = clean(img.alt); }
      if (/product-reviews/.test(a.getAttribute('href'))) { byAsin[asin].reviews = t; return; }
      if (t.length > byAsin[asin].title.length && !/^[\d$£€.,\s]+$/.test(t)) { byAsin[asin].title = t; }
    });
    return order.map(function (asin, i) {
      var it = byAsin[asin];
      it.position = i + 1;
      return it;
    }).filter(function (it) { return it.title; });
  }

  /* A name that is unique per list and page, e.g. "Hot New Releases in Crossword Puzzles (page 2)".
   * The page heading is often just "Amazon Hot New Releases", so the category comes from the
   * "... in <category>" text, the highlighted menu entry, or Amazon's category number. */
  function listName(doc, url, kind) {
    var u = new URL(url, location.origin);
    var node = (u.pathname.match(/\/(\d{3,})(?:\/|$)/) || [])[1] || '';
    var page = u.searchParams.get('pg') || (u.pathname.match(/_pg_(\d+)/) || [])[1] || '1';
    var label = { 'new-releases': 'Hot New Releases', movers: 'Movers & Shakers', bestsellers: 'Best Sellers',
      'wished-for': 'Most Wished For', gifted: 'Gift Ideas' }[kind] || 'List';
    var category = '';
    var heads = doc.querySelectorAll('h1, h2, [class*="zg-selected"], [class*="zg_selected"]');
    for (var i = 0; i < heads.length && !category; i++) {
      var t = clean(heads[i].textContent);
      var m = t.match(/(?:Hot New Releases|Best Sellers|Movers & Shakers|Most Wished For|Gift Ideas) in (.+)$/i);
      if (m) { category = m[1]; } else if (/selected/.test(heads[i].className || '') && t.length < 80) { category = t; }
    }
    if (!category) {
      var tm = clean(doc.title).match(/(?:Hot New Releases|Best Sellers|Movers & Shakers|Most Wished For|Gift Ideas) in (.+?)(?:\s*[-:|]|$)/i);
      if (tm) { category = tm[1]; }
    }
    category = category || ('category ' + (node || 'unknown'));
    return { name: label + ' in ' + category + (page !== '1' ? ' (page ' + page + ')' : ''),
      category: category, node: node, page: parseInt(page, 10) };
  }

  /* A best seller / new release / movers list, then each book's own page for rank, reviews and date. */
  async function captureList(doc, url, progress) {
    var kind = listKind(new URL(url, location.origin).pathname);
    var info = listName(doc, url, kind);
    var cap = {
      tool: 'kdp-capture', version: 1, store: storeOf(location.hostname), url: url,
      captured_at: new Date().toISOString(), type: 'list',
      list: { kind: kind, name: info.name, category: info.category, node: info.node, page: info.page },
      items: parseList(doc)
    };
    for (var n = 0; n < cap.items.length; n++) {
      progress('book ' + (n + 1) + ' of ' + cap.items.length + ' (slow on purpose)');
      await pause();
      try {
        var d = await getDoc('/dp/' + cap.items[n].asin);
        if (isBlocked(d)) { cap.partial = cap.blocked = true; break; }
        cap.items[n].product = parseProduct(d, cap.items[n].asin);
      } catch (e) {
        cap.items[n].error = String(e);
      }
    }
    cap.books_read = cap.items.filter(function (i) { return i.product; }).length;
    return cap;
  }

  function listKind(path) {
    if (/movers-and-shakers/.test(path)) { return 'movers'; }
    if (/new-releases/.test(path)) { return 'new-releases'; }
    if (/most-wished-for|wishlist/.test(path)) { return 'wished-for'; }
    if (/most-gifted/.test(path)) { return 'gifted'; }
    return 'bestsellers';
  }

  /* ---------- UI ---------- */
  var box = document.getElementById('kdp-capture-box');
  if (!box) {
    box = document.createElement('div');
    box.id = 'kdp-capture-box';
    box.style.cssText = 'position:fixed;z-index:2147483647;top:12px;right:12px;max-width:380px;' +
      'max-height:85vh;overflow:auto;' +
      'background:#111;color:#fff;font:13px/1.4 system-ui,sans-serif;padding:10px 12px;' +
      'border-radius:8px;box-shadow:0 4px 18px rgba(0,0,0,.35)';
    document.body.appendChild(box);
  }
  function say(msg) { box.textContent = 'KDP Capture: ' + msg; }

  function downloadNamed(obj, name) {
    if (TEST) { (window.__KDP_DOWNLOADS__ = window.__KDP_DOWNLOADS__ || []).push({ name: name, data: obj }); return; }
    var url = URL.createObjectURL(new Blob([JSON.stringify(obj, null, 1)], { type: 'application/json' }));
    /* Some Amazon pages cancel every link click they see (their own page routing),
     * which silently kills a download. So the link sits in a closed shadow root
     * and its click event neither bubbles nor leaves the shadow root. */
    var host = document.createElement('span');
    host.style.display = 'none';
    document.documentElement.appendChild(host);
    var root = host.attachShadow({ mode: 'closed' });
    var a = document.createElement('a');
    a.href = url;
    a.download = name;
    root.appendChild(a);
    a.dispatchEvent(new MouseEvent('click', { bubbles: false, cancelable: true, composed: false }));
    setTimeout(function () { URL.revokeObjectURL(url); host.remove(); }, 60000);
  }

  /* Fallback when downloads don't work at all: put the file's text on the clipboard. */
  function copyText(obj, done) {
    var text = JSON.stringify(obj);
    function fallback() {
      var ta = document.createElement('textarea');
      ta.value = text;
      ta.style.cssText = 'position:fixed;top:0;left:0;width:1px;height:1px;opacity:0';
      document.body.appendChild(ta);
      ta.select();
      var ok = false;
      try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
      ta.remove();
      done(ok);
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () { done(true); }, fallback);
    } else {
      fallback();
    }
  }

  /* Your Capture Inbox page: paste copied data there and Claude reads it directly. */
  var INBOX_URL = window.KDP_INBOX_URL || 'https://claude.ai/artifact/R1ACbV9sgirgWCx32XhL3V';
  var COPY_HELP = 'Copied. Open your Capture Inbox and press Ctrl+V there.';

  function openInbox() { window.open(INBOX_URL, '_blank', 'noopener'); }

  function slugOf(s) { return String(s || 'page').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 50); }

  function fileName(kind, slug, iso, store) {
    /* Date and time (UTC) in the name, so files from different runs never share a name. */
    return 'kdp_capture_' + kind + '_' + slug + '_' + iso.slice(0, 10) + '_' + iso.slice(11, 16).replace(':', '') + '_' +
      store.replace(/\./g, '-') + '.json';
  }

  function download(capture) {
    var slug = slugOf(capture.keyword || (capture.list && capture.list.name) || capture.product && capture.product.asin);
    downloadNamed(capture, fileName(capture.type, slug, capture.captured_at, capture.store));
  }

  function button(label, onClick, parent) {
    var b = document.createElement('button');
    b.textContent = label;
    b.style.cssText = 'margin:8px 8px 0 0;padding:4px 10px;border:0;border-radius:4px;' +
      'background:#ff9900;color:#111;font:600 12px system-ui,sans-serif;cursor:pointer';
    b.onclick = onClick;
    (parent || box).appendChild(b);
    return b;
  }

  /* Nothing downloads by itself: some browsers (Firefox) block downloads that
   * a page starts on its own. Copy data + the Capture Inbox is the main route. */
  function save(capture, message) {
    if (TEST && !window.__KDP_AUTOPILOT__) { window.__KDP_RESULT__ = capture; return; }
    say(message + ' Press Copy data, then paste it into your Capture Inbox.');
    box.appendChild(document.createElement('br'));
    button('Copy data', function () {
      copyText(capture, function (ok) { say(ok ? COPY_HELP : 'Copying failed. Tell Claude what happened.'); });
    });
    button('Open inbox', openInbox);
    button('Save file', function () { download(capture); });
    button('Close', function () { box.remove(); });
  }

  function pause() { return sleep(DELAY_MIN + Math.random() * (DELAY_MAX - DELAY_MIN)); }

  async function getDoc(url) {
    return (await getPage(url)).doc;
  }

  async function getPage(url) {
    var resp = await fetch(url, { credentials: 'include' });
    return { doc: new DOMParser().parseFromString(await resp.text(), 'text/html'), status: resp.status, url: resp.url };
  }

  function searchUrl(term) {
    var u = new URL('/s', location.origin);
    u.searchParams.set('k', term);
    u.searchParams.set('i', 'stripbooks');
    return u.toString();
  }

  /* Reads PAGES result pages of a search, then opens up to maxBooks organic books.
   * firstDoc is the page already on screen (or null to fetch it). */
  async function captureSearch(term, firstDoc, pageUrl, maxBooks, progress) {
    var capture = {
      tool: 'kdp-capture', version: 1, store: storeOf(location.hostname), url: pageUrl,
      captured_at: new Date().toISOString(), type: 'search', keyword: term, items: []
    };
    var seen = {}, pagesRead = 0;
    var start = parseInt(new URL(pageUrl, location.origin).searchParams.get('page') || '1', 10);
    for (var pg = start; pg < start + PAGES; pg++) {
      var doc = null;
      if (pg === start && firstDoc) {
        doc = firstDoc;
      } else {
        progress('results page ' + (pg - start + 1) + ' of ' + PAGES);
        await pause();
        var u = new URL(pageUrl, location.origin);
        u.searchParams.set('page', String(pg));
        try {
          doc = await getDoc(u.toString());
        } catch (e) {
          if (!pagesRead) { capture.partial = capture.blocked = true; capture.empty_reason = 'fetch failed: ' + e; }
          break;
        }
      }
      if (isBlocked(doc)) { capture.partial = capture.blocked = true; break; }
      var more = parseSearch(doc).filter(function (i) { return !seen[i.asin]; });
      if (!more.length) {
        /* An empty first page that doesn't say "No results" is Amazon quietly throttling: stop as for
           a captcha instead of saving dozens of empty searches. */
        if (!pagesRead && !saysNoResults(doc)) {
          capture.partial = capture.blocked = true;
          capture.empty_reason = clean(doc.title || '').slice(0, 120) || 'empty results page';
        }
        break;
      }
      more.forEach(function (i) { seen[i.asin] = true; i.page = pg; capture.items.push(i); });
      pagesRead++;
    }
    capture.items.forEach(function (i, idx) { i.position = idx + 1; });
    capture.pages = pagesRead;
    var organic = capture.blocked ? [] : capture.items.filter(function (i) { return !i.sponsored; }).slice(0, maxBooks);
    for (var n = 0; n < organic.length; n++) {
      progress('book ' + (n + 1) + ' of ' + organic.length + ' (slow on purpose)');
      try {
        var d = await getDoc('/dp/' + organic[n].asin);
        if (isBlocked(d)) { capture.partial = capture.blocked = true; break; }
        organic[n].product = parseProduct(d, organic[n].asin);
      } catch (e) {
        organic[n].error = String(e);
      }
      await pause();
    }
    capture.books_read = organic.filter(function (i) { return i.product; }).length;
    return capture;
  }

  /* Some Amazon pages add their reviews with scripts after the page loads, so a fetched copy
   * has none. This opens the book page in a small, nearly invisible frame in this tab (same
   * site, as if you opened it), scrolls it to the reviews and reads what appears. */
  function loadInFrame(url, timeoutMs) {
    return new Promise(function (resolve) {
      var f = document.createElement('iframe');
      f.style.cssText = 'position:fixed;right:0;bottom:0;width:480px;height:360px;opacity:0.01;' +
        'pointer-events:none;border:0;z-index:1';
      var done = false;
      function finish(doc) { if (!done) { done = true; resolve({ frame: f, doc: doc }); } }
      f.onload = function () { try { finish(f.contentDocument); } catch (e) { finish(null); } };
      setTimeout(function () { finish(null); }, timeoutMs);
      f.src = url;
      document.body.appendChild(f);
    });
  }

  async function renderedBookPage(asin) {
    var r = await loadInFrame('/dp/' + asin, TEST ? 5000 : 30000);
    var out = { reviews: [], page: null, blocked: false };
    try {
      if (!r.doc) { return out; }
      if (isBlocked(r.doc)) { out.blocked = true; return out; }
      var win = r.frame.contentWindow;
      var anchor = r.doc.querySelector('#reviewsMedley, #customerReviews, #cm-cr-dp-review-list, ' +
        '[data-hook="top-customer-reviews-widget"]');
      if (anchor) { anchor.scrollIntoView(); }
      for (var step = 0; step < 40; step++) {
        out.reviews = parseReviews(r.doc);
        if (out.reviews.length) { break; }
        win.scrollBy(0, 700);
        await sleep(TEST ? 25 : 400);
      }
      out.page = { doc: r.doc, status: 200, url: win.location.href };
      out.diag = reviewDiag(out.page, 'book page in frame');
      out.extras = pageExtras(r.doc);
    } catch (e) {
      out.error = String(e);
    } finally {
      r.frame.remove();
    }
    return out;
  }

  /* The star breakdown ("5 star 80%") and Amazon's "Customers say" summary, when present.
   * Rows are read one at a time (aria-label first, then the row's text), never a whole table. */
  function pageExtras(doc) {
    var out = {};
    var hist = {};
    Array.prototype.forEach.call(doc.querySelectorAll('[aria-label]'), function (el) {
      var m = (el.getAttribute('aria-label') || '').match(/(\d{1,3})\s*percent of reviews have ([1-5]) stars?/i);
      if (m) { hist[m[2]] = parseInt(m[1], 10); }
    });
    if (!Object.keys(hist).length) {
      Array.prototype.forEach.call(doc.querySelectorAll('[id*="histogram"] li, [id*="histogram"] tr, ' +
        '[class*="histogram"] li, [class*="histogram"] tr'), function (row) {
        var m = text(row).match(/^\s*([1-5])\s*stars?\D{0,20}?(\d{1,3})\s*%/i);
        if (m && !(m[1] in hist)) { hist[m[1]] = parseInt(m[2], 10); }
      });
    }
    if (Object.keys(hist).length) { out.histogram = hist; }
    var histEl = doc.querySelector('[id*="histogram"], [class*="histogram"]');
    if (histEl) { out.histogram_text = text(histEl).slice(0, 300); }    /* to check the parsing */
    var heads = doc.querySelectorAll('h2, h3, h4, span');
    for (var i = 0; i < heads.length; i++) {
      if (clean(heads[i].textContent) === 'Customers say') {
        var box = heads[i].parentElement && heads[i].parentElement.parentElement;
        if (box) { out.customers_say = text(box).replace(/^\s*Customers say\s*/, '').slice(0, 2000); }
        break;
      }
    }
    return out;
  }

  var listsWalled = false;    /* set once this run finds the review lists behind a sign-in */

  /* Reviews of one book: those on its product page, then up to REVIEW_PAGES pages of
   * critical reviews and one page of top positive ones. If a filtered page is walled off,
   * the plain list the book page links to ("See more reviews") is tried instead.
   * startPage is the review page on screen when the bookmarklet is clicked on one. */
  async function captureReviews(asin, progress, startPage) {
    var cap = {
      tool: 'kdp-capture', version: 1, store: storeOf(location.hostname), url: location.origin + '/dp/' + asin,
      captured_at: new Date().toISOString(), type: 'reviews', keyword: 'reviews:' + asin, asin: asin, reviews: [],
      diagnostics: []
    };
    var seen = {};
    function add(list, source) {
      list.forEach(function (r) {
        var k = r.id || (r.title + '|' + r.body.slice(0, 80));
        if (seen[k]) { return; }
        seen[k] = true;
        r.source = source;
        cap.reviews.push(r);
      });
    }
    /* Reads a review list and follows its Next links. Returns 'ok', 'walled' or 'empty'. */
    async function readList(first, source, maxPages) {
      var page = first, next = null;
      for (var pg = 1; pg <= maxPages; pg++) {
        if (!page) {
          await pause();
          progress(source + ' reviews, page ' + pg);
          try { page = await getPage(next); } catch (e) { return pg > 1 ? 'ok' : 'empty'; }
        }
        if (isBlocked(page.doc)) { cap.partial = cap.blocked = true; return 'blocked'; }
        cap.diagnostics.push(reviewDiag(page, source + ' ' + pg));
        if (needsSignIn(page)) { return pg > 1 ? 'ok' : 'walled'; }
        var got = parseReviews(page.doc);
        add(got, source);
        var link = page.doc.querySelector('li.a-last:not(.a-disabled) a');
        if (!got.length) { return pg > 1 ? 'ok' : 'empty'; }
        if (!link) { return 'ok'; }
        next = new URL(link.getAttribute('href'), page.url || location.href).toString();
        page = null;
      }
      return 'ok';
    }
    progress('book page');
    var bookPage = await getPage('/dp/' + asin);
    if (isBlocked(bookPage.doc)) { cap.partial = cap.blocked = true; return cap; }
    cap.product = parseProduct(bookPage.doc, asin);
    if (!cap.product.title && !startPage) {     /* not sold on this Amazon site: skip its review pages */
      cap.not_found = true;
      cap.books_read = 0;
      return cap;
    }
    cap.diagnostics.push(reviewDiag(bookPage, 'book page'));
    add(parseReviews(bookPage.doc), 'product page');
    Object.assign(cap, pageExtras(bookPage.doc));
    if (!cap.reviews.length && !startPage) {
      await pause();
      progress('book page, letting its reviews load');
      var shown = await renderedBookPage(asin);
      if (shown.blocked) { cap.partial = cap.blocked = true; return cap; }
      if (shown.diag) { cap.diagnostics.push(shown.diag); }
      if (shown.error) { cap.diagnostics.push({ what: 'book page in frame', error: shown.error }); }
      add(shown.reviews, 'product page');
      Object.assign(cap, shown.extras || {});
    }
    var results = [];
    if (listsWalled && !startPage) {    /* already known this run: the review lists need a sign-in */
      cap.signed_out = true;
      cap.books_read = 1;
      return cap;
    }
    if (startPage) {
      results.push(await readList(startPage, 'this page', REVIEW_PAGES + 2));
    }
    var base = '/product-reviews/' + asin + '/?reviewerType=all_reviews&sortBy=helpful';
    var critical = await readFrom(base + '&filterByStar=critical&pageNumber=1', 'critical', REVIEW_PAGES);
    results.push(critical);
    if (critical === 'blocked') { return cap; }
    if (critical !== 'ok') {
      var seeAll = bookPage.doc.querySelector('a[data-hook="see-all-reviews-link-foot"], a[data-hook="see-all-reviews-link"]');
      var plain = seeAll ? new URL(seeAll.getAttribute('href'), bookPage.url || location.href).toString()
        : '/product-reviews/' + asin + '/';
      results.push(await readFrom(plain, 'all', REVIEW_PAGES));
    } else {
      results.push(await readFrom(base + '&filterByStar=positive&pageNumber=1', 'positive', 1));
    }
    if (results.indexOf('ok') < 0 && results.indexOf('walled') >= 0) {
      cap.signed_out = true;
      listsWalled = results.every(function (r) { return r === 'walled'; });
    }
    cap.books_read = 1;
    return cap;

    async function readFrom(url, source, maxPages) {
      await pause();
      progress(source + ' reviews, page 1');
      var first;
      try { first = await getPage(url); } catch (e) { return 'empty'; }
      return readList(first, source, maxPages);
    }
  }

  function asinsIn(textValue) {
    var out = [];
    (textValue.match(/\b(?:B0[A-Z0-9]{8}|\d{9}[\dX])\b/g) || []).forEach(function (a) {
      if (out.indexOf(a) < 0) { out.push(a); }
    });
    return out;
  }

  /* ---------- autopilot: autocomplete discovery + capture queue ---------- */
  var MARKETS = {
    'amazon.com': ['completion.amazon.com', 'ATVPDKIKX0DER'],
    'amazon.co.uk': ['completion.amazon.co.uk', 'A1F83G8C2ARO7P'],
    'amazon.ca': ['completion.amazon.com', 'A2EUQ1WTGCTBG2'],
    'amazon.com.au': ['completion.amazon.com.au', 'A39IBJ37TRP1C6'],
    'amazon.de': ['completion.amazon.co.uk', 'A1PA6795UKMFR9']
  };
  var DEFAULT_ROOTS = ['gift for', 'journal for', 'notebook for', 'activity book for kids', 'coloring book for',
    'puzzle book for', 'word search for', 'workbook for', 'log book for', 'planner for', 'guided journal',
    'book for new', 'prompts for', 'sketchbook for'];

  async function suggest(prefix) {
    var m = MARKETS[storeOf(location.hostname)] || MARKETS['amazon.com'];
    var url = (window.KDP_AC_URL || 'https://' + m[0] + '/api/2017/suggestions') +
      '?limit=11&suggestion-type=KEYWORD&page-type=Gateway&alias=stripbooks&site-variant=desktop&version=3' +
      '&mid=' + m[1] + '&prefix=' + encodeURIComponent(prefix);
    var resp = await fetch(url);
    var data = await resp.json();
    return (data.suggestions || []).map(function (s) { return clean(s.value).toLowerCase(); }).filter(Boolean);
  }

  /* Ask autocomplete for each root and root + a..z. Suggestions listed higher are
   * searched more, so each appearance scores 1 / (1 + position). */
  async function discover(roots, progress, isStopped) {
    var rows = [], scores = {}, ok = 0, failed = 0;
    for (var r = 0; r < roots.length; r++) {
      var prefixes = [roots[r]].concat('abcdefghijklmnopqrstuvwxyz'.split('').map(function (l) { return roots[r] + ' ' + l; }));
      for (var p = 0; p < prefixes.length; p++) {
        if (isStopped()) { return { rows: rows, scores: scores }; }
        progress('asking autocomplete: "' + prefixes[p] + '" (' + (r + 1) + ' of ' + roots.length + ')');
        try {
          (await suggest(prefixes[p])).forEach(function (s, pos) {
            if (s === roots[r]) { return; }
            rows.push({ seed: roots[r], suggestion: s, position: pos + 1 });
            scores[s] = (scores[s] || 0) + 1 / (1 + pos);
          });
          ok++;
        } catch (e) {
          failed++;
          if (!ok && failed >= 3) { throw new Error('Amazon autocomplete did not answer (' + e + ')'); }
        }
        await sleep(AC_MIN + Math.random() * (AC_MAX - AC_MIN));
      }
    }
    return { rows: rows, scores: scores };
  }

  function el(tag, css, textContent) {
    var e = document.createElement(tag);
    if (css) { e.style.cssText = css; }
    if (textContent) { e.textContent = textContent; }
    return e;
  }

  function autopilot() {
    var stopped = false;
    var store = storeOf(location.hostname);
    var remembered = null;
    try { remembered = localStorage.getItem('kdp-roots'); } catch (e) { /* private window */ }
    box.textContent = '';
    box.appendChild(el('div', 'font-weight:700;font-size:15px;margin-bottom:6px', 'KDP Autopilot'));
    box.appendChild(el('div', 'opacity:.8;margin-bottom:8px',
      'Finds what people search for with Amazon autocomplete, then captures the top searches one by one. ' +
      'Leave this tab open. Everything is kept in the tab until you copy it to your Capture Inbox.'));
    box.appendChild(el('label', 'display:block;margin-top:4px', 'Starting phrases (one per line):'));
    var roots = el('textarea', 'width:100%;box-sizing:border-box;height:110px;font:12px monospace;color:#111');
    roots.id = 'kdp-roots';
    roots.value = remembered || DEFAULT_ROOTS.join('\n');
    box.appendChild(roots);
    var nums = el('div', 'display:flex;gap:10px;margin-top:6px;flex-wrap:wrap');
    function numInput(label, id, value) {
      var wrap = el('label', '', label + ' ');
      var input = el('input', 'width:52px;color:#111');
      input.type = 'number'; input.min = '1'; input.id = id; input.value = String(value);
      wrap.appendChild(input);
      nums.appendChild(wrap);
      return input;
    }
    var howMany = numInput('Searches to capture', 'kdp-howmany', 15);
    var perSearch = numInput('Books per search', 'kdp-books', 16);
    box.appendChild(nums);
    var status = el('div', 'margin-top:8px;min-height:1.4em;color:#ffd27a');
    status.id = 'kdp-status';
    var controls = el('div', '');
    box.appendChild(controls);
    box.appendChild(status);
    var list = el('div', 'margin-top:6px');
    list.id = 'kdp-list';
    box.appendChild(list);
    var found = null;

    function progress(msg) { status.textContent = msg; }

    button('1. Find what people search', async function () {
      stopped = false;
      var r = roots.value.split('\n').map(function (x) { return clean(x).toLowerCase(); }).filter(Boolean);
      try { localStorage.setItem('kdp-roots', roots.value); } catch (e) { /* private window */ }
      try {
        found = await discover(r, progress, function () { return stopped; });
      } catch (e) {
        progress(String(e.message || e) + '. Type your own searches in the box below instead, one per line.');
        found = { rows: [], scores: {} };
      }
      var ranked = Object.keys(found.scores).sort(function (a, b) { return found.scores[b] - found.scores[a]; });
      list.textContent = '';
      ranked.slice(0, 150).forEach(function (term, i) {
        var row = el('label', 'display:flex;gap:6px;align-items:center');
        var cb = el('input', '');
        cb.type = 'checkbox'; cb.value = term;
        row.appendChild(cb);
        row.appendChild(el('span', '', term));
        list.appendChild(row);
      });
      var want = parseInt(howMany.value, 10);
      Array.prototype.forEach.call(list.querySelectorAll('input[type=checkbox]'), function (c) {
        if (want > 0 && !NOT_A_NICHE.test(c.value)) { c.checked = true; want--; }
      });
      if (found.rows.length) {
        var data = loadData();
        data.suggestions = found.rows;
        saveData(data);
        updateSaveBox();
      }
      progress(ranked.length + ' searches found, most searched first. ' +
        'The top ones are ticked. Change the ticks if you like, then press 2.');
    }, controls);

    function ticked() {
      return Array.prototype.filter.call(list.querySelectorAll('input[type=checkbox]'), function (c) { return c.checked; })
        .map(function (c) { return c.value; });
    }

    /* Captures terms one by one. Each finished search is kept in the tab at once;
     * the queue is saved before each search, so after a captcha, a Stop or a
     * closed tab the next click on KDP Capture can continue. */
    async function runQueue(terms, books) {
      stopped = false;
      clearInterval(timer);
      resumeBox.hidden = true;
      function remember(from, extra) {
        saveState(Object.assign({ remaining: terms.slice(from), books: books, savedAt: Date.now() }, extra || {}));
      }
      function keep(cap) {
        var data = loadData();
        data.captures = data.captures.filter(function (c) { return c.keyword !== cap.keyword; });
        data.captures.push(cap);
        saveData(data);
        updateSaveBox();
      }
      var i = 0, signedOutWarned = false;
      for (; i < terms.length && !stopped; i++) {
        remember(i);
        var say_ = function (m) {
          progress((/^reviews:/.test(terms[i]) ? 'Book ' : 'Search ') + (i + 1) + ' of ' + terms.length +
            ' "' + terms[i] + '": ' + m);
        };
        var cap = /^reviews:/.test(terms[i])
          ? await captureReviews(terms[i].slice(8), say_)
          : await captureSearch(terms[i], null, searchUrl(terms[i]), books, say_);
        if (cap.signed_out && !cap.reviews.length && !signedOutWarned) {
          signedOutWarned = true;
          alert('No reviews found on the page of ' + terms[i].slice(8) + ', and Amazon asks for a sign-in to see ' +
            'its review lists. It carries on with the other books.');
        }
        if (cap.blocked) {
          remember(i, { blockedAt: Date.now() });      /* redo the interrupted search */
          progress('Amazon asked for a captcha after ' + i + ' searches. Those are kept: press Copy data ' +
            'and paste into your Capture Inbox. To go on, use Show the captcha above.');
          showResume(loadState());
          window.__KDP_DONE__ = true;
          return;
        }
        keep(cap);
        if (i < terms.length - 1 && !stopped) {
          progress('Resting between searches (slow on purpose)...');
          await sleep(BETWEEN_MIN + Math.random() * (BETWEEN_MAX - BETWEEN_MIN));
        }
      }
      if (i < terms.length) {
        remember(i);
        progress('Stopped. What was captured is kept: press Copy data and paste into your Capture Inbox. ' +
          'Click KDP Capture again later to continue.');
      } else {
        clearState();
        progress('Done. Press Copy data, then paste into your Capture Inbox (Open inbox).');
      }
      window.__KDP_DONE__ = true;
    }

    function bundle() {
      var data = loadData();
      var now = new Date().toISOString();
      return { tool: 'kdp-capture', version: 1, type: 'batch', store: store, captured_at: now,
        captures: data.captures, suggestions: data.suggestions };
    }

    function downloadAll() {
      var b = bundle();
      if (!b.captures.length && !b.suggestions.length) { return; }
      try {
        downloadNamed(b, fileName('batch', 'autopilot', b.captured_at, store));
      } catch (e) {
        progress('Saving the file failed (' + e + '). Use Copy data instead.');
      }
    }

    var saveBox = el('div', 'margin:8px 0;padding:8px;border:1px solid #6fcf97;border-radius:6px');
    saveBox.id = 'kdp-saved';
    box.insertBefore(saveBox, box.children[2]);
    function updateSaveBox() {
      var data = loadData();
      saveBox.textContent = '';
      saveBox.hidden = !data.captures.length && !data.suggestions.length;
      if (saveBox.hidden) { return; }
      var nReviews = data.captures.filter(function (c) { return c.type === 'reviews'; }).length;
      var nSearches = data.captures.length - nReviews;
      saveBox.appendChild(el('div', '', 'Kept in this tab: ' + nSearches + ' searches' +
        (nReviews ? ', reviews of ' + nReviews + ' books' : '') +
        (data.suggestions.length ? ' and the autocomplete list' : '') + '. Copy data, then paste into your Capture Inbox.'));
      button('Copy data', function () {
        copyText(bundle(), function (ok) { progress(ok ? COPY_HELP : 'Copying failed. Tell Claude what happened.'); });
      }, saveBox).id = 'kdp-copy';
      button('Open inbox', openInbox, saveBox);
      button('Save file', downloadAll, saveBox).id = 'kdp-save';
      button('Clear (after pasting)', function () { clearData(); updateSaveBox(); }, saveBox);
    }
    var old = loadData();
    if (old.startedAt && Date.now() - old.startedAt > 3 * 86400000) { clearData(); }   /* stale after 3 days */
    updateSaveBox();

    var resumeBox = el('div', 'margin:8px 0;padding:8px;border:1px solid #ff9900;border-radius:6px');
    resumeBox.id = 'kdp-resume';
    resumeBox.hidden = true;
    box.insertBefore(resumeBox, box.children[2]);
    var timer = null;

    function showResume(st) {
      if (!st || !st.remaining || !st.remaining.length) { resumeBox.hidden = true; return; }
      resumeBox.hidden = false;
      resumeBox.textContent = '';
      resumeBox.appendChild(el('div', 'font-weight:700', st.remaining.length + ' left from your last run'));
      var info = el('div', 'margin-top:4px');
      resumeBox.appendChild(info);
      var go = button('Continue where it left off', function () {
        clearInterval(timer);
        runQueue(st.remaining, st.books || 16);
      }, resumeBox);
      go.id = 'kdp-continue';
      /* The captcha only shows on a normal Amazon page, not inside the panel. */
      var show = button('Show the captcha', function () { window.open(searchUrl('books'), '_blank'); }, resumeBox);
      var early = button('I solved the captcha, continue now', function () {
        clearInterval(timer);
        runQueue(st.remaining, st.books || 16);
      }, resumeBox);
      button('Forget them', function () { clearInterval(timer); clearState(); resumeBox.hidden = true; }, resumeBox);
      var readyAt = (st.blockedAt || 0) + COOLDOWN_MIN * 60000;
      function tick() {
        var left = readyAt - Date.now();
        if (left <= 0) {
          clearInterval(timer);
          go.disabled = false;
          go.style.opacity = '1';
          early.hidden = true;
          show.hidden = true;
          info.textContent = st.blockedAt ? 'The wait is over. Amazon should let you continue now.' : 'Stopped or closed before it finished.';
          return;
        }
        var m = Math.floor(left / 60000), sec = Math.floor(left / 1000) % 60;
        go.disabled = true;
        go.style.opacity = '.5';
        info.textContent = 'Amazon asked for a captcha. You can continue in ' + m + ':' + (sec < 10 ? '0' : '') + sec +
          ', or press Show the captcha, solve it in the tab that opens, then press I solved the captcha.';
      }
      clearInterval(timer);
      tick();
      timer = setInterval(tick, 1000);
    }
    showResume(loadState());

    button('2. Capture ticked searches', function () {
      var terms = ticked();
      if (!terms.length) { progress('Tick at least one search first (or press 1).'); return; }
      runQueue(terms, parseInt(perSearch.value, 10) || 16);
    }, controls);

    button('Capture the phrases in the box directly', function () {
      var terms = roots.value.split('\n').map(function (x) { return clean(x).toLowerCase(); }).filter(Boolean);
      runQueue(terms, parseInt(perSearch.value, 10) || 16);
    }, controls);

    button('Stop', function () { stopped = true; progress('Stopping after the current search...'); }, controls);

    box.appendChild(el('div', 'font-weight:700;margin-top:12px', 'Book reviews'));
    box.appendChild(el('div', 'opacity:.8', 'Paste Amazon links or ASINs of books to learn from (one per line). ' +
      'Reads the reviews on each book page, plus critical reviews when you are signed in.'));
    var reviewBox = el('textarea', 'width:100%;box-sizing:border-box;height:70px;font:12px monospace;color:#111');
    reviewBox.id = 'kdp-review-asins';
    box.appendChild(reviewBox);
    var reviewControls = el('div', '');
    box.appendChild(reviewControls);
    button('Capture reviews of these books', function () {
      var asins = asinsIn(reviewBox.value);
      if (!asins.length) { progress('Paste at least one Amazon link or ASIN first.'); return; }
      runQueue(asins.map(function (a) { return 'reviews:' + a; }), 0);
    }, reviewControls).id = 'kdp-review-go';
    button('Close', function () { stopped = true; box.remove(); }, controls);
  }

  async function run() {
    var path = location.pathname;
    var params = new URLSearchParams(location.search);

    if ((params.get('k') && /^\/s\/?$/.test(path)) || document.querySelector('[data-component-type="s-search-result"]')) {
      var capture = await captureSearch(params.get('k') || '', document, location.href, MAX_RESULTS, function (m) {
        say('reading ' + m + '...');
      });
      save(capture, capture.partial
        ? 'Amazon asked for a captcha, so it stopped. Saved the ' + capture.books_read + ' books read so far; try again later.'
        : 'Done: "' + capture.keyword + '" (' + capture.books_read + ' books from ' + capture.pages + ' pages).');
      return;
    }

    var base = {
      tool: 'kdp-capture', version: 1, store: storeOf(location.hostname),
      url: location.href, captured_at: new Date().toISOString()
    };

    var reviewPage = path.match(/\/product-reviews\/([A-Z0-9]{10})/);
    if (reviewPage) {
      var rc = await captureReviews(reviewPage[1], function (m) { say('reading ' + m + '...'); },
        { doc: document, status: 200, url: location.href });
      save(rc, 'Saved ' + rc.reviews.length + ' reviews of ' + reviewPage[1] + '.');
      return;
    }

    if (asinFromUrl(location.href) || document.querySelector('#productTitle')) {
      var product = parseProduct(document, asinFromUrl(location.href));
      var here = { doc: document, status: 200, url: location.href };
      product.reviews = parseReviews(document);          /* as rendered on screen */
      product.review_diagnostics = reviewDiag(here, 'book page on screen');
      save(Object.assign({}, base, { type: 'product', product: product }),
        'Saved ' + (product.title || product.asin).slice(0, 60) + '.');
      return;
    }

    if (/bestsellers|movers-and-shakers|new-releases|most-wished-for|most-gifted|zgbs/.test(path)) {
      var lc = await captureList(document, location.href, function (m) { say('reading ' + m + '...'); });
      save(lc, lc.partial
        ? 'Amazon asked for a captcha, so it stopped. Saved "' + lc.list.name.slice(0, 60) + '" with ' +
          lc.books_read + ' books read; try again later.'
        : 'Saved "' + lc.list.name.slice(0, 70) + '" (' + lc.items.length + ' books, ' + lc.books_read + ' book pages).');
      return;
    }

    autopilot();
  }

  run().catch(function (e) { say('error: ' + e); });
})();

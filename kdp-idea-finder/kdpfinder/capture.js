/* KDP Capture bookmarklet.
 * Click it on an Amazon page you are looking at:
 *   - search results  -> opens the top organic results one by one (slowly) and
 *                        saves title, BSR, reviews, price, pages, publisher, date
 *   - a product page  -> saves that book
 *   - Best Sellers / Movers & Shakers / New Releases -> saves the list
 *   - any other Amazon page (e.g. the front page) -> Autopilot: finds popular
 *                        searches with autocomplete and captures them one by one
 * The result downloads as kdp_capture_*.json. Import it with `kdp import`.
 * Runs in your own browser at human pace; never touches your KDP account.
 * Only block comments in this file: it is turned into a javascript: URL.
 */
(function () {
  var PAGES = window.KDP_PAGES || 3;              /* search result pages to read */
  var MAX_RESULTS = window.KDP_MAX_RESULTS || 60;  /* books to open, across all pages */
  var TEST = window.__KDP_CAPTURE_TEST__ || null;
  var DELAY_MIN = TEST ? 0 : 2500, DELAY_MAX = TEST ? 10 : 5000;
  var AC_MIN = TEST ? 0 : 600, AC_MAX = TEST ? 5 : 1100;          /* autocomplete is light */

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

  function isBlocked(doc) {
    var t = doc.body ? doc.body.textContent : '';
    return !!doc.querySelector('form[action*="validateCaptcha"]') ||
      /Enter the characters you see below|Type the characters you see in this image/i.test(t);
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
    var a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([JSON.stringify(obj, null, 1)], { type: 'application/json' }));
    a.download = name;
    document.body.appendChild(a);
    a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 2000);
  }

  function slugOf(s) { return String(s || 'page').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 50); }

  function fileName(kind, slug, iso, store) {
    return 'kdp_capture_' + kind + '_' + slug + '_' + iso.slice(0, 10) + '_' + store.replace(/\./g, '-') + '.json';
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

  /* Downloads the file, then leaves a button to save it again: some browsers
   * (Firefox with "always ask") only allow a download from a direct click. */
  function save(capture, message) {
    if (TEST && !window.__KDP_AUTOPILOT__) { window.__KDP_RESULT__ = capture; return; }
    download(capture);
    say(message + ' A kdp_capture_...json file should be in your Downloads.');
    box.appendChild(document.createElement('br'));
    button('Save file again', function () { download(capture); });
    button('Close', function () { box.remove(); });
  }

  function pause() { return sleep(DELAY_MIN + Math.random() * (DELAY_MAX - DELAY_MIN)); }

  async function getDoc(url) {
    var resp = await fetch(url, { credentials: 'include' });
    return new DOMParser().parseFromString(await resp.text(), 'text/html');
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
        try { doc = await getDoc(u.toString()); } catch (e) { break; }
      }
      if (isBlocked(doc)) { capture.partial = capture.blocked = true; break; }
      var more = parseSearch(doc).filter(function (i) { return !seen[i.asin]; });
      if (!more.length) { break; }
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
      'Leave this tab open; it saves a file every 5 searches.'));
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
        cb.type = 'checkbox'; cb.value = term; cb.checked = i < parseInt(howMany.value, 10);
        row.appendChild(cb);
        row.appendChild(el('span', '', term));
        list.appendChild(row);
      });
      if (found.rows.length) {
        downloadNamed({ tool: 'kdp-capture', version: 1, type: 'suggestions', store: store,
          captured_at: new Date().toISOString(), rows: found.rows },
          fileName('suggestions', 'autocomplete', new Date().toISOString(), store));
      }
      progress(ranked.length + ' searches found (most searched first; saved as a file). ' +
        'The top ones are ticked. Change the ticks if you like, then press 2.');
    }, controls);

    button('2. Capture ticked searches', async function () {
      stopped = false;
      var terms = Array.prototype.filter.call(list.querySelectorAll('input[type=checkbox]'), function (c) { return c.checked; })
        .map(function (c) { return c.value; });
      if (!terms.length) { progress('Tick at least one search first (or press 1).'); return; }
      var books = parseInt(perSearch.value, 10) || 16;
      var part = [], partNo = 1, when = new Date().toISOString();
      function flush() {
        if (!part.length) { return; }
        downloadNamed({ tool: 'kdp-capture', version: 1, type: 'batch', store: store, captured_at: when, captures: part },
          fileName('batch', 'autopilot-part-' + partNo, when, store));
        part = [];
        partNo++;
      }
      for (var i = 0; i < terms.length && !stopped; i++) {
        var cap = await captureSearch(terms[i], null, searchUrl(terms[i]), books, function (m) {
          progress('Search ' + (i + 1) + ' of ' + terms.length + ' "' + terms[i] + '": ' + m);
        });
        part.push(cap);
        if (cap.blocked) {
          flush();
          progress('Amazon asked for a captcha after ' + (i + 1) + ' searches, so Autopilot stopped. ' +
            'Everything so far is saved. Try the rest in a few hours.');
          window.__KDP_DONE__ = true;
          return;
        }
        if (part.length >= 5) { flush(); }
      }
      flush();
      progress((stopped ? 'Stopped. ' : 'Done. ') + 'Upload the kdp_capture_batch files from Downloads.');
      window.__KDP_DONE__ = true;
    }, controls);

    button('Stop', function () { stopped = true; progress('Stopping after the current step...'); }, controls);
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

    if (asinFromUrl(location.href) || document.querySelector('#productTitle')) {
      var product = parseProduct(document, asinFromUrl(location.href));
      save(Object.assign({}, base, { type: 'product', product: product }),
        'Saved ' + (product.title || product.asin).slice(0, 60) + '.');
      return;
    }

    if (/bestsellers|movers-and-shakers|new-releases|most-wished-for|most-gifted|zgbs/.test(path)) {
      var list = parseList(document);
      var name = clean((document.querySelector('h1') || {}).textContent || document.title);
      save(Object.assign({}, base, { type: 'list', list: { kind: listKind(path), name: name }, items: list }),
        'Saved list "' + name.slice(0, 60) + '" (' + list.length + ' books).');
      return;
    }

    autopilot();
  }

  run().catch(function (e) { say('error: ' + e); });
})();

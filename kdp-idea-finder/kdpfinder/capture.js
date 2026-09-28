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
  var BETWEEN_MIN = TEST ? 0 : 15000, BETWEEN_MAX = TEST ? 5 : 30000;  /* rest between searches */
  var COOLDOWN_MIN = TEST ? 0 : (window.KDP_COOLDOWN_MIN || 60);     /* wait after a captcha */
  var STATE_KEY = 'kdp-autopilot-state';
  /* Suggestions that are rarely a book you could publish: not ticked by default. */
  var NOT_A_NICHE = /gift ?cards?|new books?|new releases?|kindle|audible|amazon|prime|\b20\d\d\b|\bby [a-z]+ [a-z]+$/;

  function loadState() { try { return JSON.parse(localStorage.getItem(STATE_KEY) || 'null'); } catch (e) { return null; } }
  function saveState(st) { try { localStorage.setItem(STATE_KEY, JSON.stringify(st)); } catch (e) { /* private window */ } }
  function clearState() { try { localStorage.removeItem(STATE_KEY); } catch (e) { /* private window */ } }

  /* Everything captured is kept here until you press Clear, so a download that
   * the browser blocked or dropped never loses data: press Save file again. */
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

  var COPY_HELP = 'Copied. On GitHub open your repository, choose Add file > Create new file, name it ' +
    'kdp_capture.json, paste (Ctrl+V) and click Commit changes.';

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

  /* Downloads the file, then leaves a button to save it again: some browsers
   * (Firefox with "always ask") only allow a download from a direct click. */
  function save(capture, message) {
    if (TEST && !window.__KDP_AUTOPILOT__) { window.__KDP_RESULT__ = capture; return; }
    download(capture);
    say(message + ' A kdp_capture_...json file should be in your Downloads.');
    box.appendChild(document.createElement('br'));
    button('Save file again', function () { download(capture); });
    button('Copy data', function () {
      copyText(capture, function (ok) { say(ok ? COPY_HELP : 'Copying failed too. Tell Claude.'); });
    });
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
      'Leave this tab open. Everything is kept in the tab and saved as one file at the end.'));
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
      var i = 0;
      for (; i < terms.length && !stopped; i++) {
        remember(i);
        var cap = await captureSearch(terms[i], null, searchUrl(terms[i]), books, function (m) {
          progress('Search ' + (i + 1) + ' of ' + terms.length + ' "' + terms[i] + '": ' + m);
        });
        if (cap.blocked) {
          remember(i, { blockedAt: Date.now() });      /* redo the interrupted search */
          downloadAll();
          progress('Amazon asked for a captcha after ' + i + ' searches. Those are saved in one file ' +
            '(press Save file if it is not in your Downloads).');
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
      downloadAll();
      if (i < terms.length) {
        remember(i);
        progress('Stopped. What was captured is saved in one file. Click KDP Capture again later to continue.');
      } else {
        clearState();
        progress('Done. Everything is saved in one kdp_capture_batch file. ' +
          'If it is not in your Downloads, press Save file.');
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
      saveBox.appendChild(el('div', '', 'Kept in this tab: ' + data.captures.length + ' searches' +
        (data.suggestions.length ? ' and the autocomplete list' : '') + '. Everything goes into one file.'));
      button('Save file', downloadAll, saveBox).id = 'kdp-save';
      button('Copy data', function () {
        copyText(bundle(), function (ok) { progress(ok ? COPY_HELP : 'Copying failed too. Tell Claude what happened.'); });
      }, saveBox).id = 'kdp-copy';
      button('Clear (after uploading)', function () { clearData(); updateSaveBox(); }, saveBox);
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
      resumeBox.appendChild(el('div', 'font-weight:700', st.remaining.length + ' searches left from your last run'));
      var info = el('div', 'margin-top:4px');
      resumeBox.appendChild(info);
      var go = button('Continue where it left off', function () {
        clearInterval(timer);
        runQueue(st.remaining, st.books || 16);
      }, resumeBox);
      go.id = 'kdp-continue';
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
          info.textContent = st.blockedAt ? 'The wait is over. Amazon should let you continue now.' : 'Stopped or closed before it finished.';
          return;
        }
        var m = Math.floor(left / 60000), sec = Math.floor(left / 1000) % 60;
        go.disabled = true;
        go.style.opacity = '.5';
        info.textContent = 'Amazon asked for a captcha. You can continue in ' + m + ':' + (sec < 10 ? '0' : '') + sec +
          '. Keep this tab open, or come back later and click KDP Capture again.';
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

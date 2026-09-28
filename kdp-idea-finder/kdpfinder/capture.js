/* KDP Capture bookmarklet.
 * Click it on an Amazon page you are looking at:
 *   - search results  -> opens the top organic results one by one (slowly) and
 *                        saves title, BSR, reviews, price, pages, publisher, date
 *   - a product page  -> saves that book
 *   - Best Sellers / Movers & Shakers / New Releases -> saves the list
 * The result downloads as kdp_capture_*.json. Import it with `kdp import`.
 * Runs in your own browser at human pace; never touches your KDP account.
 * Only block comments in this file: it is turned into a javascript: URL.
 */
(function () {
  var PAGES = window.KDP_PAGES || 3;              /* search result pages to read */
  var MAX_RESULTS = window.KDP_MAX_RESULTS || 60;  /* books to open, across all pages */
  var TEST = window.__KDP_CAPTURE_TEST__ || null;
  var DELAY_MIN = TEST ? 0 : 2500, DELAY_MAX = TEST ? 10 : 5000;

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
      items.push({
        position: items.length + 1,
        asin: asin,
        sponsored: sponsored,
        title: h2 ? clean(h2.getAttribute('aria-label') || h2.textContent) : '',
        reviews: reviews ? clean(reviews.getAttribute('aria-label') || reviews.textContent) : ''
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
    box.style.cssText = 'position:fixed;z-index:2147483647;top:12px;right:12px;max-width:340px;' +
      'background:#111;color:#fff;font:13px/1.4 system-ui,sans-serif;padding:10px 12px;' +
      'border-radius:8px;box-shadow:0 4px 18px rgba(0,0,0,.35)';
    document.body.appendChild(box);
  }
  function say(msg) { box.textContent = 'KDP Capture: ' + msg; }

  function download(capture) {
    var json = JSON.stringify(capture, null, 1);
    var slug = (capture.keyword || (capture.list && capture.list.name) || capture.product && capture.product.asin || 'page')
      .toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 50);
    var name = 'kdp_capture_' + capture.type + '_' + slug + '_' + capture.captured_at.slice(0, 10) + '_' +
      capture.store.replace(/\./g, '-') + '.json';
    var a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([json], { type: 'application/json' }));
    a.download = name;
    document.body.appendChild(a);
    a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 2000);
  }

  function button(label, onClick) {
    var b = document.createElement('button');
    b.textContent = label;
    b.style.cssText = 'margin:8px 8px 0 0;padding:4px 10px;border:0;border-radius:4px;' +
      'background:#ff9900;color:#111;font:600 12px system-ui,sans-serif;cursor:pointer';
    b.onclick = onClick;
    box.appendChild(b);
  }

  /* Downloads the file, then leaves a button to save it again: some browsers
   * (Firefox with "always ask") only allow a download from a direct click. */
  function save(capture, message) {
    if (TEST) { window.__KDP_RESULT__ = capture; return; }
    download(capture);
    say(message + ' A kdp_capture_...json file should be in your Downloads.');
    box.appendChild(document.createElement('br'));
    button('Save file again', function () { download(capture); });
    button('Close', function () { box.remove(); });
  }

  async function run() {
    var base = {
      tool: 'kdp-capture', version: 1, store: storeOf(location.hostname),
      url: location.href, captured_at: new Date().toISOString()
    };
    var path = location.pathname;
    var params = new URLSearchParams(location.search);

    if ((params.get('k') && /^\/s\/?$/.test(path)) || document.querySelector('[data-component-type="s-search-result"]')) {
      var items = parseSearch(document);
      var seen = {};
      items.forEach(function (i) { seen[i.asin] = true; });
      var startPage = parseInt(params.get('page') || '1', 10);
      var pagesRead = 1, blocked = false;
      for (var pg = startPage + 1; pg < startPage + PAGES; pg++) {
        say('reading results page ' + pg + '...');
        await sleep(DELAY_MIN + Math.random() * (DELAY_MAX - DELAY_MIN));
        var url = new URL(location.href);
        url.searchParams.set('page', String(pg));
        try {
          var pdoc = new DOMParser().parseFromString(await (await fetch(url.toString(), { credentials: 'include' })).text(), 'text/html');
          if (isBlocked(pdoc)) { blocked = true; break; }
          var more = parseSearch(pdoc).filter(function (i) { return !seen[i.asin]; });
          if (!more.length) { break; }
          more.forEach(function (i) { seen[i.asin] = true; i.page = pg; items.push(i); });
          pagesRead++;
        } catch (e) { break; }
      }
      items.forEach(function (i, idx) { i.position = idx + 1; });
      var organic = items.filter(function (i) { return !i.sponsored; }).slice(0, MAX_RESULTS);
      var capture = Object.assign({}, base, { type: 'search', keyword: params.get('k') || '', pages: pagesRead, items: items });
      if (blocked) { capture.partial = true; organic = []; }
      for (var n = 0; n < organic.length; n++) {
        var it = organic[n];
        say('reading book ' + (n + 1) + ' of ' + organic.length + ' (slow on purpose)...');
        try {
          var resp = await fetch('/dp/' + it.asin, { credentials: 'include' });
          var doc = new DOMParser().parseFromString(await resp.text(), 'text/html');
          if (isBlocked(doc)) {
            capture.partial = true;
            break;
          }
          it.product = parseProduct(doc, it.asin);
        } catch (e) {
          it.error = String(e);
        }
        await sleep(DELAY_MIN + Math.random() * (DELAY_MAX - DELAY_MIN));
      }
      var done = organic.filter(function (i) { return i.product; }).length;
      save(capture, capture.partial
        ? 'Amazon asked for a captcha, so it stopped. Saved the ' + done + ' books read so far; try again later.'
        : 'Done: "' + capture.keyword + '" (' + done + ' books from ' + pagesRead + ' pages).');
      return;
    }

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

    say('Open an Amazon Books search, a book page, or a Best Sellers / Movers & Shakers page first.');
  }

  run().catch(function (e) { say('error: ' + e); });
})();

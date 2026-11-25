/* Day Trader: read-only screen. Every number and status line comes from data.json. */
(function () {
  'use strict';

  var PAGE_SIZE = 25;
  var state = {
    data: null,
    seriesIndex: 0,
    scale: 'log',
    tradeFilter: 'tests',
    sortDesc: true,
    page: 0,
    charts: {}
  };

  // ---------- formatting ----------
  var MINUS = '\u2212';
  function pct(x, digits) {
    if (x === null || x === undefined || isNaN(x)) return 'Not recorded';
    var d = digits === undefined ? 1 : digits;
    var v = (x * 100).toFixed(d);
    if (Number(v) === 0) v = (0).toFixed(d);
    return (v.charAt(0) === '-' ? MINUS + v.slice(1) : v) + '%';
  }
  function num(x, digits) {
    if (x === null || x === undefined || isNaN(x)) return 'Not recorded';
    var s = Number(x).toLocaleString('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits });
    return s.charAt(0) === '-' ? MINUS + s.slice(1) : s;
  }
  function int(x) { return num(x, 0); }
  function money(x) {
    if (x === null || x === undefined || isNaN(x)) return 'Not recorded';
    if (Math.abs(x) >= 1) return '$' + num(x, 2);
    if (x === 0) return '$0';
    return '$' + Number(x.toPrecision(2)).toString();
  }
  function priceFmt(x) { return '$' + num(x, 2); }
  function axisMoney(v) {
    if (v >= 1) return '$' + Number(v).toLocaleString('en-US', { maximumFractionDigits: 0 });
    return '$' + Number(v.toPrecision(1)).toString();
  }
  function esc(s) {
    return String(s === null || s === undefined ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
  function $(id) { return document.getElementById(id); }
  function cssVar(name) { return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }

  // ---------- theme ----------
  function currentTheme() { return document.documentElement.getAttribute('data-theme') || 'light'; }
  function setThemeButton() {
    var b = $('theme-toggle');
    var t = currentTheme();
    b.textContent = t === 'dark' ? 'Light theme' : 'Dark theme';
    b.setAttribute('aria-label', t === 'dark' ? 'Switch to light theme' : 'Switch to dark theme');
  }
  function initTheme() {
    setThemeButton();
    $('theme-toggle').addEventListener('click', function () {
      document.documentElement.setAttribute('data-theme', currentTheme() === 'dark' ? 'light' : 'dark');
      setThemeButton();
      if (state.data) drawCharts();
    });
    if (window.matchMedia) {
      var mq = window.matchMedia('(prefers-color-scheme: dark)');
      var onChange = function (e) {
        document.documentElement.setAttribute('data-theme', e.matches ? 'dark' : 'light');
        setThemeButton();
        if (state.data) drawCharts();
      };
      if (mq.addEventListener) mq.addEventListener('change', onChange);
    }
  }

  // ---------- section 1 ----------
  function stateTone(acc) {
    return acc.trades > 0 ? 'badge-test' : 'badge-neutral';
  }
  function renderStatus(d) {
    $('freshness').textContent = 'Static snapshot. Data made ' + d.generated_utc + ' UTC. This screen only reads; it cannot trade.';
    $('headline').innerHTML = '<ul>' + (d.headline || []).map(function (h) { return '<li>' + esc(h) + '</li>'; }).join('') + '</ul>';
    $('accounts').innerHTML = (d.accounts || []).map(function (a) {
      return '<article class="card account" data-testid="card-account-' + esc(a.id) + '">' +
        '<div class="account-top"><h3 class="account-label">' + esc(a.label) + '</h3>' +
        '<span class="badge ' + stateTone(a) + '">' + esc(a.state) + '</span></div>' +
        '<p class="account-count">' + int(a.trades) + '<span>' + (a.trades === 1 ? 'trade' : 'trades') + '</span></p>' +
        '<p class="account-why">' + esc(a.why) + '</p>' +
        '</article>';
    }).join('');
    $('status-note').innerHTML = 'The same rows as the project status page. Every result here is MEASURED and read from the test output files.' +
      (d.status_link ? ' <a href="' + esc(d.status_link) + '" target="_blank" rel="noopener">Open the status page</a>' : '');
    $('status-rows').innerHTML = (d.status_rows || []).map(function (r) {
      return '<article class="card status-row">' +
        '<h4 class="status-test">' + esc(r.test) + '</h4>' +
        (r.asked ? '<p class="status-asked">' + esc(r.asked) + '</p>' : '') +
        '<p class="status-result">' + esc(r.result) + '</p>' +
        ((r.links || []).length ? '<p class="links">' + r.links.map(function (l) {
          return '<a href="' + esc(l[1]) + '" target="_blank" rel="noopener">' + esc(l[0]) + '</a>'; }).join(' ') + '</p>' : '') +
        '</article>';
    }).join('');
  }

  // ---------- section 2 ----------
  var TONE_MARK = { fail: '\u00d7', mixed: '~', unknown: '?', info: 'i' };
  function renderTests(d) {
    $('tests-list').innerHTML = (d.tests || []).map(function (t) {
      var tone = t.tone || 'unknown';
      var nums = (t.numbers || []).length
        ? '<dl class="numlist">' + t.numbers.map(function (n) {
            return '<div><dt>' + esc(n[0]) + '</dt><dd>' + esc(n[1]) + '</dd></div>';
          }).join('') + '</dl>'
        : '';
      var links = (t.links || []).length
        ? '<p class="links">' + t.links.map(function (l) {
            return '<a href="' + esc(l[1]) + '" target="_blank" rel="noopener">' + esc(l[0]) + '</a>';
          }).join('') + '</p>'
        : '';
      var table = '';
      if (t.table && t.table.length) {
        table = '<div class="tablewrap"><table class="plain"><thead><tr>' +
          '<th>Who decided</th><th>Kind</th><th class="n">Net return</th><th class="n">Largest drop</th><th class="n">Trades</th><th class="n">Time invested</th>' +
          '</tr></thead><tbody>' + t.table.map(function (r) {
            return '<tr><td>' + esc(r.name) + '</td><td>' + (r.is_ai ? 'AI run' : 'Comparison') + '</td>' +
              '<td class="n">' + pct(r.net_return) + '</td><td class="n">' + pct(r.largest_drop) + '</td>' +
              '<td class="n">' + int(r.trades) + '</td><td class="n">' + pct(r.time_invested) + '</td></tr>';
          }).join('') + '</tbody></table></div>' +
          '<p class="meta">Past-price test. Not real money.</p>';
      }
      return '<article class="card test' + (table ? ' test-wide' : '') + '" data-testid="card-test-' + esc(t.id) + '">' +
        '<div class="test-head"><h3 class="test-title">' + esc(t.title) + '</h3>' +
        '<span class="badge badge-' + esc(tone) + '"><span class="mark" aria-hidden="true">' + (TONE_MARK[tone] || '?') + '</span>' + esc(t.verdict) + '</span></div>' +
        (t.date ? '<p class="meta">Run ' + esc(t.date) + '</p>' : '') +
        '<p class="test-summary">' + esc(t.summary) + '</p>' +
        nums + table + links +
        (t.basis ? '<p class="test-basis">' + esc(t.basis) + '</p>' : '') +
        '</article>';
    }).join('');
    var col = 0, cards = $('tests-list').children;
    for (var i = 0; i < cards.length; i++) {
      var c = cards[i];
      if (c.classList.contains('test-wide')) { if (col === 1 && i > 0) cards[i - 1].classList.add('test-wide'); col = 0; continue; }
      col = (col + 1) % 2;
      if (i === cards.length - 1 && col === 1) c.classList.add('test-wide');
    }
  }

  // ---------- section 3 ----------
  function series() { return state.data.series[state.seriesIndex]; }

  function figRows(rule, hold) {
    return '<thead><tr><th>Figure</th><th class="n">Rule</th><th class="n">Just holding</th></tr></thead><tbody>' +
      '<tr><td>Growth a year</td><td class="n figval">' + pct(rule.growth_per_year) + '</td><td class="n figval">' + pct(hold.growth_per_year) + '</td></tr>' +
      '<tr><td>Largest drop</td><td class="n figval">' + pct(rule.largest_drop) + '</td><td class="n figval">' + pct(hold.largest_drop) + '</td></tr>' +
      '<tr><td>Sharpe</td><td class="n figval">' + num(rule.sharpe, 2) + '</td><td class="n figval">' + num(hold.sharpe, 2) + '</td></tr>' +
      '<tr><td>What $1 became</td><td class="n figval">' + money(rule.total_return + 1) + '</td><td class="n figval">' + money(hold.total_return + 1) + '</td></tr>' +
      '</tbody>';
  }

  function fillSeriesSelects(d) {
    var opts = d.series.map(function (s, i) { return '<option value="' + i + '">' + esc(s.label) + '</option>'; }).join('');
    $('series-select').innerHTML = opts;
    $('trade-series-select').innerHTML = opts;
    $('series-select').addEventListener('change', function (e) { selectSeries(Number(e.target.value)); });
    $('trade-series-select').addEventListener('change', function (e) { selectSeries(Number(e.target.value)); });
  }

  function selectSeries(i) {
    state.seriesIndex = i;
    state.page = 0;
    $('series-select').value = String(i);
    $('trade-series-select').value = String(i);
    renderSeries();
    renderTrades();
  }

  function renderSeries() {
    var s = series();
    $('series-note').textContent = s.note;
    var stt = s.status;
    $('series-status').innerHTML = stt
      ? '<span class="badge ' + (stt.passed ? 'badge-pass' : 'badge-fail') + '"><span class="mark" aria-hidden="true">' + (stt.passed ? '\u2713' : '\u00d7') + '</span>' +
        (stt.passed ? 'Passed' : 'Did not pass') + '</span><p>' + esc(stt.text) + '</p>'
      : '';
    $('series-meta').textContent = (s.kind || 'Past-price test') + '. ' + s.asset + ', ' + s.start + ' to ' + s.end +
      '. Fee and slippage ' + s.cost_bps_per_side + ' bps a side.';
    $('figs-full-title').textContent = 'Whole period, ' + s.start + ' to ' + s.end;
    $('figs-full').innerHTML = figRows(s.rule, s.hold);
    var r = s.rule;
    $('rule-facts').innerHTML =
      '<div><dt>Time invested</dt><dd>' + pct(r.time_invested) + '</dd></div>' +
      (r.avg_weight !== undefined ? '<div><dt>Average share of the account in the coin</dt><dd>' + pct(r.avg_weight) + '</dd></div>' : '') +
      '<div><dt>Trades a year</dt><dd>' + num(r.trades_per_year, 1) + '</dd></div>' +
      '<div><dt>Trades in total</dt><dd>' + int(r.trades) + '</dd></div>' +
      '<div><dt>Fees paid, as a share of the account</dt><dd>' + pct(r.cost_paid_share) + '<small>each trade\'s fee as a share of the account at the time, added up</small></dd></div>';
    var sc = s.since_2023;
    $('figs-since-title').textContent = (sc.label || 'Since 2023') + ': ' + sc.start + ' to ' + sc.end;
    $('figs-since').innerHTML = figRows(sc.rule, sc.hold);
    drawCharts();
  }

  function baseOptions() {
    var text = cssVar('--muted');
    var grid = cssVar('--grid');
    return {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: { backgroundColor: cssVar('--card'), titleColor: cssVar('--text'), bodyColor: cssVar('--text'), borderColor: cssVar('--border'), borderWidth: 1 }
      },
      scales: {
        x: { ticks: { color: text, font: { size: 12 } }, grid: { color: grid } },
        y: { ticks: { color: text, font: { size: 12 } }, grid: { color: grid } }
      }
    };
  }

  function toMs(d) { return Date.parse(d.length > 10 ? d.replace(' ', 'T') + 'Z' : d + 'T00:00:00Z'); }

  function yearTicks(axis) {
    var minY = new Date(axis.min).getUTCFullYear();
    var maxY = new Date(axis.max).getUTCFullYear();
    var span = maxY - minY + 1;
    var w = axis.chart.width || 600;
    var step = Math.max(1, Math.ceil(span / Math.max(2, Math.floor(w / 64))));
    var ticks = [];
    for (var y = minY; y <= maxY; y++) {
      if ((y - minY) % step) continue;
      var v = Date.UTC(y, 0, 1);
      if (v >= axis.min && v <= axis.max) ticks.push({ value: v });
    }
    axis.ticks = ticks;
  }

  function timeX(opts, rows) {
    opts.scales.x.type = 'linear';
    opts.scales.x.min = toMs(rows[0][0]);
    opts.scales.x.max = toMs(rows[rows.length - 1][0]);
    opts.scales.x.afterBuildTicks = yearTicks;
    opts.scales.x.ticks.callback = function (v) { return String(new Date(v).getUTCFullYear()); };
    opts.scales.x.ticks.autoSkip = false;
    opts.scales.x.ticks.maxRotation = 0;
    opts.plugins.tooltip.callbacks = opts.plugins.tooltip.callbacks || {};
    opts.plugins.tooltip.callbacks.title = function (items) {
      return items.length ? new Date(items[0].parsed.x).toISOString().slice(0, 10) : '';
    };
  }

  function lineSets(rows, fmt) {
    var rule = cssVar('--rule'), hold = cssVar('--hold');
    return [
      { label: 'Rule', data: rows.map(function (r) { return { x: toMs(r[0]), y: r[1] }; }), borderColor: rule, backgroundColor: rule, borderWidth: 2, pointRadius: 0, tension: 0 },
      { label: 'Just holding', data: rows.map(function (r) { return { x: toMs(r[0]), y: r[2] }; }), borderColor: hold, backgroundColor: hold, borderWidth: 1.5, borderDash: [6, 4], pointRadius: 0, tension: 0 }
    ];
  }

  function destroy(key) { if (state.charts[key]) { state.charts[key].destroy(); delete state.charts[key]; } }

  function drawCharts() {
    if (typeof Chart === 'undefined') return;
    var s = series();

    // Account value
    destroy('equity');
    var eo = baseOptions();
    timeX(eo, s.equity);
    eo.plugins.tooltip.callbacks.label = function (c) { return c.dataset.label + ': ' + money(c.parsed.y); };
    if (state.scale === 'log') {
      eo.scales.y.type = 'logarithmic';
      eo.scales.y.afterBuildTicks = function (axis) {
        var lo = Math.floor(Math.log10(axis.min)), hi = Math.ceil(Math.log10(axis.max));
        var t = [];
        for (var e = lo; e <= hi; e++) { var v = Math.pow(10, e); if (v >= axis.min * 0.999 && v <= axis.max * 1.001) t.push({ value: v }); }
        if (t.length < 2) t = [{ value: axis.min }, { value: axis.max }];
        axis.ticks = t;
      };
    } else {
      eo.scales.y.type = 'linear';
      eo.scales.y.beginAtZero = true;
    }
    eo.scales.y.ticks.callback = function (v) { return axisMoney(Number(v)); };
    state.charts.equity = new Chart($('chart-equity'), { type: 'line', data: { datasets: lineSets(s.equity) }, options: eo });

    // Drawdown
    destroy('drawdown');
    var dopt = baseOptions();
    timeX(dopt, s.drawdown);
    dopt.scales.y.max = 0;
    dopt.scales.y.ticks.callback = function (v) { return pct(Number(v), 0); };
    dopt.plugins.tooltip.callbacks.label = function (c) { return c.dataset.label + ': ' + pct(c.parsed.y); };
    state.charts.drawdown = new Chart($('chart-drawdown'), { type: 'line', data: { datasets: lineSets(s.drawdown) }, options: dopt });

    // Yearly
    destroy('yearly');
    var yo = baseOptions();
    yo.scales.x.grid = { display: false };
    yo.scales.x.ticks.maxRotation = 0;
    yo.scales.x.ticks.autoSkip = true;
    yo.scales.y.ticks.callback = function (v) { return pct(Number(v), 0); };
    yo.plugins.tooltip.callbacks = { label: function (c) { return c.dataset.label + ': ' + pct(c.parsed.y); } };
    var rc = cssVar('--rule'), hc = cssVar('--hold');
    state.charts.yearly = new Chart($('chart-yearly'), {
      type: 'bar',
      data: {
        labels: s.yearly.map(function (r) { return String(r[0]); }),
        datasets: [
          { label: 'Rule', data: s.yearly.map(function (r) { return r[1]; }), backgroundColor: rc, borderColor: rc, borderWidth: 0 },
          { label: 'Just holding', data: s.yearly.map(function (r) { return r[2]; }), backgroundColor: hc, borderColor: hc, borderWidth: 0 }
        ]
      },
      options: yo
    });
  }

  function initScale() {
    var btns = document.querySelectorAll('[data-scale]');
    btns.forEach(function (b) {
      b.addEventListener('click', function () {
        state.scale = b.getAttribute('data-scale');
        btns.forEach(function (o) { o.setAttribute('aria-pressed', o === b ? 'true' : 'false'); });
        drawCharts();
      });
    });
  }

  // ---------- section 4 ----------
  function initTradeFilter(d) {
    var el = $('trade-filter');
    el.innerHTML = d.accounts.map(function (a) {
      return '<button type="button" class="seg-btn" data-filter="' + esc(a.id) + '" aria-pressed="' + (a.id === state.tradeFilter) + '">' +
        esc(a.label) + '<span class="count">' + int(a.trades) + '</span></button>';
    }).join('');
    el.addEventListener('click', function (e) {
      var b = e.target.closest('[data-filter]');
      if (!b) return;
      state.tradeFilter = b.getAttribute('data-filter');
      state.page = 0;
      el.querySelectorAll('[data-filter]').forEach(function (o) { o.setAttribute('aria-pressed', o === b ? 'true' : 'false'); });
      renderTrades();
    });
  }

  function renderTrades() {
    var d = state.data;
    var body = $('trade-body');
    var acc = d.accounts.filter(function (a) { return a.id === state.tradeFilter; })[0];
    var isTests = state.tradeFilter === 'tests';
    $('trade-series-field').hidden = !isTests;

    if (!isTests) {
      body.innerHTML = '<div class="empty" data-testid="empty-trades"><h3>No trades in ' + esc(acc ? acc.label : 'this account') + '</h3>' +
        '<p><strong>' + esc(acc ? acc.state : '') + '.</strong> ' + esc(acc ? acc.why : '') + '</p></div>';
      return;
    }

    var s = series();
    var rows = s.trades_list.slice();
    if (!state.sortDesc) rows.reverse();
    var pages = Math.max(1, Math.ceil(rows.length / PAGE_SIZE));
    if (state.page >= pages) state.page = pages - 1;
    var startI = state.page * PAGE_SIZE;
    var pageRows = rows.slice(startI, startI + PAGE_SIZE);
    var shownNote = s.trades_shown < s.trades_total
      ? 'Showing the latest ' + int(s.trades_shown) + ' of ' + int(s.trades_total) + ' trades.'
      : 'Showing all ' + int(s.trades_total) + ' trades.';

    body.innerHTML =
      '<div class="trade-info"><p><span class="testlabel">Past-price test. Not real money.</span> ' + esc(s.label) + '. ' + shownNote + '</p></div>' +
      '<div class="tablewrap"><table class="trades-table"><thead><tr>' +
        '<th><button type="button" class="sort-btn" id="sort-time" aria-label="Sort by time, now ' + (state.sortDesc ? 'newest first' : 'oldest first') + '">Time (UTC) <span aria-hidden="true">' + (state.sortDesc ? '\u2193' : '\u2191') + '</span></button></th>' +
        '<th>Buy or sell</th><th class="n">Price</th><th class="n">Share of account traded</th><th class="n">Fee, share of account</th>' +
      '</tr></thead><tbody>' +
      pageRows.map(function (t) {
        return '<tr><td>' + esc(t.time) + '</td><td class="act">' + esc(t.action) + '</td>' +
          '<td class="n">' + priceFmt(t.price) + '</td><td class="n">' + pct(t.share_of_account) + '</td>' +
          '<td class="n">' + pct(t.cost_share_of_account, 3) + '</td></tr>';
      }).join('') +
      '</tbody></table></div>' +
      '<div class="pager"><p class="pager-info">Rows ' + int(rows.length ? startI + 1 : 0) + ' to ' + int(startI + pageRows.length) + ' of ' + int(rows.length) + ', ' + (state.sortDesc ? 'newest first' : 'oldest first') + '</p>' +
      '<div class="pager-btns"><button type="button" class="btn" id="pg-prev"' + (state.page === 0 ? ' disabled' : '') + '>Previous</button>' +
      '<button type="button" class="btn" id="pg-next"' + (state.page >= pages - 1 ? ' disabled' : '') + '>Next</button></div></div>';

    $('sort-time').addEventListener('click', function () { state.sortDesc = !state.sortDesc; state.page = 0; renderTrades(); $('sort-time').focus(); });
    $('pg-prev').addEventListener('click', function () { if (state.page > 0) { state.page--; renderTrades(); focusPager('pg-prev'); } });
    $('pg-next').addEventListener('click', function () { if (state.page < pages - 1) { state.page++; renderTrades(); focusPager('pg-next'); } });
  }
  function focusPager(id) {
    var b = $(id);
    if (b && !b.disabled) b.focus(); else { var o = $(id === 'pg-next' ? 'pg-prev' : 'pg-next'); if (o) o.focus(); }
  }

  // ---------- sections 5 and 6 ----------
  function renderWaiting(d) {
    var items = d.waiting_on_you || [];
    $('waitlist').innerHTML = items.length ? items.map(function (w) {
      return '<li><div><strong>' + esc(w[0]) + '</strong><span>' + esc(w[1]) + '</span></div></li>';
    }).join('') : '<li class="wait-empty"><div><strong>' + esc(d.waiting_problem || 'Nothing is listed.') + '</strong><span>Open the full list below.</span></div></li>';
    $('waitlink').innerHTML = d.waiting_link ? '<a href="' + esc(d.waiting_link) + '" target="_blank" rel="noopener">See the full list</a>' : '';
  }
  function renderGlossary(d) {
    $('glossary').innerHTML = (d.glossary || []).map(function (g) {
      return '<dt>' + esc(g[0]) + '</dt><dd>' + esc(g[1]) + '</dd>';
    }).join('');
  }

  // ---------- nav highlight ----------
  function initNav() {
    var links = Array.prototype.slice.call(document.querySelectorAll('.sectionnav a'));
    var sections = Array.prototype.slice.call(document.querySelectorAll('main section[id]'));
    var ticking = false;
    function update() {
      ticking = false;
      var bar = document.querySelector('.topbar').getBoundingClientRect().bottom + 48;
      var current = sections[0];
      sections.forEach(function (s) { if (s.getBoundingClientRect().top <= bar) current = s; });
      if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 2) current = sections[sections.length - 1];
      links.forEach(function (l) {
        var on = l.getAttribute('href') === '#' + current.id;
        l.classList.toggle('active', on);
        if (on) {
          l.setAttribute('aria-current', 'true');
          var nav = l.parentNode, lr = l.getBoundingClientRect(), nr = nav.getBoundingClientRect();
          if (lr.left < nr.left || lr.right > nr.right) nav.scrollLeft += (lr.left - nr.left) - (nr.width - lr.width) / 2;
        } else l.removeAttribute('aria-current');
      });
    }
    window.addEventListener('scroll', function () { if (!ticking) { ticking = true; setTimeout(update, 50); } }, { passive: true });
    window.addEventListener('resize', update);
    update();
    state.updateNav = update;
  }

  // ---------- boot ----------
  function showError(msg) {
    var e = $('load-error');
    e.hidden = false;
    e.innerHTML = msg;
    $('freshness').textContent = 'No data loaded';
  }

  function boot() {
    initTheme();
    initScale();
    initNav();
    fetch('data.json', { cache: 'no-store' })
      .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(function (d) {
        state.data = d;
        renderStatus(d);
        $('compare-notes').innerHTML = (d.compare_notes || []).map(function (n) { return '<p>' + esc(n) + '</p>'; }).join('');
        renderTests(d);
        fillSeriesSelects(d);
        initTradeFilter(d);
        renderWaiting(d);
        renderGlossary(d);
        if (typeof Chart === 'undefined') {
          document.querySelectorAll('.chartbox').forEach(function (b) {
            b.innerHTML = '<div class="empty"><h3>Charts could not load</h3><p>The chart file vendor/chart.umd.min.js did not load. Check that it is in the dashboard folder, then reload.</p></div>';
          });
        }
        selectSeries(0);
        if (state.updateNav) state.updateNav();
        window.__dashReady = true;
      })
      .catch(function () {
        showError('Could not read <code>data.json</code>. Make it with <code>research_rig/export_dashboard.py</code>, put it in this folder, then run <code>python3 -m http.server</code> here and open the address it prints.');
      });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();

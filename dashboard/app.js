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
      if (state.data) { drawCharts(); drawPracticeChart(); }
    });
    if (window.matchMedia) {
      var mq = window.matchMedia('(prefers-color-scheme: dark)');
      var onChange = function (e) {
        document.documentElement.setAttribute('data-theme', e.matches ? 'dark' : 'light');
        setThemeButton();
        if (state.data) { drawCharts(); drawPracticeChart(); }
      };
      if (mq.addEventListener) mq.addEventListener('change', onChange);
    }
  }

  // ---------- section 1 ----------
  function stateTone(acc) {
    return acc.trades > 0 ? 'badge-test' : 'badge-neutral';
  }
  function renderStatus(d) {
    $('freshness').textContent = 'Static snapshot. Data made ' + mtFromUtc(d.generated_utc) + '. All times are Mountain Time. This screen only reads; it cannot trade.';
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
        '<p class="status-result">' + esc(mtStampsIn(r.result)) + '</p>' +
        ((r.links || []).length ? '<p class="links">' + r.links.map(function (l) {
          return '<a href="' + esc(l[1]) + '" target="_blank" rel="noopener">' + esc(l[0]) + '</a>'; }).join(' ') + '</p>' : '') +
        '</article>';
    }).join('');
  }

  // ---------- what we believe now ----------
  function renderScoreboard(d) {
    var score = d.scoreboard;
    var body = $('scoreboard-body');
    if (!score) { body.innerHTML = '<p class="meta">Export a new snapshot to see the scoreboard.</p>'; return; }
    function report(row, label) {
      return '<a href="' + esc(row.url) + '" target="_blank" rel="noopener">' + esc(label) + '</a>';
    }
    body.innerHTML =
      '<p><strong>' + int(score.tests) + '</strong> tests run · <strong>' + int(score.passed) + '</strong> passed · <strong>' + int(score.did_not_pass) + '</strong> did not pass</p>' +
      '<p><strong>Passes:</strong> ' + (score.passes.map(function (row) {
        return report(row, row.label) + (row.name ? ': ' + esc(row.name) : '') + (row.scope ? ' (' + esc(row.scope) + ')' : '');
      }).join('; ') || 'None') + '</p>' +
      '<p><strong>Latest five results:</strong> ' + score.latest.map(function (row) {
        return report(row, row.label) + ': ' + esc(row.verdict);
      }).join('; ') + '</p>';
  }

  var BELIEVED_FIRST = 6;
  function believedLink(l) {
    var m = /^(\d+)_/.exec(l[0]);
    return '<a href="' + esc(l[1]) + '" target="_blank" rel="noopener">' + esc(m ? 'Write-up ' + String(+m[1]) : l[0]) + '</a>';
  }
  function renderBelieved(d) {
    var body = $('believed-body');
    if (!body) return;
    var list = d.believed || [];
    if (!list.length) { body.innerHTML = '<p class="meta">Nothing was read from the status page.</p>'; return; }
    var html = '<ul class="believed-list" id="believed-list">' + list.map(function (b, i) {
      var lead = String(b.lead || '');
      var stop = /[.?:]$/.test(lead) ? '' : '.';
      return '<li class="believed-item"' + (i >= BELIEVED_FIRST ? ' hidden' : '') + '><span class="believed-lead">' + esc(mtStampsIn(lead) + stop) + '</span>' +
        (b.body ? ' ' + esc(b.body).replace(/\d{4}-\d{2}-\d{2}(?: \d{2}:\d{2}(?::\d{2})? UTC)?/g, function (x) { return '<span class="believed-date">' + esc(/UTC$/.test(x) ? mtFromUtc(x) : x) + '</span>'; }) : '') +
        ((b.links || []).length ? ' <span class="believed-links">' + b.links.map(believedLink).join(', ') + '</span>' : '') + '</li>';
    }).join('') + '</ul>';
    if (list.length > BELIEVED_FIRST) {
      html += '<button type="button" class="btn believed-more" aria-expanded="false" aria-controls="believed-list">Show all ' + int(list.length) + '</button>';
    }
    body.innerHTML = html;
    var btn = body.querySelector('.believed-more');
    if (btn) btn.addEventListener('click', function () {
      var open = btn.getAttribute('aria-expanded') !== 'true';
      Array.prototype.forEach.call(body.querySelectorAll('.believed-item'), function (li, i) { if (i >= BELIEVED_FIRST) li.hidden = !open; });
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      btn.textContent = open ? 'Show the first ' + BELIEVED_FIRST + ' only' : 'Show all ' + int(list.length);
    });
  }

  // ---------- section 2 ----------
  var TONE_MARK = { fail: '\u00d7', mixed: '~', unknown: '?', info: 'i' };
  // Keep a date such as 2024-01-01, 2026-11-26 17:00 MT or 2026-11-26 5:39 PM MT, on one line, so a narrow screen does not split it at a hyphen.
  function keepDates(html) { return html.replace(/\b(\d{4}-\d{2}-\d{2}(?: \d{1,2}:\d{2}(?: [AP]M)? MT)?|\d{1,2}:\d{2}(?: [AP]M)? MT)(?![\w:])/g, '<span class="nowrap">$1</span>'); }

  // A small bar chart drawn in plain HTML, so it reads on a phone. Each bar has its value written beside it.
  function barsHtml(b) {
    var rows = b.rows || [];
    var top = Math.max.apply(null, rows.map(function (r) { return Math.abs(r[1]); }).concat([1e-9]));
    return '<figure class="hbars" aria-label="' + esc(b.label) + '"><figcaption class="meta">' + esc(b.label) + '</figcaption>' +
      rows.map(function (r) {
        var v = r[1], w = (Math.abs(v) / top * 50).toFixed(1);
        var txt = (v < 0 ? '\u2212' : '+') + Math.abs(v).toFixed(1) + (b.unit === '%' ? '' : ' ') + esc(b.unit);
        return '<div class="hbar"><span class="hbar-label">' + esc(r[0]) + '</span>' +
          '<span class="hbar-track"><span class="hbar-zero" aria-hidden="true"></span><span class="hbar-fill ' + (v < 0 ? 'neg' : 'pos') + '" style="' +
          (v < 0 ? 'right:50%' : 'left:50%') + ';width:' + w + '%"></span></span>' +
          '<span class="hbar-val' + (v < 0 ? ' neg' : '') + '">' + txt + '</span></div>';
      }).join('') + '</figure>';
  }
  function renderNewest(d) {
    $('newest-list').innerHTML = (d.newest || []).map(testCard).join('');
    layoutCards($('newest-list'));
    var rows = d.running_now || [];
    $('running-body').innerHTML = rows.length
      ? '<ol class="running-list">' + rows.map(function (r) {
          return '<li><span class="running-num">' + (r[0] === '-' ? 'No number' : 'Row ' + esc(r[0])) + '</span><span class="running-what">' + esc(mtStampsIn(r[1])) +
            (r[2] ? ' <span class="running-state' + (/^Stopped|^On hold/.test(r[2]) ? ' running-stopped' : '') + '">' + keepDates(esc(r[2])) + '</span>' : '') + '</span></li>';
        }).join('') + '</ol>' + (d.running_link ? '<p class="links"><a href="' + esc(d.running_link) + '" target="_blank" rel="noopener">Open the queue page</a></p>' : '')
      : '<p class="meta">Nothing is listed as running.</p>';
  }
  function renderTests(d) {
    $('tests-list').innerHTML = (d.tests || []).map(testCard).join('');
    layoutCards($('tests-list'));
  }
  function testCard(t) {
      var tone = t.tone || 'unknown';
      var nums = (t.numbers || []).length
        ? '<dl class="numlist">' + t.numbers.map(function (n) {
            return '<div><dt>' + keepDates(esc(n[0])) + '</dt><dd>' + esc(n[1]) + '</dd></div>';
          }).join('') + '</dl>'
        : '';
      // Optional side-by-side figures: t.columns = {head: ['', 'A', 'B'], rows: [[label, a, b], ...]}.
      var cols = t.columns && (t.columns.rows || []).length
        ? '<div class="tablewrap"><table class="cols"><thead><tr>' + t.columns.head.map(function (h, i) {
            return '<th' + (i ? ' class="n"' : '') + '>' + esc(h) + '</th>';
          }).join('') + '</tr></thead><tbody>' + t.columns.rows.map(function (r) {
            return '<tr>' + r.map(function (c, i) { return i ? '<td class="n">' + esc(c) + '</td>' : '<th scope="row">' + esc(c) + '</th>'; }).join('') + '</tr>';
          }).join('') + '</tbody></table></div>'
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
        '<p class="test-summary">' + keepDates(esc(t.summary)) + '</p>' +
        nums + cols + (t.bars ? barsHtml(t.bars) : '') + table + links +
        (t.basis ? '<p class="test-basis">' + esc(t.basis) + '</p>' : '') +
        '</article>';
  }
  function layoutCards(list) {
    var col = 0, cards = list.children;
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
      ? '<span class="badge badge-' + esc(stt.tone || (stt.passed ? 'pass' : 'fail')) + '"><span class="mark" aria-hidden="true">' +
        (stt.tone ? (TONE_MARK[stt.tone] || '?') : (stt.passed ? '\u2713' : '\u00d7')) + '</span>' +
        esc(stt.label || (stt.passed ? 'Passed' : 'Did not pass')) + '</span><p>' + esc(stt.text) + '</p>'
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

    var pr = practice.summary;
    if (state.tradeFilter === 'practice' && pr && pr.orders && pr.orders.length) {
      body.innerHTML = '<p data-testid="practice-trades-pointer">Practice trades are listed in the <a href="#practice">Practice account section</a> at the top of the page.</p>';
      return;
    }
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
        '<th><button type="button" class="sort-btn" id="sort-time" aria-label="Sort by time, now ' + (state.sortDesc ? 'newest first' : 'oldest first') + '">Time (Mountain) <span aria-hidden="true">' + (state.sortDesc ? '\u2193' : '\u2191') + '</span></button></th>' +
        '<th>Buy or sell</th><th class="n">Price</th><th class="n">Share of account traded</th><th class="n">Fee, share of account</th>' +
      '</tr></thead><tbody>' +
      pageRows.map(function (t) {
        return '<tr><td>' + esc(mtFromUtc(t.time)) + '</td><td class="act">' + esc(t.action) + '</td>' +
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
      var rec = w[2] ? '<span class="wait-rec">Research recommends: ' + esc(w[2]) + '</span>' : '';
      var more = w[1] ? (w[2] ? '<details><summary>What this covers</summary><p>' + esc(w[1]) + '</p></details>' : '<span>' + esc(w[1]) + '</span>') : '';
      return '<li><div><strong>' + esc(w[0]) + '</strong>' + rec + more + '</div></li>';
    }).join('') : '<li class="wait-empty"><div><strong>' + esc(d.waiting_problem || 'Nothing is listed.') + '</strong><span>Open the full list below.</span></div></li>';
    $('waitlink').innerHTML = d.waiting_link ? '<a href="' + esc(d.waiting_link) + '" target="_blank" rel="noopener">See the status page</a>' : '';
  }
  function renderGlossary(d) {
    $('glossary').innerHTML = (d.glossary || []).map(function (g) {
      return '<dt>' + esc(g[0]) + '</dt><dd>' + esc(g[1]) + '</dd>';
    }).join('');
  }

  // ---------- live desk, card E15 (fields written by practice/desk_e15.py publish; local only) ----------
  function renderDesk(d) {
    var k = d.desk_e15;
    if (!k) { $('desk-body').innerHTML = '<p class="meta">The live desk has not been published yet.</p>'; return; }
    function mt(s) { return s ? mtFromUtc(s) : '-'; }
    function pct(x) { return isNum(x) ? (x * 100).toFixed(2).replace('-', '\u2212') + '%' : '-'; }
    function kv(o) { return Object.keys(o || {}).map(function (x) { return esc(x) + ' ' + esc(o[x]); }).join(', ') || 'none'; }
    var h = '<p><strong>' + esc(k.status) + '</strong>' + (k.stop ? ', stopped: ' + esc(k.stop.reason) : '') +
      '. Gate: ' + esc(k.gate) + '. Last wake ' + esc(mt(k.last_wake_utc)) + ', next ' + esc(mt(k.next_wake_utc)) +
      '. Scout calls ' + esc(k.scout_calls) + ' (' + kv(k.scout_status) + ').</p>';
    ['W', 'F'].forEach(function (c) {
      var x = k[c] || {};
      h += '<h3>Card ' + c + ': ' + esc(x.label) + '</h3><p>Signals ' + esc(x.signals) + '. Open by line: ' + kv(x.open_by_line) +
        '. Closed pairs: ' + kv(x.closed_pairs) + ' of ' + esc(x.judging_count) + '. Entries: ' + kv(x.entries_by_line_and_status) + '.</p>';
    });
    var s = k.S || {};
    h += '<h3>Card S</h3><p class="meta">' + esc(s.label) + '</p>';
    h += '<p>' + Object.keys(s.gap || {}).map(function (l) { var g = s.gap[l];
      return esc(l) + ' (' + esc(g.model) + '): ' + esc(g.pairs) + ' paired scans, running gap against random ' + pct(g.running_gap_sum) + ' summed, ' + pct(g.running_gap_mean) + ' a scan'; }).join('; ') + '.</p>';
    h += '<h4>Open pretend positions</h4><ul>' + ((s.open || []).map(function (o) {
      return '<li>' + esc(o.line) + ' ' + esc(o.coin) + ', in ' + esc(mt(o.entry_utc)) + ', exit due ' + esc(mt(o.exit_due_utc)) + '</li>'; }).join('') || '<li>None</li>') + '</ul>';
    h += '<h4>Last proposals</h4><ul>' + ((s.last_proposals || []).map(function (p) {
      return '<li>' + esc(mt(p.wake_utc)) + ' ' + esc(p.line) + ': ' + esc(p.choice || 'no reply') + (p.tags && p.tags.length ? ' [' + esc(p.tags.join(', ')) + ']' : '') +
        ', ' + esc(p.outcome || '-') + (p.reason && p.reason !== 'ok' ? ' (' + esc(p.reason) + ')' : '') + '</li>'; }).join('') || '<li>None yet</li>') + '</ul>';
    var closed = (s.closed || []).slice().reverse();   // every closed pretend trade, newest exit first
    h += '<h4>Closed pretend trades</h4><ul>' + (closed.map(function (c) {
      return '<li>' + esc(c.line) + ' ' + esc(c.coin) + ', ' + esc(mt(c.entry_utc)) + ' to ' + esc(mt(c.exit_utc)) + ': ' + (c.status === 'ok' ? pct(c.net) : esc(c.status)) + '</li>'; }).join('') || '<li>None yet</li>') + '</ul>';
    $('desk-body').innerHTML = h;
  }

  // ---------- practice account ----------
  // The practice desk's summary.json (practice/trader.py, Run.summary). The copy in data.json is shown first,
  // then the page quietly asks practice_live_url for a newer one. Nothing here can place or change an order.
  var practice = { summary: null, source: 'baked', check: 'none', open: {}, hl: '', ordersShown: (window.innerWidth || 1200) < 700 ? 10 : 25, ordersTrader: '', closedShown: (window.innerWidth || 1200) < 700 ? 10 : 25, ghBase: '' };
  var PR_PAGE = (window.innerWidth || 1200) < 700 ? 10 : 25;

  function isNum(x) { return typeof x === 'number' && isFinite(x); }
  function timeOf(s) { var t = Date.parse(s || ''); return isNaN(t) ? null : t; }
  // The owner reads Mountain Time. Stored stamps stay UTC; the screen converts them.
  var OWNER_ZONE = 'America/Boise';
  // The owner asked for the label MT, not MST or MDT.
  function mtLabel(s) { return String(s).replace(/\bM[SD]T\b/, 'MT'); }
  function mtText(t) {
    try {
      return mtLabel(new Date(t).toLocaleString('en-US', { timeZone: OWNER_ZONE, year: 'numeric', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit', timeZoneName: 'short' }));
    } catch (e) { return new Date(t).toISOString().slice(0, 16).replace('T', ' ') + ' UTC'; }
  }
  // Turns 'YYYY-MM-DD HH:MM[:SS][ UTC]' (a UTC stamp) into Mountain Time. Anything else is returned as it is.
  function mtFromUtc(s) {
    var m = /^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})(?::(\d{2}))?(?:\.\d+)?(?:Z| UTC)?$/.exec(String(s || ''));
    return m ? mtText(Date.UTC(+m[1], +m[2] - 1, +m[3], +m[4], +m[5], +(m[6] || 0))) : String(s || '');
  }
  function mtInText(s) {
    return String(s || '').replace(/\d{4}-\d{2}-\d{2} \d{2}:\d{2}(?::\d{2})?(?: UTC)?/g, function (x) { return mtFromUtc(x); });
  }
  // Converts only stamps that say UTC ('YYYY-MM-DD HH:MM[:SS] UTC') inside a sentence.
  function mtStampsIn(s) {
    return String(s || '').replace(/\d{4}-\d{2}-\d{2} \d{2}:\d{2}(?::\d{2})? UTC/g, function (x) { return mtFromUtc(x); })
      .replace(/(\d{2}:\d{2}) UTC on (\d{4}-\d{2}-\d{2})/g, function (x, hm, day) { return mtFromUtc(day + ' ' + hm); });
  }
  function utcText(s) {
    var t = timeOf(s);
    return t === null ? (s ? String(s) : 'Not recorded') : new Date(t).toISOString().slice(0, 16).replace('T', ' ') + ' UTC';
  }
  function localText(t, withZone) {
    var d = new Date(t), now = new Date();
    var o = { timeZone: OWNER_ZONE, month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' };
    if (d.getFullYear() !== now.getFullYear()) o.year = 'numeric';
    if (withZone !== false) o.timeZoneName = 'short';
    try { return mtLabel(d.toLocaleString('en-US', o)); } catch (e) { return d.toISOString().slice(0, 16).replace('T', ' ') + ' UTC'; }
  }
  // A time in the owner's local time, with the UTC time in the title.
  function timeTag(s, fallback) {
    var t = timeOf(s);
    if (t === null) return esc(fallback || 'Not recorded');
    return '<time datetime="' + esc(new Date(t).toISOString()) + '" title="' + esc(utcText(s)) + '">' + esc(localText(t)) + '</time>';
  }
  function signedMoney(x) {
    if (!isNum(x)) return 'Not recorded';
    if (Math.abs(x) < 0.005) return '$0.00';
    return (x < 0 ? MINUS : '+') + '$' + num(Math.abs(x), 2);
  }
  function signedPct(x, digits) {
    if (!isNum(x)) return 'Not recorded';
    var dg = digits === undefined ? 2 : digits;
    var p = pct(x, dg);
    return x > 0 && Number((x * 100).toFixed(dg)) !== 0 ? '+' + p : p;
  }
  function money2(x) { return isNum(x) ? (x < 0 ? MINUS : '') + '$' + num(Math.abs(x), 2) : 'Not recorded'; }
  function priceAny(x) {
    if (!isNum(x)) return 'Not recorded';
    var a = Math.abs(x), dg = a >= 1 ? 2 : (a >= 0.01 ? 4 : 8);
    return (x < 0 ? MINUS : '') + '$' + num(a, dg);
  }
  function qtyFmt(x) {
    if (!isNum(x)) return 'Not recorded';
    var s = Number(x).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 8 });
    return s.charAt(0) === '-' ? MINUS + s.slice(1) : s;
  }
  function negCls(x) { return isNum(x) && x < 0 ? 'neg' : ''; }
  function gainHtml(usd, p) {
    var ref = isNum(usd) ? usd : p;
    if (!isNum(usd) && !isNum(p)) return 'Not recorded';
    var parts = [];
    if (isNum(usd)) parts.push(signedMoney(usd));
    if (isNum(p)) parts.push(isNum(usd) ? '(' + signedPct(p) + ')' : signedPct(p));
    return '<span class="' + negCls(ref) + '">' + esc(parts.join(' ')) + '</span>';
  }
  function capital(s) { s = String(s || ''); return s ? s.charAt(0).toUpperCase() + s.slice(1) : 'Not recorded'; }
  function plural(n, one, many) { return int(n) + ' ' + (n === 1 ? one : many); }
  function safeUrl(u) { return typeof u === 'string' && /^https?:\/\//i.test(u) ? u : null; }
  function traders() { return (practice.summary && practice.summary.traders) || []; }
  function traderById(id) { var l = traders(); for (var i = 0; i < l.length; i++) if (l[i].id === id) return l[i]; return null; }
  function traderName(id) { var t = traderById(id); return t ? (t.name || t.id) : (id || 'Not recorded'); }
  function kindText(t) {
    if (t.kind === 'ai') return 'AI' + (t.model ? ', ' + t.model : '');
    if (t.kind === 'rule') return 'Fixed rule';
    return capital(t.kind);
  }

  var PR_STATE = {
    waiting_for_key: { label: 'Waiting for the key', cls: 'badge-neutral', mark: '' },
    running: { label: 'Running', cls: 'badge-test', mark: '' },
    halted: { label: 'Stopped, needs you', cls: 'badge-fail', mark: '\u00d7' }
  };

  function recordsLine(s) {
    var parts = [];
    if (!(s && timeOf(s.made_utc) !== null)) parts.push('No records yet.');
    else if (!(s.last_check_utc && timeOf(s.last_check_utc) === timeOf(s.made_utc))) parts.push('Records as of ' + timeTag(s.made_utc) + '.');
    if (practice.check === 'checking') parts.push('Checking for newer records.');
    else if (practice.check === 'failed') parts.push('Could not check for newer records.');
    else if (practice.source === 'live') parts.push('This is the newest copy from the records branch.');
    else if (practice.check === 'same') parts.push('Checked for newer records, none found.');
    return parts.join(' ');
  }
  function setRecordsLine() {
    var el = $('practice-records');
    if (el) el.innerHTML = recordsLine(practice.summary);
  }

  function kpi(label, value, sub, cls) {
    return '<div class="card pr-kpi' + (cls || '') + '"><p class="pr-kpi-label">' + esc(label) + '</p>' +
      '<p class="pr-kpi-value">' + value + '</p>' + (sub ? '<p class="pr-kpi-sub">' + sub + '</p>' : '') + '</div>';
  }
  // ---------- time machine ----------
  function tmMoney(x) { return isNum(x) ? '<span class="' + negCls(x) + '">' + esc(signedMoney(x)) + '</span>' : '<span class="muted">Not yet</span>'; }
  function tmVerdict(v) {
    v = String(v || 'not finished');
    var cls = /^(not finished|running|not started|being scored|passes line [12] only)$/.test(v) ? 'badge-neutral' :
      (/^counts|helped: six|^passes both lines$|^passes$|^shown$/.test(v) ? 'badge-pass' : 'badge-fail');
    return '<span class="badge ' + cls + '">' + esc(capital(v)) + '</span>';
  }
  function tmPct(x) { return isNum(x) ? esc(num(x, 1)) : '<span class="muted">None</span>'; }
  function tmLinks(pl) {
    return '<p class="links">' + (pl.doc ? '<a href="' + esc(pl.doc) + '" target="_blank" rel="noopener noreferrer">Full results</a> ' : '') +
      '<a href="' + esc(pl.plan) + '" target="_blank" rel="noopener noreferrer">The plan, fixed before the run</a></p>';
  }
  function tmSessions(se, unit) {
    if (!se) return '';
    return esc(int(se.finished)) + ' of ' + esc(int(se.planned)) + ' ' + unit + ' finished' +
      (se.running ? ', ' + esc(int(se.running)) + ' still running' : '') + (se.not_started ? ', ' + esc(int(se.not_started)) + ' not started' : '') + '.';
  }
  var TM_NF = '<span class="muted">Not finished</span>';
  function tmDial(pl, tm) {
    var start = isNum(pl.start_usd) ? pl.start_usd : tm.start_usd;
    var h = '<div class="card pr-block tm-plan" data-testid="tm-plan-TM03"><h3 class="h3">' + esc(pl.label) + '</h3>' +
      '<p>Once a day each model sets how much of a ' + esc(money2(start)) + ' pretend-money account to keep in bitcoin, one month at a time, ' +
      esc(int(pl.months)) + ' months in all. Ahead of holding with a low percentile means it held less bitcoin while bitcoin fell. That is less risk held, not timing skill.</p>' +
      '<p class="meta">' + tmSessions(pl.sessions, 'month-long sessions') + ' A model gets figures only when all its months are in.</p>' +
      '<div class="tablewrap"><table class="pr-stack tm-models"><caption class="sr-only">Bitcoin dial, one row per model, months added up</caption><thead><tr>' +
      '<th scope="col">Model</th><th scope="col" class="n">Months in</th><th scope="col" class="n">Gain, months added up</th><th scope="col" class="n">Holding bitcoin, same months</th>' +
      '<th scope="col" class="n">Percentile against its own answers in random order</th><th scope="col">Verdict</th></tr></thead><tbody>' +
      pl.models.map(function (m) {
        var f = m.complete;
        return '<tr><th scope="row">' + esc(m.name) + '</th><td class="n" data-label="Months in">' + esc(int(m.months_in)) + ' of ' + esc(int(m.months)) + '</td>' +
          '<td class="n" data-label="Gain, months added up">' + (f ? tmMoney(m.gain) : TM_NF) + '</td>' +
          '<td class="n" data-label="Holding bitcoin, same months">' + (f ? tmMoney(m.hold) : TM_NF) + '</td>' +
          '<td class="n" data-label="Percentile, own answers shuffled">' + (f ? tmPct(m.percentile) : TM_NF) + '</td>' +
          '<td class="pr-state" data-label="Verdict">' + tmVerdict(f ? m.verdict : 'not finished') + '</td></tr>';
      }).join('') + '</tbody></table></div>' +
      '<p class="meta">MEASURED. Pretend money. Gain is in dollars on ' + esc(money2(start)) + ' a month, added up over the months. The percentile is the share of reshufflings of the model\'s own answers that ended below it.' +
      (isNum(pl.pass_percentile) ? ' Line 1 is beating holding. Line 2 is a percentile above ' + esc(num(pl.pass_percentile, 0)) + '.' : '') + '</p>';
    if (pl.rule) {
      h += '<p data-testid="tm03-rule">MEASURED. A plain trend rule on the same months: ' + tmMoney(pl.rule.rule_gain) + ', against ' + tmMoney(pl.rule.model_gain) +
        ' for the best model, ' + esc(pl.rule.model) + '. <a href="' + esc(pl.rule.doc) + '" target="_blank" rel="noopener noreferrer">The plain rules</a></p>';
    }
    h += '<p class="meta">Verdict for the method: ' + tmVerdict(pl.method) + '</p>';
    return h + tmLinks(pl) + '</div>';
  }
  function tmBasket(pl, tm) {
    var h = '<div class="card pr-block tm-plan" data-testid="tm-plan-TM04"><h3 class="h3">' + esc(pl.label) + '</h3>' +
      '<p>Once a week each model picks which stocks to hold from a fixed list, always fully invested, with pretend money. It is measured against holding the whole list in equal shares and against baskets drawn at random from the same list.</p>';
    if (!pl.scored) return h + '<p class="meta" data-testid="tm04-scoring">' + tmVerdict('being scored') + ' Results show here when the scores are written.</p>' + tmLinks(pl) + '</div>';
    h += '<p class="meta">' + tmSessions(pl.sessions, 'runs') + ' Each model runs twice. A run gets figures only when it is finished.</p>' +
      '<div class="tablewrap"><table class="pr-stack tm-models"><caption class="sr-only">Stock basket, one row per model and run</caption><thead><tr>' +
      '<th scope="col">Model</th><th scope="col">Run</th><th scope="col" class="n">Gain</th><th scope="col" class="n">Equal shares of the list</th>' +
      '<th scope="col" class="n">Percentile among random baskets</th><th scope="col">Verdict</th></tr></thead><tbody>' +
      pl.rows.map(function (r) {
        var f = r.finished;
        return '<tr><th scope="row">' + esc(r.name) + '</th><td data-label="Run">' + esc(String(r.run).replace(/^r/, 'Run ')) + '</td>' +
          '<td class="n" data-label="Gain">' + (f ? tmMoney(r.gain) : TM_NF) + '</td>' +
          '<td class="n" data-label="Equal shares of the list">' + (f ? tmMoney(r.equal) : TM_NF) + '</td>' +
          '<td class="n" data-label="Percentile, random baskets">' + (f ? tmPct(r.percentile) : TM_NF) + '</td>' +
          '<td class="pr-state" data-label="Verdict">' + tmVerdict(r.verdict) + '</td></tr>';
      }).join('') + '</tbody></table></div>' +
      '<p class="meta">MEASURED. Pretend money. Gain is in dollars on the account. The percentile is the share of random baskets that ended below the run.' +
      (isNum(pl.pass_percentile) ? ' A run passes only if it beats equal shares and its percentile is above ' + esc(num(pl.pass_percentile, 0)) + '.' : '') + '</p>' +
      '<p class="meta">Verdict for the method, on run 1: ' + tmVerdict(pl.method) + '</p>';
    return h + tmLinks(pl) + '</div>';
  }
  function renderTimeMachine(d) {
    var body = $('timemachine-body');
    if (!body) return;
    var tm = d.timemachine;
    // A study on hold is said plainly at the top, with no weekly figure.
    var hold = d.tm_hold ? '<div class="card pr-block tm-plan tm-hold" data-testid="tm-hold-' + esc(d.tm_hold.id) + '"><div class="test-head"><h3 class="h3">' +
      esc(d.tm_hold.title) + '</h3><span class="badge badge-unknown"><span class="mark" aria-hidden="true">' + TONE_MARK.unknown + '</span>On hold</span></div>' +
      '<p>' + keepDates(esc(d.tm_hold.text)) + '</p></div>' : '';
    if (!tm || !tm.plans || !tm.plans.length) {
      body.innerHTML = hold + '<div class="empty"><h3>No replay has finished yet</h3><p>Results show here when the first sessions are scored.</p></div>';
      return;
    }
    var html = hold;
    tm.plans.forEach(function (pl) {
      if (pl.kind === 'dial') { html += tmDial(pl, tm); return; }
      if (pl.kind === 'basket') { html += tmBasket(pl, tm); return; }
      var done = pl.sessions.length;
      html += '<div class="card pr-block tm-plan" data-testid="tm-plan-' + esc(pl.id) + '"><h3 class="h3">' + esc(pl.label) + '</h3>' +
        '<p class="meta">' + esc(int(done)) + ' of ' + esc(int(pl.sessions_total)) + ' month-long sessions finished. Each starts with ' + esc(money2(tm.start_usd)) +
        ' of pretend money. A model counts only if, over all five months added up, it beats both holding bitcoin and four in five of its random twins. One month alone decides nothing.</p>' +
        '<div class="tablewrap"><table class="pr-stack tm-models"><caption class="sr-only">Models, months added up</caption><thead><tr>' +
        '<th scope="col">Model</th><th scope="col" class="n">Months counted</th><th scope="col" class="n">Gain</th><th scope="col" class="n">Just holding bitcoin</th>' +
        '<th scope="col" class="n">Random twins, 80th percentile</th><th scope="col">Verdict</th></tr></thead><tbody>' +
        pl.models.map(function (m) {
          return '<tr><th scope="row">' + esc(m.name) + '</th><td class="n" data-label="Months counted">' + esc(int(m.months_counted)) + ' of ' + esc(int(m.months)) + '</td>' +
            '<td class="n" data-label="Gain">' + tmMoney(m.gain) + '</td><td class="n" data-label="Just holding bitcoin">' + tmMoney(m.hold) + '</td>' +
            '<td class="n" data-label="Random twins, 80th percentile">' + tmMoney(m.twin_p80) + '</td><td class="pr-state" data-label="Verdict">' + tmVerdict(m.verdict) + '</td></tr>';
        }).join('') + '</tbody></table></div>' +
        '<p class="meta">A month is counted once its session, the bitcoin hold and all 20 twins are done, so this table lags the list below.</p>';
      if (pl.news_test) {
        var nt = pl.news_test;
        html += '<h4 class="tm-h4">Did the news help</h4><p class="meta">Only if all six models gain more with headlines than without, over the five months. Verdict so far: ' + tmVerdict(nt.verdict) + '</p>';
      }
      if (done) {
        html += '<h4 class="tm-h4">Sessions and why each trade was made</h4>' +
          pl.sessions.map(function (x) {
            var why = x.why.length ? '<div class="tablewrap"><table class="pr-stack tm-why"><caption class="sr-only">Buys of ' + esc(x.model) + ' in ' + esc(x.month) + '</caption><thead><tr>' +
              '<th scope="col">Woke (Mountain)</th><th scope="col">Coin</th><th scope="col">Looked at</th><th scope="col">Its reason</th>' +
              (pl.id === 'TM02' ? '<th scope="col">Headlines it named</th>' : '') + '<th scope="col">Ended</th><th scope="col" class="n">Result</th></tr></thead><tbody>' +
              x.why.map(function (w) {
                return '<tr><th scope="row">' + esc(mtFromUtc(w.wake)) + '</th><td data-label="Coin">' + esc(w.coin) + '</td><td class="tm-wrap" data-label="Looked at">' + esc(w.looked) + '</td>' +
                  '<td class="tm-wrap tm-reason" data-label="Its reason">' + esc(w.reason) + '</td>' +
                  (pl.id === 'TM02' ? '<td class="tm-wrap tm-reason" data-label="Headlines it named">' + (w.sources.length ? w.sources.map(esc).join('<br>') : 'None') + '</td>' : '') +
                  '<td class="tm-wrap" data-label="Ended">' + esc(capital(mtInText(w.ended))) + '</td>' +
                  '<td class="n" data-label="Result">' + (isNum(w.gain) ? esc(capital(w.result)) + ' ' + gainHtml(w.gain, w.gain_pct) : esc(capital(w.result))) + '</td></tr>';
              }).join('') + '</tbody></table></div>' : '<p class="meta">It bought nothing this month.</p>';
            return '<details class="tm-session"><summary><span class="tm-sum-name">' + esc(x.month) + ', ' + esc(x.model) + '</span>' +
              '<span class="tm-sum-fig">' + tmMoney(x.gain) + ' <span class="muted">against ' + (isNum(x.hold) ? esc(signedMoney(x.hold)) + ' holding bitcoin' : 'a hold not yet run') + '</span></span>' +
              '<span class="tm-sum-fig muted">' + esc(plural(x.buys, 'buy', 'buys')) + ', ' + esc(plural(x.wins, 'win', 'wins')) + ', ' + esc(plural(x.losses, 'loss', 'losses')) +
              (isNum(x.twins_beaten) ? ', beat ' + esc(int(x.twins_beaten)) + ' of 20 twins' : ', twins ' + esc(int(x.twins_done)) + ' of 20 run') + '</span></summary>' + why + '</details>';
          }).join('');
      }
      html += tmLinks(pl) + '</div>';
    });
    body.innerHTML = html;
  }

  function renderPractice() {
    var body = $('practice-body');
    if (!body) return;
    destroy('practice');
    var s = practice.summary;
    var status = s && PR_STATE[s.status] ? s.status : 'waiting_for_key';
    var st = PR_STATE[status];
    // A pause written in the queue page wins over the desk's own last word, which was written while its timer still ran.
    var paused = practice.pause && s && status !== 'waiting_for_key';
    if (paused) st = { label: 'Paused', cls: 'badge-mixed', mark: '~' };
    var waiting = !s || status === 'waiting_for_key';
    var html = '';

    // 1. one line of state
    html += '<div class="pr-status" data-testid="practice-status"><span class="badge ' + st.cls + '">' +
      (st.mark ? '<span class="mark" aria-hidden="true">' + st.mark + '</span>' : '') + esc(st.label) + '</span>' +
      (paused ? '<p>Paused ' + keepDates(esc(practice.pause.when)) + ' by the lead agent. The desk\u2019s timer is off, so nothing new is bought or sold. Last record ' + timeTag(s.made_utc) + '.</p>'
        : (s && s.status_text ? '<p>' + esc(s.status_text) + '</p>' : '')) + '</div>' +
      '<p class="meta pr-records">' + (s && s.last_check_utc ? 'Last check ' + timeTag(s.last_check_utc) + '. ' : '') +
      '<span id="practice-records">' + recordsLine(s) + '</span></p>';

    if (waiting) {
      html += '<div class="empty pr-empty" data-testid="practice-empty"><h3>Not started</h3>' +
        '<p>' + (s && s.status_text ? 'Nothing has been bought or sold yet.' : 'No practice trades yet. The desk starts when the practice key is in place.') +
        (traders().length ? ' ' + plural(traders().length, 'trader is', 'traders are') + ' set up and waiting' +
          (s && s.account && isNum(s.account.pretend_start_usd) ? ', with ' + money2(s.account.pretend_start_usd) + ' of pretend money between them' : '') + '.' : '') +
        ' Wins, losses and gains show here after the first trades.</p></div>';
    }

    // 2. overall
    var a = (s && s.account) || {}, t = (s && s.totals) || {};
    var closed = isNum(t.closed_trades) ? t.closed_trades : 0;
    if (!waiting) {
      html += '<div class="pr-kpis">' +
        kpi(practice.pause ? 'Pretend value at the last record' : 'Pretend value now', esc(money2(a.value_usd)), gainHtml(a.gain_usd, a.gain_pct) + ' since the start of ' + esc(money2(a.pretend_start_usd)), ' pr-kpi-main') +
        kpi('Wins', esc(int(t.wins)), closed ? '' : 'No closed trades yet') +
        kpi('Losses', esc(int(t.losses)), closed ? '' : 'No closed trades yet') +
        kpi('Win rate', isNum(t.win_rate) ? esc(pct(t.win_rate, 0)) : '<span class="pr-kpi-none">None yet</span>',
          closed ? esc('Won ' + int(t.wins) + ' of ' + plural(closed, 'closed trade', 'closed trades')) : 'Shown after the first closed trade') +
        kpi('Closed trades', esc(int(closed)), isNum(t.flat) && t.flat ? esc(plural(t.flat, 'came out even', 'came out even')) : (isNum(t.orders) ? esc(plural(t.orders, 'order sent', 'orders sent')) : '')) +
        '</div>';
    }
    if (!waiting) html += '<p class="meta pr-note">' + esc((s && s.notes && s.notes.win) ||
      'A trade is counted when a holding goes back to nothing. It is a win if more dollars came back than went in, fees included.') + '</p>';

    // 3. traders
    var list = traders().slice().sort(function (x, y) {
      var gx = isNum(x.gain_pct) ? x.gain_pct : -Infinity, gy = isNum(y.gain_pct) ? y.gain_pct : -Infinity;
      return gy - gx;
    });
    if (list.length) {
      html += '<div class="card pr-block"><h3 class="h3">Traders</h3>' +
        '<p class="meta">' + esc(plural(list.length, 'trader', 'traders')) + ', each with its own pretend budget. Best gain first. Open a trader to see what it holds, why, and its trades.</p>' +
        '<div class="tablewrap"><table class="pr-stack pr-traders"><caption class="sr-only">Traders, best gain first</caption><thead><tr>' +
        '<th scope="col">Trader</th><th scope="col" class="n">Gain</th><th scope="col" class="n">Just holding</th>' +
        '<th scope="col" class="n">Wins and losses</th><th scope="col" class="n">Holdings</th><th scope="col">State</th></tr></thead>' +
        list.map(traderRows).join('') + '</table></div></div>';
    }

    // 4. chart
    html += chartCard(s);

    // 5. all trades and closed trades
    if (!waiting || (s && (s.orders || []).length)) {
      html += '<div class="card pr-block" id="pr-orders-card">' + ordersCard(s) + '</div>';
      html += '<div class="card pr-block" id="pr-closed-card">' + closedCard(s) + '</div>';
    }

    // 6. problems and stopped symbols
    var probs = (s && s.problems) || [], syms = (s && s.symbols_stopped) || [];
    if (syms.length) {
      html += '<div class="pr-problems" data-testid="practice-symbols-stopped"><h3 class="h3">Symbols stopped</h3><p class="meta">No trader can buy these until you look.</p><ul>' +
        syms.map(function (x) { return '<li><strong>' + esc(x.symbol || 'Not recorded') + '</strong>' + esc(x.reason || 'No reason was recorded.') + '</li>'; }).join('') + '</ul></div>';
    }
    if (probs.length) {
      html += '<div class="pr-problems" data-testid="practice-problems"><h3 class="h3">Problems</h3><ul>' +
        probs.map(function (p) {
          return '<li><span class="meta">' + timeTag(p.utc) + (p.trader ? ', ' + esc(traderName(p.trader)) : '') + '</span>' + esc(p.text) + '</li>';
        }).join('') + '</ul></div>';
    }

    body.innerHTML = html;
    Object.keys(practice.open).forEach(function (id) { if (practice.open[id]) openTrader(id, false); });
    drawPracticeChart();
  }

  function traderState(t) {
    if (t.halted) return '<span class="badge badge-fail"><span class="mark" aria-hidden="true">\u00d7</span>Stopped</span>' +
      '<span class="pr-halt-reason">' + esc(t.halt_reason || 'No reason was recorded.') + '</span>';
    if (t.started === false) return '<span class="pr-muted">Waiting for its first check</span>';
    return practice.pause ? 'Paused' : 'Trading';
  }
  function traderRows(t) {
    var id = String(t.id), rid = 'pr-t-' + id.replace(/[^A-Za-z0-9_-]/g, '_');
    var started = t.started !== false;
    var wl = isNum(t.closed_trades) && t.closed_trades ? int(t.wins) + ' won, ' + int(t.losses) + ' lost' : 'None closed';
    var npos = (t.positions || []).length;
    return '<tbody class="pr-trader' + (t.halted ? ' pr-trader-halted' : '') + '" data-trader="' + esc(id) + '"><tr>' +
      '<th scope="row" data-label="Trader"><button type="button" class="pr-open" id="' + esc(rid) + '-btn" aria-expanded="false" aria-controls="' + esc(rid) + '-detail" data-trader-toggle="' + esc(id) + '">' +
        '<span class="pr-chev" aria-hidden="true"></span><span class="pr-tname">' + esc(t.name || id) + '</span></button>' +
        '<span class="pr-kind">' + esc(kindText(t)) + '</span></th>' +
      '<td class="n" data-label="Gain">' + (started ? gainHtml(t.gain_usd, t.gain_pct) : '<span class="pr-muted">None yet</span>') + '</td>' +
      '<td class="n" data-label="Just holding' + (t.benchmark ? ' ' + esc(t.benchmark) : '') + '">' +
        (isNum(t.hold_value_usd) || isNum(t.hold_gain_pct)
          ? gainHtml(isNum(t.hold_value_usd) && isNum(t.start_usd) ? t.hold_value_usd - t.start_usd : null, t.hold_gain_pct)
          : '<span class="pr-muted">None yet</span>') +
        (t.benchmark ? '<span class="pr-sub">' + esc(t.benchmark) + '</span>' : '') + '</td>' +
      '<td class="n" data-label="Wins and losses">' + esc(wl) + '</td>' +
      '<td class="n" data-label="Holdings">' + esc(npos ? plural(npos, 'open', 'open') : 'None') + '</td>' +
      '<td data-label="State" class="pr-state">' + traderState(t) + '</td>' +
      '</tr></tbody>';
  }

  function openTrader(id, toggle) {
    var tb = null, all = document.querySelectorAll('#practice-body tbody.pr-trader');
    for (var i = 0; i < all.length; i++) if (all[i].getAttribute('data-trader') === id) tb = all[i];
    if (!tb) return;
    var btn = tb.querySelector('[data-trader-toggle]');
    var existing = tb.querySelector('tr.pr-detail');
    var willOpen = toggle === false ? true : !existing;
    if (existing) existing.parentNode.removeChild(existing);
    practice.open[id] = willOpen;
    btn.setAttribute('aria-expanded', willOpen ? 'true' : 'false');
    tb.classList.toggle('is-open', willOpen);
    if (!willOpen) return;
    var t = traderById(id);
    var tr = document.createElement('tr');
    tr.className = 'pr-detail';
    tr.id = btn.getAttribute('aria-controls');
    tr.innerHTML = '<td colspan="6">' + traderDetail(t) + '</td>';
    tb.appendChild(tr);
  }

  function exitText(t, p) {
    var x = p.exit;
    if (!x) return t.kind === 'rule' ? 'Sold when the rule says so' : 'None set';
    var parts = [];
    if (isNum(x.stop)) parts.push('sell if it falls to ' + priceAny(x.stop));
    if (isNum(x.target)) parts.push('sell if it reaches ' + priceAny(x.target));
    if (x.by_utc) parts.push('sell by ' + localText(timeOf(x.by_utc) || 0));
    return parts.length ? capital(parts.join(', ')) : 'None set';
  }

  function traderDetail(t) {
    var s = practice.summary || {};
    var h = '<div class="pr-detail-in">';
    var facts = [];
    facts.push('<div><dt>Kind</dt><dd>' + esc(kindText(t)) + '</dd></div>');
    facts.push('<div><dt>Pretend budget</dt><dd>' + esc(money2(t.start_usd)) + '</dd></div>');
    facts.push('<div><dt>Value now</dt><dd>' + esc(money2(t.value_usd)) + '</dd></div>');
    facts.push('<div><dt>Cash</dt><dd>' + esc(money2(t.cash_usd)) + '</dd></div>');
    if (isNum(t.target_weight)) facts.push('<div><dt>Share the rule asks to hold</dt><dd>' + esc(pct(t.target_weight, 0)) + '</dd></div>');
    facts.push('<div><dt>Closed trades made</dt><dd>' + gainHtml(t.realised_usd, null) + '</dd></div>');
    facts.push('<div><dt>Fees added</dt><dd>' + esc(money2(t.fees_added_usd)) + '</dd></div>');
    facts.push('<div><dt>Label</dt><dd>' + esc(t.label ? capital(t.label) : 'Not passed') + '</dd></div>');
    h += '<p class="meta">No trader on this desk has a counted pass. Each one runs to be watched.' +
      (t.method ? ' How it works: ' + methodLink(t.method) + '.' : '') + '</p>';
    if (t.halted) h += '<div class="pr-halt" role="note"><strong><span aria-hidden="true">\u00d7 </span>Stopped.</strong> ' + esc(t.halt_reason || 'No reason was recorded.') + '</div>';
    if (t.started === false) h += '<div class="pr-wait"><strong>Waiting for its first check.</strong> It has not made its first decision yet, so there are no holdings or gains to show.</div>';
    h += '<dl class="pr-facts">' + facts.join('') + '</dl>';

    // holdings
    var pos = t.positions || [];
    h += '<h4 class="pr-h4">Holdings now</h4>';
    if (!pos.length) h += '<p class="pr-muted">Nothing held. All ' + esc(money2(t.cash_usd)) + ' is cash.</p>';
    else h += '<div class="tablewrap"><table class="pr-stack pr-pos"><caption class="sr-only">Holdings of ' + esc(t.name || t.id) + '</caption><thead><tr>' +
      '<th scope="col">Symbol</th><th scope="col" class="n">Amount</th><th scope="col" class="n">Price now</th><th scope="col" class="n">Value</th>' +
      '<th scope="col" class="n">Paid</th><th scope="col" class="n">Gain</th><th scope="col">Bought</th><th scope="col">Exit in force</th></tr></thead><tbody>' +
      pos.map(function (p) {
        return '<tr><th scope="row" data-label="Symbol">' + esc(p.symbol) + '</th><td class="n" data-label="Amount">' + esc(qtyFmt(p.qty)) + '</td>' +
          '<td class="n" data-label="Price now">' + esc(priceAny(p.price)) + '</td><td class="n" data-label="Value">' + esc(money2(p.value_usd)) + '</td>' +
          '<td class="n" data-label="Paid">' + esc(money2(p.cost_usd)) + '</td><td class="n" data-label="Gain">' + gainHtml(p.gain_usd, isNum(p.gain_usd) && p.cost_usd > 0 ? p.gain_usd / p.cost_usd : null) + '</td>' +
          '<td data-label="Bought">' + timeTag(p.opened_utc) + '</td><td data-label="Exit in force" class="pr-wrap">' + esc(exitText(t, p)) + '</td></tr>';
      }).join('') + '</tbody></table></div>';

    // last pick
    if (t.kind === 'ai' || t.last_pick) {
      h += '<h4 class="pr-h4">Last pick</h4>';
      var lp = t.last_pick;
      if (!lp) h += '<p class="pr-muted">No pick yet.</p>';
      else {
        var src = (lp.sources || []).map(function (u) {
          var ok = safeUrl(u);
          return '<li>' + (ok ? '<a href="' + esc(ok) + '" target="_blank" rel="noopener">' + esc(u) + '</a>' : esc(u)) + '</li>';
        }).join('');
        h += '<div class="pr-pick"><p class="meta">Made ' + timeTag(lp.made_utc) + (lp.pick_id ? ', pick ' + esc(lp.pick_id) : '') + '</p>' +
          '<p class="pr-thesis">' + esc(lp.thesis || 'No reason was written.') + '</p>' +
          (src ? '<p class="meta">Sources it gave</p><ul class="pr-sources">' + src + '</ul>' : '<p class="meta">No sources given.</p>') + '</div>';
      }
    }

    // its orders and closed trades
    var orders = (s.orders || []).filter(function (o) { return o.trader === t.id; });
    h += '<h4 class="pr-h4">Its orders</h4>' + (orders.length ? ordersTable(orders, false) : '<p class="pr-muted">No orders yet.</p>');
    if (isNum(t.orders_count) && t.orders_count > orders.length) h += '<p class="meta">Showing the newest ' + int(orders.length) + ' of ' + int(t.orders_count) + ' orders. The records file keeps the newest 300 for the whole desk.</p>';
    var cl = (s.closed || []).filter(function (c) { return c.trader === t.id; });
    h += '<h4 class="pr-h4">Its closed trades</h4>' + (cl.length ? closedTable(cl, false) : '<p class="pr-muted">No closed trades yet.</p>');
    h += '<p><button type="button" class="btn" data-trader-close="' + esc(t.id) + '">Close ' + esc(t.name || t.id) + '</button></p>';
    return h + '</div>';
  }

  function methodLink(m) {
    var path = String(m).replace(/^\/+/, '');
    if (!/^[A-Za-z0-9_./-]+$/.test(path) || !practice.ghBase) return esc(m);
    if (path.indexOf('practice/') !== 0 && path.indexOf('docs/') !== 0) path = 'practice/' + path;
    return '<a href="' + esc(practice.ghBase + path) + '" target="_blank" rel="noopener">' + esc(path.split('/').pop()) + '</a>';
  }

  var STATUS_PLAIN = { filled: 'Filled', open: 'Open', 'part filled': 'Part filled' };
  function statusCell(st) {
    var k = String(st || '');
    return STATUS_PLAIN[k] ? esc(STATUS_PLAIN[k]) : '<strong>' + esc(capital(k || 'not recorded')) + '</strong>';
  }

  function ordersTable(orders, showTrader) {
    return '<div class="tablewrap"><table class="pr-stack pr-ord"><caption class="sr-only">Orders, newest first</caption><thead><tr>' +
      '<th scope="col">Sent</th>' + (showTrader ? '<th scope="col">Trader</th>' : '') +
      '<th scope="col">Order</th><th scope="col" class="n">Dollars</th><th scope="col" class="n">Fill price</th><th scope="col" class="n">Price when sent</th>' +
      '<th scope="col" class="n">Gap (bps)</th><th scope="col" class="n">Fee added</th><th scope="col">Status</th></tr></thead><tbody>' +
      orders.map(function (o) {
        var size = isNum(o.qty) ? qtyFmt(o.qty) : (isNum(o.asked_qty) ? 'asked ' + qtyFmt(o.asked_qty) : '');
        var dollars = isNum(o.notional_usd) ? money2(o.notional_usd) : (isNum(o.asked_usd) ? 'asked ' + money2(o.asked_usd) : 'Not recorded');
        return '<tr class="pr-ord-main"><td data-label="Sent">' + timeTag(o.utc) + '</td>' +
          (showTrader ? '<td data-label="Trader">' + esc(traderName(o.trader)) + '</td>' : '') +
          '<td data-label="Order"><span class="act">' + esc(capital(o.side)) + '</span> ' + esc(o.symbol || '') + (size ? '<span class="pr-sub">' + esc(size) + '</span>' : '') + '</td>' +
          '<td class="n" data-label="Dollars">' + esc(dollars) + '</td>' +
          '<td class="n" data-label="Fill price">' + esc(priceAny(o.fill_price)) + '</td>' +
          '<td class="n" data-label="Price when sent">' + esc(priceAny(o.assumed_price)) + '</td>' +
          '<td class="n" data-label="Gap (bps)">' + esc(isNum(o.gap_bps) ? num(o.gap_bps, 1) : 'Not recorded') + '</td>' +
          '<td class="n" data-label="Fee added">' + esc(isNum(o.fee_added_usd) ? money2(o.fee_added_usd) : 'Not recorded') + '</td>' +
          '<td data-label="Status">' + statusCell(o.status) + '</td></tr>' +
          '<tr class="pr-ord-reason"><td colspan="' + (showTrader ? 9 : 8) + '" data-label="Reason" class="pr-wrap"><span class="pr-reason-label">Reason: </span>' + esc(o.reason || 'No reason recorded') + '</td></tr>';
      }).join('') + '</tbody></table></div>';
  }

  function closedTable(cl, showTrader) {
    var MARK = { win: '\u2713', loss: '\u00d7', flat: '=' };
    var WORD = { win: 'Win', loss: 'Loss', flat: 'Even' };
    return '<div class="tablewrap"><table class="pr-stack pr-cl"><caption class="sr-only">Closed trades, newest first</caption><thead><tr>' +
      '<th scope="col">Closed</th>' + (showTrader ? '<th scope="col">Trader</th>' : '') +
      '<th scope="col">Symbol</th><th scope="col">Bought</th><th scope="col" class="n">Paid</th><th scope="col" class="n">Gain</th><th scope="col">Result</th></tr></thead><tbody>' +
      cl.map(function (c) {
        var r = c.result in WORD ? c.result : null;
        return '<tr><td data-label="Closed">' + timeTag(c.closed_utc) + '</td>' +
          (showTrader ? '<td data-label="Trader">' + esc(traderName(c.trader)) + '</td>' : '') +
          '<td data-label="Symbol">' + esc(c.symbol || 'Not recorded') + '</td><td data-label="Bought">' + timeTag(c.opened_utc) + '</td>' +
          '<td class="n" data-label="Paid">' + esc(money2(c.cost_usd)) + '</td><td class="n" data-label="Gain">' + gainHtml(c.gain_usd, c.gain_pct) + '</td>' +
          '<td data-label="Result"><span class="pr-result pr-result-' + esc(r || 'none') + '"><span aria-hidden="true">' + (r ? MARK[r] : '?') + ' </span>' + esc(r ? WORD[r] : capital(c.result)) + '</span></td></tr>';
      }).join('') + '</tbody></table></div>';
  }

  function traderSelect(id, label, value, includeAccount) {
    var opts = '<option value="">' + esc(includeAccount ? 'No trader highlighted' : 'All traders') + '</option>' +
      traders().map(function (t) { return '<option value="' + esc(t.id) + '"' + (t.id === value ? ' selected' : '') + '>' + esc(t.name || t.id) + '</option>'; }).join('');
    return '<label class="field pr-field"><span class="field-label">' + esc(label) + '</span><select id="' + id + '">' + opts + '</select></label>';
  }

  function ordersCard(s) {
    var all = (s && s.orders) || [];
    var list = practice.ordersTrader ? all.filter(function (o) { return o.trader === practice.ordersTrader; }) : all;
    var shown = list.slice(0, practice.ordersShown);
    var n = s && s.notes ? s.notes : {};
    var h = '<h3 class="h3">All trades</h3><p class="meta">Every order sent, newest first, with the reason given for it.</p>';
    if (all.length && traders().length > 1) h += '<div class="controls pr-controls">' + traderSelect('pr-orders-trader', 'Trader', practice.ordersTrader, false) + '</div>';
    if (!list.length) h += '<p class="pr-muted">No orders yet.</p>';
    else {
      h += ordersTable(shown, true);
      h += '<div class="pager"><p class="pager-info">Showing ' + int(shown.length) + ' of ' + int(list.length) + (all.length >= 300 ? '. The records file keeps the newest 300.' : '') + '</p>' +
        (shown.length < list.length ? '<div class="pager-btns"><button type="button" class="btn" data-more="orders">Show ' + int(Math.min(PR_PAGE, list.length - shown.length)) + ' more</button></div>' : '') + '</div>';
    }
    h += '<div class="pr-notes"><p class="meta">' + esc(n.gap || 'Gap is how far the fill was from the newest price the program had read when it sent the order, in basis points. Plus means the fill was worse for the account.') + '</p>' +
      '<p class="meta">A basis point is one hundredth of a percent.</p>' +
      (n.fee ? '<p class="meta">' + esc(n.fee) + '</p>' : '') + (n.not_added ? '<p class="meta">' + esc(n.not_added) + '</p>' : '') + '</div>';
    return h;
  }

  function closedCard(s) {
    var all = (s && s.closed) || [];
    var shown = all.slice(0, practice.closedShown);
    var h = '<h3 class="h3">Closed trades</h3><p class="meta">Each time a holding went back to nothing, newest first.</p>';
    if (!all.length) return h + '<p class="pr-muted">No closed trades yet.</p>';
    h += closedTable(shown, true);
    h += '<div class="pager"><p class="pager-info">Showing ' + int(shown.length) + ' of ' + int(all.length) + '</p>' +
      (shown.length < all.length ? '<div class="pager-btns"><button type="button" class="btn" data-more="closed">Show ' + int(Math.min(PR_PAGE, all.length - shown.length)) + ' more</button></div>' : '') + '</div>';
    return h;
  }

  // ---------- practice chart ----------
  function chartPoints(s) {
    return ((s && s.points) || []).filter(function (p) { return p && timeOf(p.utc) !== null; })
      .sort(function (x, y) { return timeOf(x.utc) - timeOf(y.utc); });
  }
  function chartCard(s) {
    var pts = chartPoints(s);
    var h = '<div class="card chart-card pr-block"><h3 class="h3">Gain over time</h3>' +
      '<p class="testlabel">Pretend money in a practice account.</p>';
    if (pts.length < 2) return h + '<p class="pr-chart-wait">The chart appears after the second check is recorded.</p></div>';
    if (typeof Chart === 'undefined') return h + '<p class="pr-chart-wait">The chart file did not load, so the chart cannot be drawn.</p></div>';
    var hl = practice.hl && traderById(practice.hl) ? practice.hl : '';
    h += '<p class="meta">Gain since the start, in percent, so traders with different budgets can be compared.</p>' +
      '<div class="controls pr-controls">' + traderSelect('pr-chart-trader', 'Highlight a trader', hl, true) + '</div>' +
      '<div class="legend" aria-hidden="true"><span class="key key-rule pr-key-acct">Whole account</span><span class="key key-hold">Just holding (dashed)</span>' +
      '<span class="key pr-key-trader">Each trader</span>' + (hl ? '<span class="key pr-key-hl">' + esc(traderName(hl)) + '</span>' : '') + '</div>' +
      '<div class="chartbox pr-chartbox"><canvas id="chart-practice" role="img" aria-label="' +
      esc('Gain since the start for the whole account, for just holding, and for each trader, from ' + localText(timeOf(pts[0].utc)) + ' to ' + localText(timeOf(pts[pts.length - 1].utc)) + (hl ? '. Highlighted: ' + traderName(hl) : '')) +
      '"></canvas></div></div>';
    return h;
  }

  function drawPracticeChart() {
    destroy('practice');
    var cv = $('chart-practice'), s = practice.summary;
    if (!cv || !s || typeof Chart === 'undefined') return;
    var pts = chartPoints(s);
    if (pts.length < 2) return;
    var a = s.account || {}, list = traders();
    var start = isNum(a.pretend_start_usd) && a.pretend_start_usd > 0 ? a.pretend_start_usd : null;
    var per = {};
    list.forEach(function (t) { per[t.id] = isNum(t.start_usd) && t.start_usd > 0 ? t.start_usd : null; });
    var ids = [];
    pts.forEach(function (p) { Object.keys(p.traders || {}).forEach(function (k) { if (ids.indexOf(k) < 0) ids.push(k); }); });
    function series(get, base) {
      return pts.map(function (p) { var v = get(p); return { x: timeOf(p.utc), y: isNum(v) && base ? v / base - 1 : null }; });
    }
    var hl = practice.hl, grid = cssVar('--hold'), hlc = cssVar('--pick');
    var sets = ids.filter(function (k) { return k !== hl; }).map(function (k) {
      return { label: traderName(k), data: series(function (p) { return (p.traders || {})[k]; }, per[k] || (start && list.length ? start / list.length : null)),
        borderColor: cssVar('--trader-line'), borderWidth: 1, pointRadius: 0, tension: 0, spanGaps: true, prKind: 'trader' };
    });
    sets.push({ label: 'Just holding', data: series(function (p) { return p.hold_value_usd; }, start), borderColor: grid, borderWidth: 1.5, borderDash: [6, 4], pointRadius: 0, tension: 0, spanGaps: true, prKind: 'main' });
    sets.push({ label: 'Whole account', data: series(function (p) { return p.value_usd; }, start), borderColor: cssVar('--rule'), borderWidth: 2.5, pointRadius: 0, tension: 0, spanGaps: true, prKind: 'main' });
    if (hl && ids.indexOf(hl) >= 0) sets.push({ label: traderName(hl), data: series(function (p) { return (p.traders || {})[hl]; }, per[hl]), borderColor: hlc, borderWidth: 2.5, pointRadius: 0, tension: 0, spanGaps: true, prKind: 'main' });
    var o = baseOptions();
    var x0 = timeOf(pts[0].utc), x1 = timeOf(pts[pts.length - 1].utc), span = x1 - x0;
    o.scales.x.type = 'linear'; o.scales.x.min = x0; o.scales.x.max = x1;
    o.scales.x.ticks.maxRotation = 0; o.scales.x.ticks.autoSkip = true;
    o.scales.x.ticks.maxTicksLimit = cv.parentNode.clientWidth < 500 ? 4 : 7;
    o.scales.x.ticks.callback = function (v) {
      var d = new Date(Number(v));
      try {
        return span < 2 * 864e5 ? d.toLocaleString('en-US', { timeZone: OWNER_ZONE, hour: 'numeric', minute: '2-digit' }) : d.toLocaleString('en-US', { timeZone: OWNER_ZONE, month: 'short', day: 'numeric' });
      } catch (e) { return d.toISOString().slice(5, 16); }
    };
    o.scales.y.ticks.callback = function (v) { return pct(Number(v), Math.abs(Number(v)) < 0.1 ? 1 : 0); };
    o.plugins.tooltip.filter = function (it) { return it.dataset.prKind === 'main'; };
    o.plugins.tooltip.callbacks = {
      title: function (items) { return items.length ? localText(items[0].parsed.x) : ''; },
      label: function (c) { return c.dataset.label + ': ' + signedPct(c.parsed.y); }
    };
    state.charts.practice = new Chart(cv, { type: 'line', data: { datasets: sets }, options: o });
  }

  // ---------- practice events ----------
  function initPracticeEvents() {
    var body = $('practice-body');
    body.addEventListener('click', function (e) {
      var b = e.target.closest('[data-trader-toggle]');
      if (b) { openTrader(b.getAttribute('data-trader-toggle')); return; }
      var c = e.target.closest('[data-trader-close]');
      if (c) {
        var id = c.getAttribute('data-trader-close');
        openTrader(id, true);
        var all = body.querySelectorAll('[data-trader-toggle]');
        for (var i = 0; i < all.length; i++) if (all[i].getAttribute('data-trader-toggle') === id) all[i].focus();
        return;
      }
      var m = e.target.closest('[data-more]');
      if (m) {
        var which = m.getAttribute('data-more');
        if (which === 'orders') { practice.ordersShown += PR_PAGE; $('pr-orders-card').innerHTML = ordersCard(practice.summary); }
        else { practice.closedShown += PR_PAGE; $('pr-closed-card').innerHTML = closedCard(practice.summary); }
        var nb = body.querySelector('[data-more="' + which + '"]');
        if (nb) nb.focus();
      }
    });
    body.addEventListener('change', function (e) {
      if (e.target.id === 'pr-orders-trader') {
        practice.ordersTrader = e.target.value; practice.ordersShown = PR_PAGE;
        $('pr-orders-card').innerHTML = ordersCard(practice.summary);
        $('pr-orders-trader').focus();
      } else if (e.target.id === 'pr-chart-trader') {
        practice.hl = e.target.value;
        var card = $('chart-practice') ? $('chart-practice').closest('.chart-card') : null;
        if (card) {
          var tmp = document.createElement('div'); tmp.innerHTML = chartCard(practice.summary);
          card.parentNode.replaceChild(tmp.firstChild, card);
          drawPracticeChart();
          $('pr-chart-trader').focus();
        }
      }
    });
  }

  function checkLivePractice(url) {
    if (!url || typeof fetch !== 'function') return;
    practice.check = 'checking';
    setRecordsLine();
    var done = false;
    var timer = setTimeout(function () { if (!done) { done = true; practice.check = 'failed'; setRecordsLine(); } }, 15000);
    function fail() { if (done) return; done = true; clearTimeout(timer); practice.check = 'failed'; setRecordsLine(); }
    try {
      fetch(url, { cache: 'no-store' })
        .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
        .then(function (live) {
          if (done) return;
          if (!live || typeof live !== 'object' || Array.isArray(live)) throw new Error('bad');
          done = true; clearTimeout(timer);
          var lt = timeOf(live.made_utc), bt = practice.summary ? timeOf(practice.summary.made_utc) : null;
          if (lt !== null && (bt === null || lt > bt)) {
            practice.summary = live; practice.source = 'live'; practice.check = 'done';
            try { renderPractice(); } catch (e) { /* keep what is on screen */ }
            if (state.tradeFilter === 'practice') renderTrades();
          } else { practice.check = 'same'; setRecordsLine(); }
        })
        .catch(fail);
    } catch (e) { fail(); }
  }

  function initPractice(d) {
    practice.summary = d.practice && typeof d.practice === 'object' ? d.practice : null;
    practice.source = 'baked'; practice.check = 'none';
    practice.pause = d.practice_pause && d.practice_pause.when ? d.practice_pause : null;
    practice.ghBase = d.status_link ? String(d.status_link).replace(/docs\/STATUS\.md$/, '') : '';
    try { initPracticeEvents(); } catch (e) { /* the section still shows */ }
    try { renderPractice(); } catch (e) {
      $('practice-body').innerHTML = '<div class="empty"><h3>The practice records could not be shown</h3><p>The records in data.json are not in the expected shape.</p></div>';
    }
    try { checkLivePractice(d.practice_live_url); } catch (e) { /* stay on the saved copy */ }
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
    // The tab row can wrap to two lines on wide screens, so a jump to a section clears the real height of the bar.
    function pad() { document.documentElement.style.scrollPaddingTop = Math.ceil(document.querySelector('.topbar').getBoundingClientRect().height + 16) + 'px'; }
    window.addEventListener('resize', function () { pad(); update(); });
    pad();
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
        try { renderNewest(d); } catch (e) { $('newest-list').innerHTML = '<p class="meta">The newest results could not be shown.</p>'; }
        renderScoreboard(d);
        initPractice(d);
        try { renderDesk(d); } catch (e) { $('desk-body').innerHTML = '<p class="meta">The live desk could not be shown.</p>'; }
        try { renderBelieved(d); } catch (e) { $('believed-body').innerHTML = '<p class="meta">The findings could not be shown.</p>'; }
        renderStatus(d);
        try { renderTimeMachine(d); } catch (e) { $('timemachine-body').innerHTML = '<div class="empty"><h3>The replay results could not be shown</h3><p>The results in data.json are not in the expected shape.</p></div>'; }
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

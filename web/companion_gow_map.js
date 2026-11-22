
(function () {
  'use strict';

  var APPID = '2322010';

  var tr = window.GowI18n.t;
  document.documentElement.classList.add('gow-fs');

  
  
  function svg(cls, body, filled) {
    return '<svg class="gow-svg-glyph ' + cls + '" viewBox="0 0 24 24" aria-hidden="true" ' +
      (filled ? 'fill="currentColor" stroke="none"' :
        'fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"') +
      '>' + body + '</svg>';
  }

  var GOW_SVG = {
    raven: svg('gow-svg-raven',
      '<path d="M2 9.2c3.2.2 5.6 1.4 7.3 3.4L12 15.2l2.7-2.6c1.7-2 4.1-3.2 7.3-3.4-2.4 1.6-3.8 3.7-4.4 6-1.7.1-3.2.7-4.5 1.7L12 19.4l-1.1-2.5c-1.3-1-2.8-1.6-4.5-1.7-.6-2.3-2-4.4-4.4-6z"/>' +
      '<path d="M12 15.2l-1.3-3.6 1.3-1.8 1.6.9-1.2 1.1z"/>', true),
    norn: svg('gow-svg-norn',
      '<path d="M4 10.5h16V19H4z"/><path d="M4 10.5C4 7.4 7.6 5 12 5s8 2.4 8 5.5"/>' +
      '<path d="M8 12.8v4M8 14.2l1.3-1.2M12 12.8v4M11 13.6l2 2M16 12.8v4M16 14.8l-1.3 1.2"/>'),
    legendary: svg('gow-svg-legendary',
      '<path d="M3.5 10.5h17V19h-17z"/><path d="M3.5 10.5C4 7 7.6 5 12 5s8 2 8.5 5.5"/>' +
      '<path d="M8.5 6v13M15.5 6v13"/><path d="M10.8 12.5h2.4v3h-2.4z"/>'),
    lore: svg('gow-svg-lore',
      '<path d="M7 20.5V7.6L12 3.5l5 4.1v12.9"/><path d="M5 20.5h14"/>' +
      '<path d="M12 8.5v8M12 10.5l-2.2 1.8M12 10.5l2.2 1.8M12 14.2l-2 1.6"/>'),
    artifact: svg('gow-svg-artifact',
      '<path d="M5 5c2.3 1 4.6 1.5 7 1.5S16.7 6 19 5c.6 6.2-1.6 12.2-7 14.5C6.6 17.2 4.4 11.2 5 5z"/>' +
      '<path d="M8 10.5l3 .8M16 10.5l-3 .8M10 15.2h4"/>'),
    berserker: svg('gow-svg-berserker',
      '<path d="M6.5 20.5V9a5.5 5.5 0 0 1 11 0v11.5"/><path d="M4.5 20.5h15"/>' +
      '<path d="M12.6 6.5l-1.8 3.4 2.6 1.6-2.2 4.2"/>'),
    hel_tear: svg('gow-svg-hel-tear',
      '<path d="M12 2.5l3 6-1.4 3.4 2 3.1L12 21.5 8.4 15l2-3.1L9 8.5z"/><path d="M12 7.5v9"/>'),
    rift: svg('gow-svg-rift',
      '<path d="M12 3c4.4 2 6.5 5.2 6.5 9S16.4 19 12 21c-4.4-2-6.5-5.2-6.5-9S7.6 5 12 3z"/>' +
      '<path d="M12 7.5c1.4 1.4 2 2.9 2 4.5s-.6 3.1-2 4.5c-1.4-1.4-2-2.9-2-4.5s.6-3.1 2-4.5z"/>'),
    favour: svg('gow-svg-favour',
      '<path d="M12 2.8l9.2 9.2-9.2 9.2L2.8 12z"/><path d="M12 7.8v5.4"/><path d="M12 16.1v.1"/>'),
    gateway: svg('gow-svg-gateway',
      '<path d="M5 20.5V10a7 7 0 0 1 14 0v10.5"/><path d="M8.6 20.5V11a3.4 3.4 0 0 1 6.8 0v9.5"/>' +
      '<path d="M3.5 20.5h17"/>'),
    boss: svg('gow-svg-boss',
      '<path d="M6.5 11.5c0-3.4 2.5-6 5.5-6s5.5 2.6 5.5 6v3.7L15.8 19H8.2l-1.7-3.8z"/>' +
      '<path d="M6.8 9.3L3.5 4.6l.8 6.1M17.2 9.3l3.3-4.7-.8 6.1M9 13h6M12 13v5"/>'),
    armor: svg('gow-svg-armor',
      '<path d="M8 4l4 2 4-2 3.5 3-1.5 4v8l-6 2.2L6 19v-8L4.5 7z"/><path d="M12 6v15"/>'),
    relic: svg('gow-svg-relic',
      '<path d="M12 3v3.5"/><circle cx="12" cy="13" r="6.2"/><path d="M12 9.6l2.6 3.4-2.6 3.4-2.6-3.4z"/>'),
    treasure: svg('gow-svg-treasure',
      '<path d="M4 6.2l5-2 6 2 5-2v13.6l-5 2-6-2-5 2z"/><path d="M9 4.2v13.6M15 6.2v13.6"/>' +
      '<path d="M10.8 10.2l2.4 2.4M13.2 10.2l-2.4 2.4"/>'),
    poem: svg('gow-svg-poem',
      '<path d="M3 6.2c3-1 6-.8 9 1 3-1.8 6-2 9-1v13c-3-1-6-.8-9 1-3-1.8-6-2-9-1z"/><path d="M12 7.2v13"/>'),
    jewel: svg('gow-svg-jewel',
      '<path d="M7 4.5h10l4 4.8-9 11.2-9-11.2z"/><path d="M3 9.3h18M9.5 4.5 8 9.3l4 11.2 4-11.2-1.5-4.8"/>'),
    shard: svg('gow-svg-shard',
      '<path d="M9 3l7.2 4-2.3 14L8 15.8z"/><path d="M9 3l5 9.2"/>'),
    skull: svg('gow-svg-skull',
      '<path d="M12 3.5a7 7 0 0 0-7 7c0 2.4 1.2 4.1 3 5.1v3.9h8v-3.9c1.8-1 3-2.7 3-5.1a7 7 0 0 0-7-7z"/>' +
      '<circle cx="9.4" cy="10.8" r="1.3"/><circle cx="14.6" cy="10.8" r="1.3"/><path d="M10.6 19.5v-2M13.4 19.5v-2"/>'),
    troll: svg('gow-svg-troll',
      '<path d="M6 20.5l-1-8.2C5 7.7 8.1 4 12 4s7 3.7 7 8.3l-1 8.2z"/><path d="M8.6 11.2h2.6M12.8 11.2h2.6M10 16h4"/>'),
    bloom: svg('gow-svg-bloom',
      '<circle cx="12" cy="12" r="2.2"/><path d="M12 9.8V4M12 14.2V20M9.8 12H4M14.2 12H20' +
      'M10.4 10.4 6.4 6.4M13.6 13.6l4 4M13.6 10.4l4-4M10.4 13.6l-4 4"/>'),
    shield: svg('gow-svg-shield',
      '<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="2.4"/><path d="M12 3.5v6.1M12 14.4v6.1M3.5 12h6.1M14.4 12h6.1"/>'),
    ingredient: svg('gow-svg-ingredient',
      '<path d="M5.5 10.5h13l-1.4 8.5H6.9z"/><path d="M4 10.5h16M9.5 7.6c0-1.4.9-1.9.9-3.3M14.2 7.6c0-1.4.9-1.9.9-3.3"/>'),
    camp: svg('gow-svg-camp',
      '<path d="M3 20.2L12 5l9 15.2z"/><path d="M9 20.2l3-5.2 3 5.2"/>'),
    shop: svg('gow-svg-shop',
      '<path d="M4 8h12.5c0 2.4 1.6 3.8 3.5 4v1.2h-4.7l-1 3h1.9v2.3H7.8v-2.3h1.9l-1-3C5.9 13.2 4 10.9 4 8z"/>'),
    door: svg('gow-svg-door',
      '<path d="M6.5 20.5V5.5h11v15"/><path d="M4.5 20.5h15M14.5 13v.2"/>'),
    loot: svg('gow-svg-loot',
      '<path d="M5 11.5h14v7H5z"/><path d="M5 11.5c0-2.5 3.1-4 7-4s7 1.5 7 4"/><path d="M11 13.5h2v2h-2z"/>'),
    rune: svg('gow-svg-rune',
      '<path d="M12 21V3M12 10.5 6.8 5.3M12 10.5l5.2-5.2"/>'),
    kratos: '<svg class="gow-svg-glyph gow-svg-kratos" viewBox="0 0 24 24" aria-hidden="true">' +
      '<path d="M12 1.8l7.4 19.4L12 17l-7.4 4.2z" fill="#f0cf7a" stroke="#c94a38" stroke-width="1.6" stroke-linejoin="round"/>' +
      '<path d="M12 6.4V16" stroke="#7a1f14" stroke-width="1.2" stroke-linecap="round"/></svg>',
    
    close: svg('gow-svg-ui', '<path d="M6 6l12 12M18 6L6 18"/>'),
    chevron_left: svg('gow-svg-ui', '<path d="M15 5l-7 7 7 7"/>'),
    chevron_down: svg('gow-svg-ui', '<path d="M6 9.5l6 6 6-6"/>'),
    plus: svg('gow-svg-ui', '<path d="M12 5v14M5 12h14"/>'),
    minus: svg('gow-svg-ui', '<path d="M5 12h14"/>'),
    target: svg('gow-svg-ui', '<circle cx="12" cy="12" r="6.5"/><path d="M12 2.5v4M12 17.5v4M2.5 12h4M17.5 12h4"/>'),
    frame: svg('gow-svg-ui', '<path d="M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5"/>'),
    relief: svg('gow-svg-ui', '<path d="M2.5 18.5l6-9 4 5.5 3-4 6 7.5z"/><path d="M8.5 9.5l1.6 2.3"/>'),
    follow: svg('gow-svg-ui', '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.2l3.4 8.6L12 13.9l-3.4 1.9z"/>'),
    search: svg('gow-svg-ui', '<circle cx="10.5" cy="10.5" r="6"/><path d="M15 15l5 5"/>'),
    book: svg('gow-svg-ui', '<path d="M4 5.5c2.7-.8 5.4-.6 8 1 2.6-1.6 5.3-1.8 8-1v13c-2.7-.8-5.4-.6-8 1-2.6-1.6-5.3-1.8-8-1z"/><path d="M12 6.5v13"/>'),
    check: svg('gow-svg-ui', '<path d="M5 12.5l4.5 4.5L19 7.5"/>'),
    dot: '<svg class="gow-svg-glyph gow-svg-ui" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 6l6 6-6 6-6-6z" fill="currentColor"/></svg>'
  };

  
  var CAT_STYLE = {
    odins_raven:          { g: 'raven',      c: '#8eb4e3' },
    nornir_chest:         { g: 'norn',       c: '#c8a258' },
    legendary_chest:      { g: 'legendary',  c: '#e5c378' },
    lore:                 { g: 'lore',       c: '#d9cfb4' },
    artifact:             { g: 'artifact',   c: '#c9a77a' },
    berserker_gravestone: { g: 'berserker',  c: '#c94a38' },
    hel_tear:             { g: 'hel_tear',   c: '#8eb4e3' },
    yggdrasil_rift:       { g: 'rift',       c: '#a7b8f0' },
    favor:                { g: 'favour',     c: '#e5c378' },
    mystic_gateway:       { g: 'gateway',    c: '#8eb4e3' },
    boss:                 { g: 'boss',       c: '#c94a38' },
    armor_set:            { g: 'armor',      c: '#b9c3cc' },
    relic:                { g: 'relic',      c: '#d6a35c' },
    buried_treasure:      { g: 'treasure',   c: '#d6b06a' },
    treasure_map:         { g: 'treasure',   c: '#d6b06a' },
    kvasirs_poem:         { g: 'poem',       c: '#d9cfb4' },
    jewel_of_yggdrasil:   { g: 'jewel',      c: '#7fd0c4' },
    remnant_of_asgard:    { g: 'shard',      c: '#e5c378' },
    draugr_hole:          { g: 'skull',      c: '#9aaab8' },
    sleeping_troll:       { g: 'troll',      c: '#9aaab8' },
    nine_realms_in_bloom: { g: 'bloom',      c: '#e39ab8' },
    shield:               { g: 'shield',     c: '#b9c3cc' },
    ingredient:           { g: 'ingredient', c: '#a8c48a' },
    kol_raider_camp:      { g: 'camp',       c: '#c97a4a' },
    shop:                 { g: 'shop',       c: '#9aaab8' },
    entrance:             { g: 'door',       c: '#9aaab8' },
    hacksilver:           { g: 'loot',       c: '#9aaab8' },
    red_coffin:           { g: 'loot',       c: '#b06a5a' },
    wood_chest:           { g: 'loot',       c: '#a88a62' },
    other_loot:           { g: 'loot',       c: '#9aaab8' },
    miscellaneous:        { g: 'rune',       c: '#9aaab8' }
  };
  var CAT_ORDER = ['odins_raven', 'nornir_chest', 'legendary_chest', 'artifact', 'lore',
    'berserker_gravestone', 'hel_tear', 'yggdrasil_rift', 'favor', 'mystic_gateway', 'boss',
    'armor_set', 'relic', 'jewel_of_yggdrasil', 'remnant_of_asgard', 'buried_treasure',
    'treasure_map', 'kvasirs_poem', 'nine_realms_in_bloom', 'draugr_hole', 'sleeping_troll',
    'ingredient', 'shield', 'kol_raider_camp'];

  function catStyle(key) { return CAT_STYLE[key] || { g: 'rune', c: '#c8a258' }; }
  function catGlyph(key) { return GOW_SVG[catStyle(key).g]; }

  var REALM_SHORT = {
    midgard: tr('s000'), vanaheim: tr('s001'), svartalfheim: tr('s002'), alfheim: tr('s003'),
    jotunheim: tr('s004'), asgard: tr('s005'), helheim: tr('s006'), niflheim: tr('s007'),
    muspelheim: tr('s008'), 'sindris-house': tr('s009')
  };
  var REALM_ORDER = ['midgard', 'vanaheim', 'svartalfheim', 'alfheim', 'jotunheim', 'asgard',
    'helheim', 'niflheim', 'muspelheim', 'sindris-house'];

  var FILTER_MODES = [
    { key: 'favors',    label: tr('s010'), hint: tr('s011') },
    { key: 'remaining', label: tr('s012'), hint: tr('s013') },
    { key: 'scored',    label: tr('s014'),       hint: tr('s015') },
    { key: 'all',       label: tr('s016'), hint: tr('s017') }
  ];

  
  var S = {
    data: null,
    realm: null,              
    realmLoaded: null,        
    mode: 'remaining',
    category: null,           
    region: '',
    query: '',
    selectedId: null,
    follow: true,
    leftCollapsed: window.innerWidth < 900,
    pollTimer: null,
    pollMs: 4000,
    fetching: false,
    lastLiveRealm: null,
    mapSource: 'mapgenie',    
    gameRealms: [],
    openFavorGuides: {},
    guideSeen: {},
    guideToast: null
  };
  var map = null, tiles = null, poiLayer = null, kratosMarker = null, markerById = {};
  try { S.guideSeen = JSON.parse(sessionStorage.getItem('gowGuideSeen') || '{}') || {}; } catch (e) {}

  try {
    var saved = JSON.parse(localStorage.getItem('gowFsPrefs') || '{}');
    if (saved.mode) S.mode = saved.mode;
    if (typeof saved.follow === 'boolean') S.follow = saved.follow;
    if (typeof saved.leftCollapsed === 'boolean') S.leftCollapsed = saved.leftCollapsed;
    if (saved.mapSource === 'game') S.mapSource = 'game';
  } catch (e) {  }
  var hashRealm = (window.location.hash.match(/realm=([\w-]+)/) || [])[1];
  if (hashRealm && REALM_SHORT[hashRealm]) S.realm = hashRealm;

  function savePrefs() {
    try {
      localStorage.setItem('gowFsPrefs', JSON.stringify({
        mode: S.mode, follow: S.follow, leftCollapsed: S.leftCollapsed, mapSource: S.mapSource }));
    } catch (e) {  }
  }

  
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function $(id) { return document.getElementById(id); }
  function replaceHudHTML(el, html) {
    if (el._gowHtml === html) return;
    var active = document.activeElement, key = null, value = null;
    if (active && el.contains(active)) {
      ['data-realm', 'data-guide-point', 'data-favor-guide', 'data-current-point', 'data-favor', 'data-favor-realm', 'data-cat', 'data-mode', 'data-src', 'data-pin', 'id'].some(function (attr) {
        if (active.hasAttribute(attr)) { key = attr; value = active.getAttribute(attr); return true; }
        return false;
      });
    }
    el.innerHTML = html; el._gowHtml = html;
    if (key) Array.from(el.querySelectorAll('[' + key + ']')).some(function (b) {
      if (b.getAttribute(key) === value) { b.focus({ preventScroll: true }); return true; }
      return false;
    });
  }
  function pct(a, b) { return b > 0 ? Math.round(100 * a / b) : 0; }
  // Pin description: MapGenie original (EN) or our optional Russian translation (data/ru_descriptions.json).
  function descPref() {
    var v = localStorage.getItem('gowDescLang');
    return v === 'en' || v === 'ru' ? v : (window.GowI18n.lang === 'ru' ? 'ru' : 'en');
  }
  function descText(p) {
    if (p.description_ru && p.description_en) return descPref() === 'ru' ? p.description_ru : p.description_en;
    return p.description || '';
  }
  function descHtml(p) {
    var text = descText(p);
    if (!text) return p.guide ? '' : tr('s071');
    var sw = '';
    if (p.description_ru && p.description_en) {
      var cur = descPref();
      sw = '<div class="gow-fs-desc-lang" id="gowFsDescLang" role="group" aria-label="' + esc(tr('desc_toggle')) + '">' +
        [['en', tr('desc_original')], ['ru', tr('desc_translation')]].map(function (o) {
          return '<button type="button" class="gow-fs-desc-lang-btn' + (cur === o[0] ? ' is-active' : '') +
            '" data-desc-lang="' + o[0] + '" aria-pressed="' + (cur === o[0]) + '">' + esc(o[1]) + '</button>';
        }).join('') + '</div>';
    }
    return sw + '<div class="gow-fs-drawer-desc" id="gowFsDrawerDesc">' + mdLite(text) + '</div>';
  }

  function mdLite(text) {
    var s = esc(text || '');
    
    s = s.replace(/\[((?:[^\[\]]|\[[^\[\]]*\])+)\]\(pin:([a-z-]*):(\d+)\)/g,
      '<a href="#" class="gow-pin-link" data-realm="$2" data-pin="$3">$1</a>');
    s = s.replace(/\[((?:[^\[\]]|\[[^\[\]]*\])+)\]\((?:[^)\s]+)\)/g, '$1');
    s = s.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    s = s.replace(/(^|[\s(])_([^_]+)_(?=[\s).,;:!?]|$)/g, '$1<em>$2</em>');
    var html = '', block = null;
    function close() { if (block) html += '</' + block + '>'; block = null; }
    s.split(/\r?\n/).forEach(function (line) {
      var item = line.match(/^\s*(?:(\d+)\.\s+|-\s+)(.*)$/);
      if (!line.trim()) { close(); return; }
      var kind = item ? (item[1] ? 'ol' : 'ul') : 'p';
      if (block !== kind) {
        close(); html += '<' + kind + (kind === 'ol' ? ' start="' + Number(item[1]) + '"' : '') + '>'; block = kind;
      }
      else if (!item) html += '<br>';
      html += item ? '<li>' + item[2] + '</li>' : line;
    });
    close();
    return html;
  }
  function guideHtml(guide, title) {
    if (!guide || !guide.text) return '';
    var sources = (guide.sources || []).filter(function (url) { return /^https?:\/\/\S+$/i.test(url); });
    return '<section class="gow-fs-guide" lang="' + (guide.lang === 'ru' ? 'ru' : 'en') + '">' +
      (title ? '<h3>' + esc(title) + '</h3>' : '') +
      '<div class="gow-fs-drawer-desc">' + mdLite(guide.text) + '</div>' +
      (sources.length ? '<details><summary>' + esc(tr('guide_sources')) + '</summary><ul>' + sources.map(function (url) {
        return '<li><a href="' + esc(url) + '" target="_blank" rel="noopener">' + esc(url) + '</a></li>';
      }).join('') + '</ul></details>' : '') + '</section>';
  }
  function poiState(p) {
    if (p.status === 'unknown') return 'unknown';
    if (p.status === 'collected' || p.is_collected) return 'collected';
    if (p.is_completionist) return 'remaining';
    return 'resource';
  }

  
  function buildUI() {
    var root = document.createElement('div');
    root.id = 'gowFs';
    root.className = 'gow-fs-root';
    root.innerHTML =
      '<div id="gowInteractiveMap" class="gow-fs-map"></div>' +
      '<div class="gow-fs-vignette" aria-hidden="true"></div>' +

      '<header class="gow-fs-topbar gow-fs-plate" id="gowFsTopbar">' +
        tr('s018') +
          tr('s019') +
          '<div class="gow-fs-global-num"><span id="gowFsGlobalNum">—</span><em id="gowFsGlobalPct"></em></div>' +
          '<div class="gow-fs-bar"><i id="gowFsGlobalBar"></i></div>' +
        '</div>' +
        tr('s020') +
        '<div class="gow-fs-top-actions">' +
          '<div class="gow-fs-menu" id="gowFsModeMenu">' +
            '<button class="gow-fs-btn gow-fs-mode-btn" id="gowFsModeBtn" type="button" aria-haspopup="listbox">' +
              tr('s021') + GOW_SVG.chevron_down + '</button>' +
            '<div class="gow-fs-menu-list gow-fs-plate" id="gowFsModeList" role="listbox"></div>' +
          '</div>' +
          tr('s022') +
            GOW_SVG.book + tr('s023') +
        '</div>' +
      '</header>' +

      '<aside class="gow-fs-left-panel gow-fs-plate" id="gowFsLeftPanel">' +
        tr('s024') +
          GOW_SVG.chevron_left + '</button>' +
        '<div class="gow-fs-left-inner">' +
          '<div class="gow-fs-left-header">' +
            tr('s025') +
            '<h1 class="gow-fs-world-name" id="gowFsWorldName">—</h1>' +
            tr('s026') +
            '<div class="gow-fs-progress-row"><span id="gowFsRealmNum">—</span><em id="gowFsRealmPct"></em></div>' +
            '<div class="gow-fs-bar gow-fs-bar-lg"><i id="gowFsProgressFill"></i></div>' +
          '</div>' +
          '<div class="gow-fs-tools">' +
            '<label class="gow-fs-search-wrap">' + GOW_SVG.search +
              tr('s027') +
            '</label>' +
            '<div class="gow-fs-select-wrap">' +
              tr('s028') +
              GOW_SVG.chevron_down +
            '</div>' +
          '</div>' +
          tr('s029') +
          '<div class="gow-fs-checklist" id="gowFsChecklist"></div>' +
          tr('s030') +
        '</div>' +
      '</aside>' +

      '<div class="gow-fs-controls gow-fs-plate" id="gowFsControls">' +
        tr('s031') + GOW_SVG.plus + '</button>' +
        tr('s032') + GOW_SVG.minus + '</button>' +
        '<span class="gow-fs-ctl-sep"></span>' +
        tr('s033') + GOW_SVG.frame + '</button>' +
        tr('s034') + GOW_SVG.target + '</button>' +
        tr('s035') + GOW_SVG.follow + '</button>' +
        tr('s036') + GOW_SVG.relief + '</button>' +
      '</div>' +

      tr('s037') +

      '<aside class="gow-fs-right-drawer gow-fs-plate" id="gowFsRightDrawer" aria-hidden="true">' +
        tr('s038') + GOW_SVG.close + '</button>' +
        '<div class="gow-fs-drawer-body" id="gowFsDrawerBody"></div>' +
      '</aside>' +

      '<div class="gow-fs-lightbox" id="gowFsLightbox"><img id="gowFsLightboxImg" alt="" /></div>' +

      '<div class="gow-fs-codex-modal" id="gowFsCodexModal">' +
        '<div class="gow-fs-codex-body gow-fs-plate" id="gowFsCodexBody"></div>' +
      '</div>';
    document.body.appendChild(root);
    var languageButton = document.createElement('button');
    languageButton.type = 'button'; languageButton.id = 'gowLanguage';
    languageButton.className = 'gow-fs-btn'; languageButton.textContent = 'RU / EN';
    languageButton.setAttribute('aria-label', window.GowI18n.t('language'));
    languageButton.onclick = function () {
      localStorage.setItem('gowLanguage', window.GowI18n.lang === 'ru' ? 'en' : 'ru');
      location.reload();
    };
    root.querySelector('.gow-fs-top-actions').prepend(languageButton);
    var credit = document.createElement('div'); credit.className = 'gow-map-credit';
    credit.innerHTML = tr('map_credit') + ' <a href="https://mapgenie.io/god-of-war-ragnarok" target="_blank" rel="noreferrer">MapGenie</a>';
    root.appendChild(credit);
    document.body.classList.add('gow-fullscreen-mode');
    $('gowFsLeftPanel').classList.toggle('collapsed', S.leftCollapsed);
    renderModeMenu();
    bindUI();
  }

  
  
  
  function useGameTiles(realmKey) {
    return S.mapSource === 'game' && S.gameRealms.indexOf(realmKey) >= 0;
  }
  function tileUrl(realmKey) {
    return (useGameTiles(realmKey) ? '/gow-game-tiles/' : '/gow-tiles/') + realmKey + '/{z}/{x}/{y}.png';
  }
  function tilesKey(realmKey) { return realmKey + (useGameTiles(realmKey) ? ':game' : ':mg'); }
  function updateSourceButton() {
    var b = $('gowFsSource');
    if (!b) return;
    var key = S.realmLoaded || S.realm;
    b.hidden = !(key && S.gameRealms.indexOf(key) >= 0);
    b.classList.toggle('on', useGameTiles(key));
  }
  function toggleMapSource() {
    S.mapSource = S.mapSource === 'game' ? 'mapgenie' : 'game';
    savePrefs();
    var key = S.realmLoaded;
    if (tiles && key && S.tilesRealm !== tilesKey(key)) { tiles.setUrl(tileUrl(key)); S.tilesRealm = tilesKey(key); }
    updateSourceButton();
  }
  function loadGameRealms() {
    fetch('/gow-game-tiles/available.json', { cache: 'no-store' })
      .then(function (r) { return r.ok ? r.json() : { realms: [] }; })
      .then(function (d) {
        S.gameRealms = d.realms || [];
        var key = S.realmLoaded;
        if (tiles && key && S.tilesRealm !== tilesKey(key)) { tiles.setUrl(tileUrl(key)); S.tilesRealm = tilesKey(key); }
        updateSourceButton();
      })
      .catch(function () {  });
  }

  function ensureMap(rm) {
    if (typeof L === 'undefined') {
      setStatus(tr('s039'), 'warn');
      return false;
    }
    var key = rm.selected_realm_key;
    var minZ = rm.min_zoom || 9, maxZ = rm.max_zoom || 14;
    if (!map) {
      map = L.map('gowInteractiveMap', {
        zoomControl: false, attributionControl: false, minZoom: minZ, maxZoom: maxZ,
        zoomSnap: 0.5, zoomDelta: 0.5, wheelPxPerZoomLevel: 90, inertia: true
      });
      tiles = L.tileLayer(tileUrl(key), {
        minZoom: minZ, maxZoom: maxZ, maxNativeZoom: maxZ, noWrap: true, keepBuffer: 4,
        errorTileUrl: 'data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=='
      }).addTo(map);
      S.tilesRealm = tilesKey(key);
      poiLayer = L.layerGroup().addTo(map);
      map.on('click', function () { closeDrawer(); });
      map.on('dragstart', function () { S.userPanAt = Date.now(); });
      window.gowLeafletMap = map;
    }
    if (S.realmLoaded !== key) {
      if (S.tilesRealm !== tilesKey(key)) { tiles.setUrl(tileUrl(key)); S.tilesRealm = tilesKey(key); }
      tiles.options.minZoom = minZ; tiles.options.maxZoom = maxZ; tiles.options.maxNativeZoom = maxZ;
      map.setMinZoom(minZ); map.setMaxZoom(maxZ);
      fitRealm(rm, false);
      S.realmLoaded = key;
      updateSourceButton();
      S.region = ''; S.category = null; S.query = '';
      $('gowFsSearch').value = '';
      closeDrawer();
    }
    return true;
  }

  function isVisible(p) {
    var st = poiState(p);
    if (S.mode === 'favors') {
      if (!favorPinState(p) || favorPinState(p) === 'collected') return false;
    }
    if (S.mode === 'remaining' && (!p.is_completionist || (st !== 'remaining' && st !== 'unknown'))) return false;
    if (S.mode === 'scored' && !p.is_completionist) return false;
    if (S.mode !== 'favors' && S.category && p.category_key !== S.category) return false;
    if (S.region && p.region !== S.region) return false;
    if (S.query) {
      var hay = ((favorPinName(p) || '') + ' ' + (p.name || '') + ' ' + (p.region || '') + ' ' + (p.category || '') +
        ' ' + (p.artifact || '')).toLowerCase();
      if (hay.indexOf(S.query) < 0) return false;
    }
    return true;
  }

  function markerIcon(p) {
    var st = poiState(p);
    if (S.mode === 'favors') st = favorPinState(p) === 'not_collected' ? 'remaining' : favorPinState(p);
    var cs = catStyle(p.category_key);
    var size = st === 'resource' ? 24 : 32;
    return L.divIcon({
      className: 'gow-pin gow-pin--' + st + (S.mode === 'favors' ? ' gow-pin--favor' : '') +
        (p.id === S.selectedId ? ' is-selected' : ''),
      iconSize: [size, size],
      iconAnchor: [size / 2, size / 2],
      html: '<div class="gow-pin-plate" style="--pin:' + cs.c + '">' + catGlyph(p.category_key) + '</div>'
    });
  }

  function renderMarkers() {
    if (!map || !S.data) return;
    var pois = S.data.realms_map.realm_pois || [];
    poiLayer.clearLayers();
    markerById = {};
    var shown = 0;
    pois.forEach(function (p) {
      if (p.lat == null || p.lng == null || !isVisible(p)) return;
      var st = poiState(p);
      if (S.mode === 'favors') st = favorPinState(p) === 'not_collected' ? 'remaining' : favorPinState(p);
      var m = L.marker([p.lat, p.lng], {
        icon: markerIcon(p), riseOnHover: true, keyboard: false,
        zIndexOffset: st === 'remaining' ? 500 : (st === 'collected' ? 0 : -200)
      });
      m.bindTooltip(esc(favorPinName(p)), { direction: 'top', offset: [0, -14], className: 'gow-fs-tip' });
      m.on('click', function (ev) {
        L.DomEvent.stopPropagation(ev);
        openDrawer(p.id);
      });
      m.addTo(poiLayer);
      markerById[p.id] = m;
      shown++;
    });
    S.shownCount = shown;
    renderFavorTargets();
  }

  var TARGET_SVG = '<svg viewBox="0 0 32 32" aria-hidden="true"><circle cx="16" cy="16" r="10"/>' +
    '<circle cx="16" cy="16" r="3"/><path d="M16 1v8m0 14v8M1 16h8m14 0h8"/></svg>';
  function renderFavorTargets() {
    if (S.mode !== 'favors') return;
    var groups = {};
    activeFavors().forEach(function (f) { (f.points || []).forEach(function (p, i) {
      if (p.realm !== S.realmLoaded) return;
      var key = p.lat + ':' + p.lng;
      (groups[key] || (groups[key] = [])).push({ favor: f, point: p, index: i });
    }); });
    Object.keys(groups).forEach(function (key) { var group = groups[key]; group.forEach(function (entry, i) {
      // Screen-space offsets leave the anchor coordinates and metre distances intact.
      var angle = i * Math.PI * 2 / group.length, radius = group.length > 1 ? Math.max(20, group.length * 7) : 0;
      var p = entry.point, f = entry.favor;
      var marker = L.marker([p.lat, p.lng], { zIndexOffset: 1200, keyboard: false,
        icon: L.divIcon({ className: 'gow-favor-target', iconSize: [36, 36],
          iconAnchor: [18 - Math.cos(angle) * radius, 18 - Math.sin(angle) * radius], html: TARGET_SVG }) });
      marker.bindTooltip(esc(p.label), { direction: 'top', offset: [0, -18], className: 'gow-fs-tip' });
      marker.on('click', function (ev) { L.DomEvent.stopPropagation(ev); openFavorGuide(f.id, true); });
      marker.addTo(poiLayer);
    }); });
  }

  
  function liveRadar(lt) {
    if (!lt || lt.available !== true || !lt.radar) return null;
    var r = lt.radar;
    if (typeof r.map_lat !== 'number' || typeof r.map_lng !== 'number') return null;
    
    if (projConfidence(r) === 'none') return null;
    return r;
  }
  function projConfidence(r) {
    if (!r) return 'none';
    if (r.projection_confidence) return r.projection_confidence;
    if (r.projection_status === 'fallback_bbox') return 'none';
    return r.projection_status === 'proven_wad' || !r.projection_status ? 'proven' : 'approximate';
  }
  function yawOf(lt, r) {
    var cands = [r && r.yaw_deg, lt && lt.position && lt.position.yaw_deg, lt && lt.kratos && lt.kratos.yaw_deg];
    for (var i = 0; i < cands.length; i++) if (typeof cands[i] === 'number' && isFinite(cands[i])) return cands[i];
    return null;
  }

  function updateKratos(lt) {
    var r = liveRadar(lt);
    var kratosHere = r && (r.realm_key || S.realm) === S.realmLoaded;
    $('gowFsCenter').disabled = !kratosHere;
    if (!kratosHere) {
      if (kratosMarker && map && map.hasLayer(kratosMarker)) map.removeLayer(kratosMarker);
      return;
    }
    var yaw = yawOf(lt, r);
    if (!kratosMarker) {
      kratosMarker = L.marker([r.map_lat, r.map_lng], {
        zIndexOffset: 3000, interactive: false, keyboard: false,
        icon: L.divIcon({
          className: 'gow-kratos', iconSize: [150, 150], iconAnchor: [75, 75],
          html: '<div class="gow-kratos-rot">' +
            '<svg class="gow-kratos-cone" viewBox="-60 -60 120 120" aria-hidden="true">' +
              '<defs><radialGradient id="gowKratosCone" cx="0" cy="0" r="60" gradientUnits="userSpaceOnUse">' +
              '<stop offset="0" stop-color="#f0cf7a" stop-opacity=".55"/>' +
              '<stop offset="1" stop-color="#f0cf7a" stop-opacity="0"/></radialGradient></defs>' +
              '<path d="M0 0L-31 -51.4A60 60 0 0 1 31 -51.4Z" fill="url(#gowKratosCone)"/></svg>' +
            '<div class="gow-kratos-ring"></div>' + GOW_SVG.kratos + '</div>'
        })
      });
    }
    if (!map.hasLayer(kratosMarker)) kratosMarker.addTo(map);
    kratosMarker.setLatLng([r.map_lat, r.map_lng]);
    var el = kratosMarker.getElement();
    if (el) {
      el.classList.toggle('no-yaw', yaw == null);
      el.classList.toggle('is-approx', projConfidence(r) === 'approximate');
      var rot = el.querySelector('.gow-kratos-rot');
      if (rot && yaw != null) {
        
        var prev = S.lastYaw == null ? yaw : S.lastYaw;
        var d = ((yaw - prev) % 360 + 540) % 360 - 180;
        S.lastYaw = prev + d;
        rot.style.transform = 'rotate(' + S.lastYaw + 'deg)';
      }
    }
    var idle = S.userPanAt && Date.now() - S.userPanAt < 6000;
    if (S.follow && !idle) map.panTo([r.map_lat, r.map_lng], { animate: true, duration: 0.8, easeLinearity: 1 });
  }

  
  function realmEntries() {
    var rm = S.data.realms_map;
    var byKey = {};
    (rm.realms || []).forEach(function (r) { byKey[r.key] = r; });
    return REALM_ORDER.map(function (key) {
      var r = byKey[key] || { key: key, name: REALM_SHORT[key] };
      var comp = key === 'sindris-house' ? rm.sindris_house_completion : r.completion;
      return { key: key, name: REALM_SHORT[key] || r.name, comp: comp || {}, current: !!r.is_current };
    });
  }

  function renderTopbar() {
    var rm = S.data.realms_map;
    var g = rm.global_completion || {};
    $('gowFsGlobalNum').textContent = (g.collected || 0) + ' / ' + (g.total || 0);
    $('gowFsGlobalPct').textContent = pct(g.collected, g.total) + '%';
    $('gowFsGlobalBar').style.width = pct(g.collected, g.total) + '%';

    var tabsHtml = realmEntries().map(function (r, i) {
      var c = r.comp, p = pct(c.collected, c.total), done = c.total > 0 && c.collected >= c.total;
      return '<button type="button" class="gow-fs-realm-tab' + (r.key === S.realm ? ' active' : '') +
        (r.current ? ' current-ingame' : '') + (done ? ' done' : '') + '" data-realm="' + r.key + '" title="' +
        esc(r.name) + ': ' + (c.collected || 0) + tr('s040') + (c.total || 0) + (r.current ? tr('s041') : '') +
        tr('s042') + ((i + 1) % 10) + '">' +
        '<span class="gow-fs-realm-name">' + (r.current ? '<i class="gow-fs-here">' + GOW_SVG.dot + '</i>' : '') + esc(r.name) + '</span>' +
        '<span class="gow-fs-realm-meta"><span class="gow-fs-bar"><i style="width:' + p + '%"></i></span>' +
        '<span class="gow-fs-realm-pct">' + (done ? GOW_SVG.check : p + '%') + '</span></span>' +
        '</button>';
    }).join('');
    replaceHudHTML($('gowFsRealmTabs'), tabsHtml);
  }

  function realmPoisInScope() {
    var pois = S.data.realms_map.realm_pois || [];
    return S.region ? pois.filter(function (p) { return p.region === S.region; }) : pois;
  }

  function renderLeft() {
    var rm = S.data.realms_map;
    var entry = realmEntries().filter(function (r) { return r.key === S.realm; })[0] || { comp: {} };
    $('gowFsRealmKicker').textContent = entry.current ? tr('s043') : tr('s044');
    $('gowFsWorldName').textContent = REALM_SHORT[S.realm] || rm.realm_name || '—';
    $('gowFsRegionName').textContent = S.region || tr('s045');
    document.querySelector('.gow-fs-checklist-head > span').textContent = S.mode === 'favors' ? tr('s046') : tr('s047');

    var scope = realmPoisInScope();
    var scored = scope.filter(function (p) { return p.is_completionist; });
    var got = scored.filter(function (p) { return poiState(p) === 'collected'; }).length;
    $('gowFsRealmNum').textContent = got + ' / ' + scored.length;
    $('gowFsRealmPct').textContent = pct(got, scored.length) + '%';
    $('gowFsProgressFill').style.width = pct(got, scored.length) + '%';

    
    var sel = $('gowFsRegionSelect');
    var regions = {};
    (rm.realm_pois || []).forEach(function (p) { if (p.region) regions[p.region] = 1; });
    var opts = tr('s048') + Object.keys(regions).sort().map(function (r) {
      return '<option value="' + esc(r) + '"' + (r === S.region ? ' selected' : '') + '>' + esc(r) + '</option>';
    }).join('');
    if (sel.getAttribute('data-sig') !== S.realm + '|' + Object.keys(regions).length) {
      sel.innerHTML = opts;
      sel.setAttribute('data-sig', S.realm + '|' + Object.keys(regions).length);
    }
    sel.value = S.region;
    if (S.mode === 'favors') { renderFavors(); return; }

    
    var cats = {};
    scope.forEach(function (p) {
      var k = p.is_completionist ? p.category_key : '__resources';
      if (!cats[k]) cats[k] = { key: k, name: p.is_completionist ? p.category : tr('s049'), total: 0, got: 0 };
      cats[k].total++;
      if (poiState(p) === 'collected') cats[k].got++;
    });
    var keys = Object.keys(cats).filter(function (k) { return k !== '__resources'; });
    keys.sort(function (a, b) {
      var ia = CAT_ORDER.indexOf(a), ib = CAT_ORDER.indexOf(b);
      if (ia < 0) ia = 999; if (ib < 0) ib = 999;
      if (ia !== ib) return ia - ib;
      return (cats[b].total - cats[b].got) - (cats[a].total - cats[a].got);
    });
    var html = keys.map(function (k) {
      var c = cats[k], done = c.got >= c.total, cs = catStyle(k);
      return '<button type="button" class="gow-fs-cat-row' + (done ? ' done' : '') +
        (S.category === k ? ' active' : '') + (S.category && S.category !== k ? ' dimmed' : '') +
        '" data-cat="' + esc(k) + '" style="--pin:' + cs.c + '">' +
        '<span class="gow-fs-cat-icon">' + catGlyph(k) + '</span>' +
        '<span class="gow-fs-cat-label">' + esc(c.name) + '</span>' +
        '<span class="gow-fs-cat-count">' + (done ? GOW_SVG.check : c.got + '<small>/' + c.total + '</small>') + '</span>' +
        '</button>';
    }).join('');
    if (!keys.length) html = tr('s050');
    if (cats.__resources && S.mode === 'all') {
      html += '<div class="gow-fs-cat-note">' + GOW_SVG.loot + tr('s051') + cats.__resources.total +
        tr('s052');
    }
    replaceHudHTML($('gowFsChecklist'), html);
    $('gowFsCatReset').hidden = !S.category;
  }

  function renderModeMenu() {
    var cur = FILTER_MODES.filter(function (m) { return m.key === S.mode; })[0] || FILTER_MODES[0];
    $('gowFsModeLabel').textContent = cur.label;
    $('gowFsModeList').innerHTML = FILTER_MODES.map(function (m) {
      return '<button type="button" role="option" class="gow-fs-menu-item' + (m.key === S.mode ? ' active' : '') +
        '" data-mode="' + m.key + '"><span>' + esc(m.label) + '</span><small>' + esc(m.hint) + '</small></button>';
    }).join('');
  }

  function setStatus(text, kind) {
    var el = $('gowFsStatus');
    if (!el) return;
    el.className = 'gow-fs-status gow-fs-plate' + (kind ? ' is-' + kind : '');
    $('gowFsStatusText').innerHTML = text;
  }

  
  function nearestPin(d, r) {
    var rm = d.realms_map || {}, pois = rm.realm_pois || [], best = null, bd = Infinity;
    if ((rm.selected_realm_key || S.realm) !== (r.realm_key || S.realm)) return null;
    for (var i = 0; i < pois.length; i++) {
      var p = pois[i];
      if (typeof p.lat !== 'number' || typeof p.lng !== 'number') continue;
      var dd = Math.hypot(p.lat - r.map_lat, p.lng - r.map_lng);
      if (dd < bd) { bd = dd; best = p; }
    }
    if (!best) return null;
    var k = r.map_scale_per_metre;
    return { name: best.name, metres: (typeof k === 'number' && k > 0) ? Math.round(bd / k) : null };
  }

  function updateGuideToast() {
    var el = $('gowGuideToast');
    if (!el) {
      el = document.createElement('div'); el.id = 'gowGuideToast';
      el.className = 'gow-fs-guide-toast gow-fs-plate'; el.hidden = true;
      el.innerHTML = '<button type="button" data-guide-open></button><button type="button" data-guide-dismiss aria-label="' +
        esc(tr('guide_dismiss')) + '">×</button>';
      el.querySelector('[data-guide-open]').onclick = function () {
        var item = S.guideToast;
        if (!item) return;
        if (item.favor) { focusGuidePoint(item.favor.id, item.index); }
        else { if (S.mode === 'favors') setMode('remaining'); focusPin(item.pin.id); }
      };
      el.querySelector('[data-guide-dismiss]').onclick = function () { el.hidden = true; S.guideToast = null; };
      $('gowFs').appendChild(el);
    }
    var r = liveRadar(S.data && S.data.live_telemetry), k = r && r.map_scale_per_metre;
    if (!r || r.realm_key !== S.realmLoaded || typeof k !== 'number' || !isFinite(k) || k <= 0) {
      el.hidden = true; S.guideToast = null; return;
    }
    var candidates = [];
    (S.data.realms_map.realm_pois || []).forEach(function (p) {
      if (p.guide && !p.is_manual && (p.status === 'not_collected' || p.is_collected === false)) {
        candidates.push({ key: 'pin:' + p.id, pin: p, lat: p.lat, lng: p.lng });
      }
    });
    activeFavors().forEach(function (f) { (f.points || []).forEach(function (p, i) {
      if (p.realm === r.realm_key) candidates.push({ key: 'favor:' + f.id + ':' + p.realm + ':' + p.anchor_pin,
        favor: f, index: i, lat: p.lat, lng: p.lng });
    }); });
    candidates.forEach(function (p) { p.distance = Math.hypot(p.lat - r.map_lat, p.lng - r.map_lng) / k; });
    // Keep the current toast through 30–45 m jitter; completed/removed sites disappear immediately.
    var current = S.guideToast && candidates.filter(function (p) { return p.key === S.guideToast.key && p.distance <= 45; })[0];
    if (current) { S.guideToast = current; return; }
    var next = candidates.filter(function (p) { return p.distance <= 30 && !S.guideSeen[p.key]; })
      .sort(function (a, b) { return a.distance - b.distance; })[0];
    S.guideToast = next || null; el.hidden = !next;
    if (!next) return;
    S.guideSeen[next.key] = true;
    try { sessionStorage.setItem('gowGuideSeen', JSON.stringify(S.guideSeen)); } catch (e) {}
    el.querySelector('[data-guide-open]').textContent = next.favor ?
      tr('guide_near_favor').replace('{name}', next.favor.name) :
      tr(next.pin.category_key === 'nornir_chest' ? 'guide_near_nornir' : 'guide_near_pin').replace('{name}', next.pin.name);
  }

  function renderStatus() {
    var d = S.data, lt = d.live_telemetry || {}, r = liveRadar(lt);
    if (r) {
      var np = nearestPin(d, r);
      var near = np ? tr('s053') + esc(np.name) + (np.metres != null ? ', ' + np.metres + tr('s054') : '') : '';
      var approx = projConfidence(r) === 'approximate' ? tr('s055') : '';
      setStatus(tr('s056') + esc(REALM_SHORT[r.realm_key] || r.realm_name || '') + approx + near, 'live');
      return;
    }
    if (!d.save || !d.save.ok) {
      setStatus(esc(tr('no_save')) + (lt.process_running ? ' · ' + esc(lt.reason || '') : ''), lt.process_running ? 'warn' : '');
      if (d.notices && d.notices.length > 1) $('gowFsStatusText').innerHTML += ' · ' + esc(d.notices.slice(1).join(' · '));
      return;
    }
    var save = d.save || {}, slot = (save.source && save.source.slot) || tr('s057');
    var where = save.place ? esc(save.place.split(' - ').slice(0, 2).join(' · ')) : '';
    var off = lt.available === true && lt.radar && projConfidence(lt.radar) === 'none';
    var why = lt.reason_code === 'unsupported_build' || lt.reason_code === 'build_unverified' ? ' · ' + esc(lt.reason) : off ? tr('s058')
      : lt.process_running ? tr('s059') : '';
    setStatus(tr('s060') + esc(slot) + tr('s061') + (where ? ' · ' + where : '') + why,
      lt.process_running ? 'warn' : '');
    if (d.notices && d.notices.length) $('gowFsStatusText').innerHTML += ' · ' + esc(d.notices.join(' · '));
  }

  
  function findPoi(id) {
    var pois = (S.data && S.data.realms_map.realm_pois) || [];
    for (var i = 0; i < pois.length; i++) if (pois[i].id === id) return pois[i];
    return null;
  }

  function openDrawer(id) {
    var p = findPoi(id);
    if (!p) return;
    if (S.mode === 'favors' && favorPinState(p) === null) { closeDrawer(); return; }
    var prev = S.selectedId;
    S.selectedId = id;
    [prev, id].forEach(function (k) {
      var q = k && findPoi(k);
      if (q && markerById[k]) markerById[k].setIcon(markerIcon(q));
    });
    var st = poiState(p), cs = catStyle(p.category_key);
    var statusText = st === 'collected' ? (p.is_manual ? tr('s062') : tr('s063'))
      : st === 'remaining' ? tr('s064') : tr('s065');
    if (S.mode === 'favors') {
      var favorState = favorPinState(p);
      st = favorState === 'not_collected' ? 'remaining' : favorState;
      statusText = favorState === 'not_collected' ? tr('s066') :
        favorState === 'collected' ? tr('s067') : tr('s068');
    }
    var media = (p.media || []).filter(Boolean);
    var img = media.length
      ? '<button type="button" class="gow-fs-shot" data-src="' + esc(media[0]) + '"><img src="' + esc(media[0]) +
        '" alt="" loading="lazy" /></button>' +
        (media.length > 1 ? '<div class="gow-fs-thumbs">' + media.slice(1, 5).map(function (u) {
          return '<button type="button" class="gow-fs-thumb" data-src="' + esc(u) + '"><img src="' + esc(u) + '" alt="" loading="lazy" /></button>';
        }).join('') + '</div>' : '')
      : '';
    var canToggle = S.mode !== 'favors' && (!p.is_completionist || p.is_manual || st !== 'collected');
    var drawerHtml =
      '<div class="gow-fs-drawer-cat" style="--pin:' + cs.c + '"><span class="gow-fs-drawer-glyph">' + catGlyph(p.category_key) +
        '</span><span>' + esc(p.category || '') + '</span></div>' +
      '<h2 class="gow-fs-drawer-title" id="gowFsDrawerTitle">' + esc(favorPinName(p) || tr('s069')) + '</h2>' +
      (p.region ? '<div class="gow-fs-drawer-region">' + esc(p.region) + '</div>' : '') +
      (p.artifact ? tr('s070') + esc(p.artifact) + '</div>' : '') +
      '<div class="gow-fs-drawer-status is-' + st + '">' + (st === 'collected' ? GOW_SVG.check : GOW_SVG.dot) +
        '<span>' + statusText + '</span></div>' +
      img +
      descHtml(p) +
      guideHtml(p.guide, tr('guide_solve')) +
      (canToggle ? '<button type="button" class="gow-fs-btn gow-fs-check-btn" id="gowFsCheckBtn" data-next="' +
        (st === 'collected' ? '0' : '1') + '">' + (st === 'collected' ? tr('s072') : tr('s073')) + '</button>' : '');
    replaceHudHTML($('gowFsDrawerBody'), drawerHtml);
    var descSwitch = $('gowFsDescLang');
    if (descSwitch) descSwitch.onclick = function (ev) {
      var b = ev.target.closest('[data-desc-lang]');
      if (!b) return;
      localStorage.setItem('gowDescLang', b.getAttribute('data-desc-lang'));
      var box = $('gowFsDrawerDesc');
      if (box) box.innerHTML = mdLite(descText(p));
      Array.prototype.forEach.call(descSwitch.querySelectorAll('[data-desc-lang]'), function (x) {
        x.classList.toggle('is-active', x === b); x.setAttribute('aria-pressed', x === b ? 'true' : 'false');
      });
    };
    var dr = $('gowFsRightDrawer');
    dr.classList.add('open');
    dr.setAttribute('aria-hidden', 'false');
    $('gowFs').classList.add('drawer-open');
  }

  
  function focusPin(id) {
    var p = findPoi(id);
    if (!p) return;
    if (S.mode === 'favors' && !markerById[id]) {
      S.region = ''; S.query = ''; $('gowFsSearch').value = ''; rerender();
      if (!markerById[id]) { setStatus(tr('s074')); return; }
    }
    if (!markerById[id]) {
      S.category = null; S.region = ''; S.query = ''; $('gowFsSearch').value = '';
      setMode('all'); rerender();
    }
    if (map) map.panTo([p.lat, p.lng], { animate: true });
    openDrawer(id);
  }

  function closeDrawer() {
    var dr = $('gowFsRightDrawer');
    if (!dr || !dr.classList.contains('open')) return false;
    dr.classList.remove('open');
    dr.setAttribute('aria-hidden', 'true');
    $('gowFs').classList.remove('drawer-open');
    var prev = S.selectedId;
    S.selectedId = null;
    var q = prev && findPoi(prev);
    if (q && markerById[prev]) markerById[prev].setIcon(markerIcon(q));
    return true;
  }

  function toggleCollected(next) {
    var id = S.selectedId;
    if (!id) return;
    try {
      var marks = JSON.parse(localStorage.getItem('gowMarks') || '{}');
      if (next === '1') marks[id] = true; else delete marks[id];
      localStorage.setItem('gowMarks', JSON.stringify(marks));
    } catch (e) { return; }
    refresh().then(function () { if (S.selectedId === id) openDrawer(id); });
  }

  function renderCodex() {
    var d = S.data || {}, save = d.save || {}, adv = d.progression_advice || {}, hints = d.hints || [];
    var rows = [
      [tr('s077'), save.place], [tr('s078'), save.objective], [tr('s079'), save.play_time], [tr('s080'), save.difficulty],
      [tr('s081'), adv.power_level], [tr('s082'), adv.hacksilver != null ? Number(adv.hacksilver).toLocaleString(window.GowI18n.lang) : null],
      [tr('s083'), adv.skills_count], [tr('s084'), adv.total_unused_flames]
    ].filter(function (r) { return r[1] != null && r[1] !== ''; });
    var build = adv.build_synergy && adv.build_synergy.archetype_name
      ? tr('s085') + esc(adv.build_synergy.archetype_name) + '</em></p>' : '';
    var hintHtml = hints.slice(0, 8).map(function (h) {
      return '<li><strong>' + esc(h.name) + '</strong><span>' + esc(h.desc || h.hint_text || '') + '</span></li>';
    }).join('');
    $('gowFsCodexBody').innerHTML =
      tr('s086') + GOW_SVG.close + '</button>' +
      tr('s087') +
      '<dl class="gow-fs-codex-grid">' + rows.map(function (r) {
        return '<dt>' + esc(r[0]) + '</dt><dd>' + esc(r[1]) + '</dd>';
      }).join('') + '</dl>' + build +
      (hintHtml ? tr('s088') + hintHtml + '</ul>' : '');
  }
  function openCodex() { renderCodex(); $('gowFsCodexModal').classList.add('open'); $('gowFsCodexModal').querySelector('button').focus(); }
  function closeCodex() {
    var m = $('gowFsCodexModal');
    if (!m.classList.contains('open')) return false;
    m.classList.remove('open'); return true;
  }
  function openLightbox(src) { $('gowFsLightboxImg').src = src; $('gowFsLightbox').classList.add('open'); }
  function closeLightbox() {
    var lb = $('gowFsLightbox');
    if (!lb.classList.contains('open')) return false;
    lb.classList.remove('open'); return true;
  }

  
  function switchGowRealm(key) {
    if (!REALM_SHORT[key] || key === S.realm) return;
    S.realm = key;
    history.replaceState(null, '', '#realm=' + key);
    renderTopbar();
    
    $('gowFsWorldName').textContent = REALM_SHORT[key];
    $('gowFs').classList.add('is-loading');
    setStatus(tr('s089') + esc(REALM_SHORT[key]) + '…');
    refresh();
  }
  function setMode(mode) {
    if (mode === 'favors') { S.category = null; S.region = ''; S.query = ''; $('gowFsSearch').value = ''; }
    S.mode = mode; savePrefs(); renderModeMenu();
    $('gowFsModeMenu').classList.remove('open');
    rerender();
  }
  function toggleGowUncollectedOnly() { setMode(S.mode === 'remaining' ? 'scored' : 'remaining'); }
  
  function hudPadding() {
    if (window.innerWidth < 900) return { paddingTopLeft: [30,140], paddingBottomRight: [70,120] };
    var left = S.leftCollapsed ? 60 : 380;
    return { paddingTopLeft: [left, 110], paddingBottomRight: [90, 70] };
  }
  function fitRealm(rm, animate) {
    var pts = (rm.realm_pois || []).filter(function (p) { return p.lat != null && p.lng != null; })
      .map(function (p) { return [p.lat, p.lng]; });
    if (pts.length < 2) {
      map.setView([rm.center_lat, rm.center_lng], rm.initial_zoom || 11, { animate: false });
      return;
    }
    var opts = hudPadding();
    opts.maxZoom = Math.min(13, rm.max_zoom || 13);
    if (animate) { opts.duration = 0.6; map.flyToBounds(L.latLngBounds(pts).pad(0.08), opts); }
    else { opts.animate = false; map.fitBounds(L.latLngBounds(pts).pad(0.08), opts); }
  }
  function resetGowMapView() {
    if (!map || !S.data) return;
    fitRealm(S.data.realms_map, true);
  }
  function centerOnKratos() {
    var r = liveRadar(S.data && S.data.live_telemetry);
    if (!r || !map) return;
    if (r.realm_key && r.realm_key !== S.realm) { switchGowRealm(r.realm_key); return; }
    S.userPanAt = 0;
    map.flyTo([r.map_lat, r.map_lng], Math.max(map.getZoom(), 12), { duration: 0.6 });
  }
  function toggleGowAutoFollow() {
    S.follow = !S.follow; savePrefs();
    $('gowFsFollow').classList.toggle('on', S.follow);
    if (S.follow) centerOnKratos();
  }
  function toggleLeft() {
    S.leftCollapsed = !S.leftCollapsed; savePrefs();
    $('gowFsLeftPanel').classList.toggle('collapsed', S.leftCollapsed);
  }
  function rerender() { renderLeft(); renderMarkers(); }

  function activeFavors() {
    return ((S.data && S.data.realms_map.favors) || []).filter(function (f) { return f.state === 'active'; });
  }
  function favorPinState(p) {
    var states = activeFavors().filter(function (f) { return (p.favor_ids || []).indexOf(f.id) >= 0; }).map(function (f) {
      return (f.pin_states && f.pin_states[p.id]) || 'unknown';
    });
    if (states.indexOf('unknown') >= 0) return 'unknown';
    if (states.indexOf('not_collected') >= 0) return 'not_collected';
    return states.length ? 'collected' : null;
  }
  function favorPinName(p) {
    if (S.mode !== 'favors' || p.category_key !== 'favor') return p.name;
    var favor = activeFavors().filter(function (f) { return (p.favor_ids || []).indexOf(f.id) >= 0; })[0];
    return favor ? favor.name : p.name;
  }
  function favorRealms(f) {
    var result = Object.keys(f.pin_realms || {}).filter(function (id) {
      return (f.pin_states || {})[id] !== 'collected';
    }).map(function (id) { return f.pin_realms[id]; });
    if (!Object.keys(f.pin_realms || {}).length && f.realm) result.push(f.realm);
    (f.points || []).forEach(function (p) { result.push(p.realm); });
    return result.filter(function (k, i) { return result.indexOf(k) === i; });
  }
  function currentGuidePoint(f) {
    var ids = f.step_ids || (f.objectives || []).map(function (o) { return o.id; });
    return (f.points || []).findIndex(function (p) { return p.step != null && ids.indexOf(p.step) >= 0; });
  }
  function favorGuidePanel(f) {
    var points = f.points || [], current = currentGuidePoint(f);
    var note = current >= 0 ? '<button type="button" class="gow-fs-link" data-current-point="' + esc(f.id) + '">' +
      esc(tr('guide_point')) + '</button>' : points.length ? '<span class="gow-fs-favor-note">' +
      esc(tr('guide_points')) + points.length + '</span>' : f.step_locations_unknown ? tr('s093') : '';
    return '<div class="gow-fs-favor-help">' + note +
      (f.guide ? '<button type="button" class="gow-fs-link" data-favor-guide="' + esc(f.id) +
        '" aria-expanded="' + !!S.openFavorGuides[f.id] + '">' + esc(tr('guide_button')) + '</button>' : '') +
      points.map(function (p, i) { return '<button type="button" class="gow-fs-guide-point" data-point-favor="' + esc(f.id) +
        '" data-guide-point="' + i + '">' + TARGET_SVG + '<span>' + esc(p.label) +
        (p.realm !== S.realm ? ' · ' + esc(REALM_SHORT[p.realm] || p.realm) : '') + '</span></button>'; }).join('') +
      (S.openFavorGuides[f.id] && f.guide ? '<div class="gow-fs-favor-guide">' + guideHtml(f.guide) + '</div>' : '') + '</div>';
  }
  function openFavorGuide(id, force) {
    var f = activeFavors().filter(function (q) { return q.id === id; })[0];
    if (!f) return;
    if (force) {
      closeDrawer();
      setMode('favors');
      S.leftCollapsed = false; $('gowFsLeftPanel').classList.remove('collapsed');
    }
    S.openFavorGuides[id] = force || !S.openFavorGuides[id];
    renderFavors();
    var button = Array.from($('gowFsChecklist').querySelectorAll('[data-favor-guide]')).filter(function (b) {
      return b.getAttribute('data-favor-guide') === id;
    })[0];
    if (button && force) { button.scrollIntoView({ block: 'nearest' }); button.focus({ preventScroll: true }); }
  }
  function focusGuidePoint(id, index) {
    var f = activeFavors().filter(function (q) { return q.id === id; })[0], p = f && (f.points || [])[index];
    if (!p) return;
    S.follow = false; $('gowFsFollow').classList.remove('on'); savePrefs();
    if (p.realm !== S.realmLoaded) {
      S.pendingGuidePoint = { id: id, index: index }; switchGowRealm(p.realm); return;
    }
    setMode('favors');
    if (map) map.setView([p.lat, p.lng], Math.max(map.getZoom(), 13));
    openFavorGuide(id, true);
  }
  function renderFavors() {
    var active = activeFavors(), groups = {}, others = {};
    active.forEach(function (f) {
      var realms = favorRealms(f);
      if (!realms.length || realms.indexOf(S.realm) >= 0) (groups[f.region || tr('s090')] || (groups[f.region || tr('s090')] = [])).push(f);
      realms.forEach(function (r) { if (r !== S.realm && REALM_SHORT[r]) (others[r] || (others[r] = [])).push(f.id); });
    });
    var html = Object.keys(groups).map(function (group) {
      return '<h2 class="gow-fs-favor-group">' + esc(group) + '</h2>' + groups[group].map(function (f) {
        var objectives = f.objectives && f.objectives.length ? f.objectives : [{ name: f.step || tr('s091'), counter: f.counter }];
        return '<button type="button" class="gow-fs-favor-row" data-favor="' + esc(f.id) + '">' +
          '<span class="gow-fs-favor-title">' + GOW_SVG.favour + esc(f.name) + '</span>' +
          objectives.map(function (o) {
            return '<span class="gow-fs-favor-step">' + esc(o.name) + '</span>' +
              (o.counter ? '<span class="gow-fs-favor-count">' + o.counter.done + tr('s040') + o.counter.total + '</span>' :
               o.counter_unknown ? tr('s092') : '');
          }).join('') + (Object.keys(f.pin_states || {}).some(function (id) {
            return (f.pin_realms || {})[id] === S.realm && f.pin_states[id] === 'unknown';
          }) ? tr('s094') : '') + '</button>' + favorGuidePanel(f);
      }).join('');
    }).join('');
    if (!html) html = tr('s095');
    var outside = active.filter(function (f) { return favorRealms(f).some(function (r) { return r !== S.realm; }); }).length;
    if (outside) {
      html += tr('s096') + outside + tr('s097') +
        Object.keys(others).map(function (r) { return '<button type="button" class="gow-fs-favor-world" data-favor-realm="' + r + '">' +
          esc(REALM_SHORT[r]) + '<span>' + others[r].length + '</span></button>'; }).join('');
    }
    replaceHudHTML($('gowFsChecklist'), html);
    $('gowFsCatReset').hidden = true;
  }
  function focusFavor(id) {
    var f = activeFavors().filter(function (q) { return q.id === id; })[0];
    if (!f) return;
    var point = currentGuidePoint(f);
    if ((f.points || []).length) { focusGuidePoint(id, point >= 0 ? point : 0); return; }
    S.region = ''; S.query = ''; $('gowFsSearch').value = '';
    rerender();
    var pins = (S.data.realms_map.realm_pois || []).filter(function (p) {
      return (p.favor_ids || []).indexOf(id) >= 0 && (f.pin_states || {})[p.id] !== 'collected' &&
        p.lat != null && p.lng != null && isVisible(p);
    });
    if (!pins.length) { setStatus(tr('s099')); return; }
    focusPin(pins[0].id);
    if (pins.length > 1 && map) { var o = hudPadding(); o.paddingBottomRight = [430, 70]; o.maxZoom = 13; map.fitBounds(pins.map(function (p) { return [p.lat, p.lng]; }), o); }
  }

  
  function moveHudFocus(backwards) {
    if ($('gowFsLightbox').classList.contains('open')) return;
    var root = $('gowFsCodexModal').classList.contains('open') ? $('gowFsCodexModal') :
      $('gowFsModeMenu').classList.contains('open') ? $('gowFsModeMenu') : $('gowFs');
    var controls = Array.from(root.querySelectorAll('button, input, select, a[href], [role="button"]')).filter(function (b) {
      return !b.disabled && b.getClientRects().length && getComputedStyle(b).visibility !== 'hidden' && !b.closest('[aria-hidden="true"]') &&
        !(b.closest('#gowFsLeftPanel.collapsed') && b.id !== 'gowFsLeftToggle');
    });
    if (!controls.length) return;
    var i = controls.indexOf(document.activeElement);
    var b = controls[i < 0 ? (backwards ? controls.length - 1 : 0) :
      (i + (backwards ? -1 : 1) + controls.length) % controls.length];
    if (b) { b.focus({ preventScroll: true }); b.scrollIntoView({ block: 'nearest' }); }
  }
  var padLastAt = 0, padHeld = false;
  function closeTopLayer() {
    if (closeLightbox() || closeCodex()) return true;
    if ($('gowFsModeMenu').classList.contains('open')) {
      $('gowFsModeMenu').classList.remove('open'); $('gowFsModeBtn').focus(); return true;
    }
    return closeDrawer();
  }
  function activateHudControl() {
    var el = document.activeElement;
    if (!el) return;
    if (el.tagName === 'SELECT') {
      el.selectedIndex = (el.selectedIndex + 1) % el.options.length;
      el.dispatchEvent(new Event('change', { bubbles: true }));
    } else if (el.click) el.click();
  }
  function pollFavorPad(now) {
    var pads = navigator.getGamepads ? navigator.getGamepads() : [];
    var pad = Array.from(pads).filter(function (p) { return p && p.mapping === 'standard'; })[0];
    if (pad) {
      var down = function (i) { return pad.buttons[i] && pad.buttons[i].pressed; };
      if ((down(12) || down(13) || down(14) || down(15)) && now - padLastAt > 180) {
        moveHudFocus(down(12) || down(14)); padLastAt = now;
      }
      if (down(0) && !padHeld) activateHudControl();
      if (down(1) && !padHeld) closeTopLayer();
      padHeld = down(0) || down(1);
    }
    requestAnimationFrame(pollFavorPad);
  }

  
  window.switchGowRealm = switchGowRealm;
  window.toggleGowUncollectedOnly = toggleGowUncollectedOnly;
  window.resetGowMapView = resetGowMapView;
  window.centerOnKratos = centerOnKratos;
  window.toggleGowAutoFollow = toggleGowAutoFollow;

  function bindUI() {
    $('gowFsRealmTabs').addEventListener('click', function (e) {
      var b = e.target.closest('[data-realm]');
      if (b) switchGowRealm(b.getAttribute('data-realm'));
    });
    $('gowFsModeBtn').addEventListener('click', function (e) {
      e.stopPropagation(); $('gowFsModeMenu').classList.toggle('open');
    });
    $('gowFsModeList').addEventListener('click', function (e) {
      var b = e.target.closest('[data-mode]');
      if (b) setMode(b.getAttribute('data-mode'));
    });
    document.addEventListener('click', function (e) {
      if (!e.target.closest('#gowFsModeMenu')) $('gowFsModeMenu').classList.remove('open');
    });
    $('gowFsCodexBtn').addEventListener('click', openCodex);
    $('gowFsCodexModal').addEventListener('click', function (e) {
      if (e.target.id === 'gowFsCodexModal' || e.target.closest('[data-close-codex]')) closeCodex();
    });
    $('gowFsLeftToggle').addEventListener('click', toggleLeft);
    $('gowFsSearch').addEventListener('input', function (e) {
      S.query = e.target.value.trim().toLowerCase(); renderMarkers();
    });
    $('gowFsRegionSelect').addEventListener('change', function (e) {
      S.region = e.target.value; rerender(); fitRegion();
    });
    $('gowFsChecklist').addEventListener('click', function (e) {
      var point = e.target.closest('[data-guide-point]');
      if (point) { focusGuidePoint(point.getAttribute('data-point-favor'), Number(point.getAttribute('data-guide-point'))); return; }
      var current = e.target.closest('[data-current-point]');
      if (current) {
        var f = activeFavors().filter(function (q) { return q.id === current.getAttribute('data-current-point'); })[0];
        if (f) focusGuidePoint(f.id, currentGuidePoint(f));
        return;
      }
      var guide = e.target.closest('[data-favor-guide]');
      if (guide) { openFavorGuide(guide.getAttribute('data-favor-guide')); return; }
      var favor = e.target.closest('[data-favor]');
      if (favor) { focusFavor(favor.getAttribute('data-favor')); return; }
      var world = e.target.closest('[data-favor-realm]');
      if (world) { switchGowRealm(world.getAttribute('data-favor-realm')); return; }
      var b = e.target.closest('[data-cat]');
      if (!b) return;
      var k = b.getAttribute('data-cat');
      S.category = S.category === k ? null : k;
      if (S.category && S.mode === 'remaining' && b.classList.contains('done')) setMode('scored');
      else rerender();
    });
    $('gowFsCatReset').addEventListener('click', function () { S.category = null; rerender(); });
    $('gowFsZoomIn').addEventListener('click', function () { map && map.zoomIn(); });
    $('gowFsZoomOut').addEventListener('click', function () { map && map.zoomOut(); });
    $('gowFsReset').addEventListener('click', resetGowMapView);
    $('gowFsCenter').addEventListener('click', centerOnKratos);
    $('gowFsFollow').addEventListener('click', toggleGowAutoFollow);
    $('gowFsSource').addEventListener('click', toggleMapSource);
    loadGameRealms();
    $('gowFsFollow').classList.toggle('on', S.follow);
    $('gowFsDrawerClose').addEventListener('click', closeDrawer);
    $('gowFsDrawerBody').addEventListener('click', function (e) {
      var shot = e.target.closest('[data-src]');
      if (shot) { openLightbox(shot.getAttribute('data-src')); return; }
      var chk = e.target.closest('#gowFsCheckBtn');
      if (chk) toggleCollected(chk.getAttribute('data-next'));
    });
    $('gowFs').addEventListener('click', function (e) {
      var link = e.target.closest('.gow-pin-link');
      if (link) {
        e.preventDefault();
        var id = link.getAttribute('data-pin'), realm = link.getAttribute('data-realm');
        if (realm && realm !== S.realmLoaded) { S.pendingOpen = id; switchGowRealm(realm); }
        else focusPin(id);
      }
    });
    $('gowFsLightbox').addEventListener('click', closeLightbox);

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        if (closeTopLayer()) e.preventDefault();
        if (document.activeElement && document.activeElement.blur) document.activeElement.blur();
        return;
      }
      if (e.key === 'Tab') { e.preventDefault(); toggleLeft(); return; }
      var t = e.target;
      if (t && (t.tagName === 'INPUT' || t.tagName === 'SELECT' || t.tagName === 'TEXTAREA')) return;
      if (e.ctrlKey || e.altKey || e.metaKey) return;
      if (/^Arrow(Up|Down|Left|Right)$/.test(e.key)) { e.preventDefault(); moveHudFocus(e.key === 'ArrowUp' || e.key === 'ArrowLeft'); return; }
      if (/^[0-9]$/.test(e.key)) {
        var idx = e.key === '0' ? 9 : Number(e.key) - 1;
        if (REALM_ORDER[idx]) switchGowRealm(REALM_ORDER[idx]);
      } else if (e.key === 'u' || e.key === 'U' || e.key === tr('s100') || e.key === tr('s101')) {
        toggleGowUncollectedOnly();
      } else if (e.key === 'c' || e.key === 'C' || e.key === tr('s102') || e.key === tr('s103')) {
        centerOnKratos();
      } else if (e.key === 'r' || e.key === 'R' || e.key === tr('s104') || e.key === tr('s105')) {
        resetGowMapView();
      }
    });
    requestAnimationFrame(pollFavorPad);
  }

  function fitRegion() {
    if (!map || !S.region) return;
    var pts = realmPoisInScope().filter(function (p) { return p.lat != null; })
      .map(function (p) { return [p.lat, p.lng]; });
    if (pts.length) { var o = hudPadding(); o.maxZoom = 13; o.duration = 0.6; map.flyToBounds(pts, o); }
  }

  
  function dataSig(d) {
    var rm = d.realms_map;
    return rm.selected_realm_key + ':' + (rm.realm_pois || []).map(function (p) {
      return p.id + (p.status || '') + (p.is_manual ? 'm' : '') + JSON.stringify(p.guide || null);
    }).join(',') + ':' + JSON.stringify(rm.favors || []);
  }

  function refresh() {
    if (S.fetching) { S.refetch = true; return S.inflight; }
    S.fetching = true; S.refetch = false;
    var url = '/api/map?lang=' + window.GowI18n.lang + (S.realm ? '&realm=' + encodeURIComponent(S.realm) : '');
    try {
      var savedMarks = JSON.parse(localStorage.getItem('gowMarks') || '{}');
      url += '&marked=' + encodeURIComponent(Object.keys(savedMarks).filter(function (id) { return savedMarks[id]; }).join(','));
    } catch (e) { /* Storage may be unavailable. */ }
    S.inflight = fetch(url, { cache: 'no-store' })
      .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(function (d) {
        if (!d || !d.ok || !d.realms_map) throw new Error(tr('s106'));
        var rm = d.realms_map;
        try {
          var marks = JSON.parse(localStorage.getItem('gowMarks') || '{}');
          (rm.realm_pois || []).forEach(function (p) {
            if (marks[p.id]) { p.is_manual = true; p.is_collected = true; p.status = 'collected'; }
          });
        } catch (e) { /* Storage may be unavailable. */ }
        
        if (S.realm && rm.selected_realm_key !== S.realm) return;
        var sig = dataSig(d), changed = sig !== S.sig;
        S.data = d; S.sig = sig;
        if (!S.realm) { S.realm = rm.selected_realm_key; }
        if (!ensureMap(rm)) return;
        $('gowFs').classList.remove('is-loading');
        renderTopbar();
        if (changed) rerender();
        renderStatus();
        updateKratos(d.live_telemetry);
        updateGuideToast();
        autoSwitchRealm(d.live_telemetry);
        if (S.pendingGuidePoint && S.realm === S.realmLoaded) {
          var gp = S.pendingGuidePoint; S.pendingGuidePoint = null; focusGuidePoint(gp.id, gp.index);
        }
        if (S.pendingOpen && findPoi(S.pendingOpen)) { var po = S.pendingOpen; S.pendingOpen = null; focusPin(po); }
        else if (S.selectedId && changed && $('gowFsRightDrawer').classList.contains('open')) openDrawer(S.selectedId);
        var lt = d.live_telemetry || {};
        schedule(lt.process_running ? 1000 : 4000);
      })
      .catch(function (err) {
        setStatus(tr('s107') + esc(err.message || err), 'warn');
        schedule(5000);
      })
      .then(function () {
        S.fetching = false;
        if (S.refetch) return refresh();
      });
    return S.inflight;
  }

  
  function autoSwitchRealm(lt) {
    var r = liveRadar(lt);
    if (!r || !r.realm_key) return;
    if (r.realm_key !== S.lastLiveRealm) {
      var first = S.lastLiveRealm == null;
      S.lastLiveRealm = r.realm_key;
      if (!first && r.realm_key !== S.realm) { S.follow = true; switchGowRealm(r.realm_key); }
    }
  }

  function schedule(ms) {
    if (S.pollTimer && S.pollMs === ms) return;
    clearInterval(S.pollTimer);
    S.pollMs = ms;
    S.pollTimer = setInterval(refresh, ms);
  }

  function start() {
    buildUI();
    refresh();
    window.addEventListener('resize', function () { if (map) map.invalidateSize(); });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();

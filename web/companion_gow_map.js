
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
    kratos: '<svg class="gow-svg-glyph gow-svg-kratos" viewBox="0 0 36 36" aria-hidden="true">' +
      '<path d="M18 1.5l4.2 6.8h-8.4z" fill="#f0cf7a" stroke="#18120c" stroke-width="1"/>' +
      '<circle cx="18" cy="19.5" r="11.2" fill="#17191d" stroke="#d8a94c" stroke-width="2.1"/>' +
      '<circle cx="18" cy="19.5" r="9.1" fill="none" stroke="rgba(220,76,56,.78)" stroke-width="1.2"/>' +
      '<path d="M12.7 25.2h3.4l-.8-1.9a5.2 5.2 0 1 1 5.4 0l-.8 1.9h3.4" fill="none" stroke="#e44c36" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    
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
    dot: '<svg class="gow-svg-glyph gow-svg-ui" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 6l6 6-6 6-6-6z" fill="currentColor"/></svg>',
    compass: svg('gow-svg-ui gow-compass-needle', '<path d="M12 3l3.6 9-3.6 9-3.6-9z"/><path d="M12 3l3.6 9H8.4z" fill="currentColor"/>'),
    trail: svg('gow-svg-ui', '<path d="M4 18c3-6 5-2 8-7s5-1 8-6"/><circle cx="4" cy="18" r="1.6" fill="currentColor"/><circle cx="20" cy="5" r="1.6" fill="currentColor"/>'),
    nearest: svg('gow-svg-ui', '<path d="M12 2.5l2.4 6.6 6.6 2.4-6.6 2.4-2.4 6.6-2.4-6.6-6.6-2.4 6.6-2.4z"/>'),
    route: svg('gow-svg-ui', '<circle cx="5.5" cy="18" r="2.1"/><circle cx="18.5" cy="6" r="2.1"/><path d="M7.5 17.5c4.5 0 2.5-5.5 6.5-5.5s2-5.5 2.5-6"/>'),
    wake: svg('gow-svg-ui', '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2.2M12 19.3v2.2M2.5 12h2.2M19.3 12h2.2M5.3 5.3l1.6 1.6M17.1 17.1l1.6 1.6M18.7 5.3l-1.6 1.6M6.9 17.1l-1.6 1.6"/>'),
    lock: svg('gow-svg-ui', '<rect x="5" y="11" width="14" height="9" rx="1.5"/><path d="M8 11V7.5a4 4 0 0 1 8 0V11"/>'),
    eye: svg('gow-svg-ui', '<path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6z"/><circle cx="12" cy="12" r="2.6"/>'),
    spark: svg('gow-svg-ui', '<path d="M12 3l2.1 6.1L20 12l-5.9 2.9L12 21l-2.1-6.1L4 12l5.9-2.9z"/>'),
    crest: svg('gow-svg-ui', '<path d="M12 3l7.5 3.5V12c0 4.6-3.2 7.8-7.5 9.2C7.7 19.8 4.5 16.6 4.5 12V6.5z"/><path d="M12 7v9M8.8 10.5L12 8l3.2 2.5"/>'),
    snow: svg('gow-svg-ui', '<path d="M12 2.5v19M3.8 7.2l16.4 9.6M20.2 7.2L3.8 16.8M9.5 4.8L12 7l2.5-2.2M9.5 19.2L12 17l2.5 2.2M5.2 10.5l2.4-.6-.6-2.4M18.8 13.5l-2.4.6.6 2.4M18.8 10.5l-2.4-.6.6-2.4M5.2 13.5l2.4.6-.6 2.4"/>'),
    fullscreen: svg('gow-svg-ui', '<path d="M3.5 9V3.5H9M15 3.5h5.5V9M20.5 15v5.5H15M9 20.5H3.5V15M3.5 3.5l5.2 5.2M20.5 3.5l-5.2 5.2M20.5 20.5l-5.2-5.2M3.5 20.5l5.2-5.2"/>'),
    fullscreen_exit: svg('gow-svg-ui', '<path d="M9 3.5V9H3.5M15 3.5V9h5.5M15 20.5V15h5.5M9 20.5V15H3.5"/>'),
    quill: svg('gow-svg-ui', '<path d="M19.5 4.5c-5.8.6-10.2 4.3-12.6 10.2L5 19.5l4.8-1.9c5.9-2.4 9.6-6.8 9.7-13.1z"/><path d="M5 19.5l8.8-8.8M11 10.8l3.8-.5M8.8 13.8l4.1-.4"/>'),
    book_open: svg('gow-svg-ui', '<path d="M2.5 6.2c2.8-.9 5.8-.7 9.5 1.3 3.7-2 6.7-2.2 9.5-1.3v12.4c-2.8-.9-5.8-.7-9.5 1.3-3.7-2-6.7-2.2-9.5-1.3z"/><path d="M12 7.5v12.4M6 10.5h3.2M6 13.8h3.2M14.8 10.5H18M14.8 13.8H18"/>')
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
    mapSource: 'native3d',    
    gameRealms: [],
    native3dRealms: {},
    openFavorGuides: {},
    guideSeen: {},
    guideToast: null,
    showTrail: true,
    weatherOn: true,
    beaconPinId: null,
    beaconTarget: null,
    autoAdvanceBeacon: false,
    routeActive: false,
    routeMode: null,
    routeTarget: null,
    routeOriginInfo: null,
    routePins: [],
    routeMetres: null,
    pendingRoute: null,
    wakeLockOn: false,
    wakeSentinel: null,
    codex: null,
    codexLoading: false,
    codexLive: false,
    sse: null,
    codexTab: 'bestiary',
    codexBookMode: true,
    bookCatOpen: true,
    bookToolsOpen: false,
    bookTexReady: false,
    bookTexChecked: false,
    gameMapIconsReady: false,
    gameMapIconsChecked: false,
    codexCat: '',
    codexStatus: 'all',
    treasureFilter: 'all',
    codexValhalla: false,
    codexSpoiler: true,
    codexSort: 'unlocked',
    codexQuery: '',
    codexSelectedId: null,
    codexRevealed: {},
    codexNewIds: {},
    codexMobileDetail: false,
    codexSkillFilter: 'all',
    codexMaterialQuery: '',
    codexToastTimer: null,
    codexToastAction: null
  };
  var map = null, tiles = null, poiLayer = null, kratosMarker = null, markerById = {};
  try { S.guideSeen = JSON.parse(sessionStorage.getItem('gowGuideSeen') || '{}') || {}; } catch (e) {}

  var ASSET_REV = '20261128_codex2';
  var PREFS_VER = 2;
  try {
    var saved = JSON.parse(localStorage.getItem('gowFsPrefs') || '{}');
    if (saved.mode) S.mode = saved.mode;
    if (typeof saved.follow === 'boolean') S.follow = saved.follow;
    if (typeof saved.leftCollapsed === 'boolean') S.leftCollapsed = saved.leftCollapsed;
    if (saved.prefsVer === PREFS_VER) {
      if (saved.mapSource === 'mapgenie') S.mapSource = 'mapgenie';
      else if (saved.mapSource === 'native3d' || saved.mapSource === 'game') S.mapSource = 'native3d';
    } else {
      // One-time migration from legacy pre-Native-3D default ('mapgenie') to full native 3D engine
      S.mapSource = 'native3d';
    }
    if (typeof saved.showTrail === 'boolean') S.showTrail = saved.showTrail;
    if (typeof saved.weatherOn === 'boolean') S.weatherOn = saved.weatherOn;
    if (typeof saved.codexBookMode === 'boolean') S.codexBookMode = saved.codexBookMode;
    if (typeof saved.codexSpoiler === 'boolean') S.codexSpoiler = saved.codexSpoiler;
    if (typeof saved.codexValhalla === 'boolean') S.codexValhalla = saved.codexValhalla;
    if (saved.codexSort === 'alpha' || saved.codexSort === 'unlocked') S.codexSort = saved.codexSort;
  } catch (e) {  }
  var hashRealm = (window.location.hash.match(/realm=([\w-]+)/) || [])[1];
  if (hashRealm && REALM_SHORT[hashRealm]) S.realm = hashRealm;

  function savePrefs() {
    try {
      localStorage.setItem('gowFsPrefs', JSON.stringify({
        prefsVer: PREFS_VER,
        mode: S.mode, follow: S.follow, leftCollapsed: S.leftCollapsed,
        mapSource: S.mapSource, showTrail: S.showTrail, weatherOn: S.weatherOn,
        codexBookMode: S.codexBookMode,
        codexSpoiler: S.codexSpoiler, codexValhalla: S.codexValhalla, codexSort: S.codexSort }));
    } catch (e) {  }
  }
  savePrefs();

  
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
          '<button class="gow-fs-btn gow-fs-icon-btn" id="gowFsFullscreen" type="button" title="' + esc(tr('ctl_fullscreen')) + '" aria-label="' + esc(tr('ctl_fullscreen')) + '" aria-pressed="false">' + GOW_SVG.fullscreen + '</button>' +
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
              '<button type="button" class="gow-fs-search-clear" id="gowFsSearchClear" title="' + esc(tr('search_clear')) + '" hidden>×</button>' +
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
        '<button class="gow-fs-ctl gow-fs-ctl-text on" id="gowFs3D" type="button" title="' + esc(tr('ctl_3d')) + '">3D</button>' +
        '<div class="gow-fs-ctl-pair">' +
          '<button class="gow-fs-ctl gow-fs-ctl-half" id="gowFsRotL" type="button" title="' + esc(tr('ctl_rot_l')) + '">⟲</button>' +
          '<button class="gow-fs-ctl gow-fs-ctl-half" id="gowFsRotR" type="button" title="' + esc(tr('ctl_rot_r')) + '">⟳</button>' +
        '</div>' +
        '<button class="gow-fs-ctl is-north" id="gowFsCompass" type="button" title="' + esc(tr('ctl_compass')) + '">' + GOW_SVG.compass + '</button>' +
        '<span class="gow-fs-ctl-sep"></span>' +
        tr('s031') + GOW_SVG.plus + '</button>' +
        tr('s032') + GOW_SVG.minus + '</button>' +
        '<span class="gow-fs-ctl-sep"></span>' +
        '<button class="gow-fs-ctl" id="gowFsNearest" type="button" title="' + esc(tr('ctl_nearest')) + '">' + GOW_SVG.nearest + '</button>' +
        '<button class="gow-fs-ctl" id="gowFsRoute" type="button" title="' + esc(tr('ctl_route')) + '">' + GOW_SVG.route + '</button>' +
        '<button class="gow-fs-ctl" id="gowFsTrail" type="button" title="' + esc(tr('ctl_trail')) + '">' + GOW_SVG.trail + '</button>' +
        '<button class="gow-fs-ctl" id="gowFsWeather" type="button" title="' + esc(tr('ctl_weather')) + '">' + GOW_SVG.snow + '</button>' +
        tr('s033') + GOW_SVG.frame + '</button>' +
        tr('s034') + GOW_SVG.target + '</button>' +
        tr('s035') + GOW_SVG.follow + '</button>' +
        '<button class="gow-fs-ctl" id="gowFsWake" type="button" title="' + esc(tr('ctl_wake')) + '">' + GOW_SVG.wake + '</button>' +
        tr('s036') + GOW_SVG.relief + '</button>' +
      '</div>' +

      '<div class="gow-fs-beacon-pill gow-fs-plate" id="gowFsBeaconPill" title="' + esc(tr('beacon_jump')) + '" hidden>' +
        '<span class="gow-beacon-dot" id="gowFsBeaconDot"></span>' +
        '<strong id="gowFsBeaconDist"></strong>' +
        '<span class="gow-fs-beacon-name" id="gowFsBeaconName"></span>' +
        '<button class="gow-fs-beacon-x" id="gowFsBeaconClear" type="button" title="' + esc(tr('beacon_clear')) + '">×</button>' +
      '</div>' +

      '<div class="gow-fs-route-pill gow-fs-plate" id="gowFsRoutePill" title="' + esc(tr('route_pill_title')) + '" hidden>' +
        GOW_SVG.route +
        '<strong id="gowFsRouteLabel"></strong>' +
        '<span class="gow-fs-route-meta" id="gowFsRouteMeta"></span>' +
        '<button class="gow-fs-beacon-x" id="gowFsRouteClear" type="button" title="' + esc(tr('route_clear')) + '">×</button>' +
      '</div>' +

      '<div class="gow-codex-toast gow-fs-plate" id="gowCodexToast" hidden>' +
        '<button type="button" class="gow-codex-toast-open" id="gowCodexToastOpen">' +
          '<span class="gow-codex-toast-badge">' + esc(tr('codex_new_badge')) + '</span>' +
          '<span class="gow-codex-toast-text" id="gowCodexToastText"></span>' +
        '</button>' +
        '<button type="button" class="gow-fs-beacon-x" id="gowCodexToastClose" aria-label="' + esc(tr('guide_dismiss')) + '">×</button>' +
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
    var codexBtn = $('gowFsCodexBtn');
    if (codexBtn) {
      var badge = document.createElement('em');
      badge.className = 'gow-codex-badge';
      badge.id = 'gowFsCodexBadge';
      badge.hidden = true;
      codexBtn.appendChild(badge);
    }
    var credit = document.createElement('div'); credit.className = 'gow-map-credit';
    credit.innerHTML = tr('map_credit') + ' <a href="https://mapgenie.io/god-of-war-ragnarok" target="_blank" rel="noreferrer">MapGenie</a>';
    root.appendChild(credit);
    document.body.classList.add('gow-fullscreen-mode');
    $('gowFsLeftPanel').classList.toggle('collapsed', S.leftCollapsed);
    renderModeMenu();
    bindUI();
  }

  
  
  
  function hasNative3D(realmKey) {
    return Boolean(realmKey && S.native3dRealms && S.native3dRealms[realmKey]);
  }
  function useNative3D(realmKey) {
    return S.mapSource === 'native3d' && hasNative3D(realmKey);
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
    var avail = Boolean(key && (hasNative3D(key) || S.gameRealms.indexOf(key) >= 0));
    b.hidden = !avail;
    b.classList.toggle('on', useNative3D(key) || useGameTiles(key));
  }
  function toggleMapSource() {
    var key = S.realmLoaded || S.realm;
    if (hasNative3D(key)) {
      S.mapSource = S.mapSource === 'native3d' ? 'mapgenie' : 'native3d';
    } else {
      S.mapSource = S.mapSource === 'game' ? 'mapgenie' : 'game';
    }
    savePrefs();
    if (map && map.setNative3D) map.setNative3D(S.mapSource === 'native3d');
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
      map.on('camerachange', syncCameraControls);
      map.on('native3dready', function (ev) {
        if (ev && ev.realm) {
          S.native3dRealms[ev.realm] = Boolean(ev.meta && ev.meta.has_native_3d);
          if (map.setNative3D) map.setNative3D(S.mapSource === 'native3d');
          updateSourceButton();
        }
      });
      if (map.setNative3D) map.setNative3D(S.mapSource === 'native3d');
      if (map.setShowTrail) map.setShowTrail(S.showTrail);
      if (map.setWeatherEnabled) map.setWeatherEnabled(S.weatherOn);
      window.gowLeafletMap = map;
    }
    if (S.realmLoaded !== key) {
      clearBeacon();
      clearClearingRoute();
      if (map.setRealm) map.setRealm(key);
      if (S.tilesRealm !== tilesKey(key)) { tiles.setUrl(tileUrl(key)); S.tilesRealm = tilesKey(key); }
      tiles.options.minZoom = minZ; tiles.options.maxZoom = maxZ; tiles.options.maxNativeZoom = maxZ;
      map.setMinZoom(minZ); map.setMaxZoom(maxZ);
      fitRealm(rm, false);
      S.realmLoaded = key;
      updateSourceButton();
      S.region = ''; S.category = null; S.query = '';
      $('gowFsSearch').value = '';
      if ($('gowFsSearchClear')) $('gowFsSearchClear').hidden = true;
      closeDrawer();
    }
    return true;
  }

  function syncCameraControls() {
    if (!map) return;
    var b3d = $('gowFs3D');
    if (b3d) b3d.classList.toggle('on', !!map.mode3D);
    var comp = $('gowFsCompass');
    if (comp) {
      var yaw = ((map.yawDeg || 0) % 360 + 540) % 360 - 180;
      comp.classList.toggle('is-north', Math.abs(yaw) < 1.0);
      var needle = comp.querySelector('.gow-compass-needle');
      if (needle) needle.style.transform = 'rotate(' + yaw.toFixed(1) + 'deg)';
    }
    if (S.beaconTarget) renderBeaconPill();
    if (kratosMarker) {
      var el = kratosMarker.getElement();
      var rot = el && el.querySelector('.gow-kratos-rot');
      if (rot && S.lastYaw != null) {
        rot.style.transform = 'rotate(' + (S.lastYaw + (map.yawDeg || 0)).toFixed(1) + 'deg)';
      }
    }
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

  function routeStopNumber(pinId) {
    if (!S.routeActive || !S.routePins.length || S.routeMode !== 'tour') return 0;
    for (var i = 0; i < S.routePins.length; i++) {
      if (S.routePins[i].id === pinId) return i + 1;
    }
    return 0;
  }

  var GAME_ICON_CATS = {
    mystic_gateway: true, shop: true, favor: true, yggdrasil_rift: true,
    hel_tear: true, berserker_gravestone: true, remnant_of_asgard: true,
    remnants_of_asgard: true, boss: true, boat_dock: true, entrance: true,
    muspelheim_trial: true, celestial_altar: true, kol_raider_camp: true,
    draugr_hole: true, seasonal_stag: true, wishing_well: true
  };

  function probeGameMapIcons() {
    if (S.gameMapIconsChecked) return;
    S.gameMapIconsChecked = true;
    var img = new Image();
    img.onload = function () {
      if (img.naturalWidth > 16) {
        S.gameMapIconsReady = true;
        if (S.data) renderMarkers();
      }
    };
    img.src = '/api/map-icon/mystic_gateway.png?v=' + ASSET_REV;
  }

  function updateRegionLabels() {
    if (!map || !map.setRegionLabels || !S.data) return;
    var pois = S.data.realms_map.realm_pois || [];
    var buckets = {};
    pois.forEach(function (p) {
      if (!p.region || p.lat == null || p.lng == null) return;
      if (S.region && p.region !== S.region) return;
      (buckets[p.region] || (buckets[p.region] = [])).push(p);
    });
    var labels = Object.keys(buckets).map(function (name) {
      var arr = buckets[name];
      if (arr.length < 3 && Object.keys(buckets).length > 3) return null;
      var lats = arr.map(function (p) { return p.lat; }).sort(function (a, b) { return a - b; });
      var lngs = arr.map(function (p) { return p.lng; }).sort(function (a, b) { return a - b; });
      var mid = Math.floor(lats.length / 2);
      return { name: name, lat: lats[mid], lng: lngs[mid], major: arr.length >= 10, count: arr.length };
    }).filter(Boolean).sort(function (a, b) { return b.count - a.count; });
    map.setRegionLabels(labels);
  }

  function markerIcon(p) {
    var st = poiState(p);
    if (S.mode === 'favors') st = favorPinState(p) === 'not_collected' ? 'remaining' : favorPinState(p);
    var cs = catStyle(p.category_key);
    var useGameIc = S.gameMapIconsReady && !!GAME_ICON_CATS[p.category_key];
    var size = useGameIc ? 36 : (st === 'resource' ? 24 : 32);
    var stepNo = routeStopNumber(p.id);
    var isTarget = S.routeActive && S.routeMode === 'single' && S.routeTarget && S.routeTarget.pinId === p.id;
    var isOrigin = S.routeActive && S.routeOriginInfo && S.routeOriginInfo.pinId === p.id;
    var isGw = p.category_key === 'mystic_gateway';
    var gameIconKey = (isGw && st === 'remaining') ? 'mystic_gateway_unvisited' : p.category_key;
    var inner = useGameIc
      ? '<div class="gow-pin-plate is-game-icon" style="--pin:' + cs.c + '"><img class="gow-pin-game-img" src="/api/map-icon/' +
          encodeURIComponent(gameIconKey) + '.png?v=' + ASSET_REV + '" alt="" draggable="false" />' +
          (stepNo ? '<em class="gow-pin-step">' + stepNo + '</em>' : '') + '</div>'
      : '<div class="gow-pin-plate" style="--pin:' + cs.c + '">' + catGlyph(p.category_key) +
          (stepNo ? '<em class="gow-pin-step">' + stepNo + '</em>' : '') + '</div>';
    return L.divIcon({
      className: 'gow-pin gow-pin--' + st + (S.mode === 'favors' ? ' gow-pin--favor' : '') +
        (useGameIc ? ' has-game-icon' : '') +
        (isGw ? ' gow-pin--gateway' : '') +
        (stepNo ? ' is-route-stop' : '') +
        (isTarget ? ' is-route-target' : '') +
        (isOrigin ? ' is-route-origin' : '') +
        (p.id === S.selectedId ? ' is-selected' : ''),
      iconSize: [size, size],
      iconAnchor: [size / 2, size / 2],
      html: inner
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
    updateRegionLabels();
    probeGameMapIcons();
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
    if (map.pushTrailPoint) map.pushTrailPoint(r.map_lat, r.map_lng);
    var el = kratosMarker.getElement();
    if (el) {
      el.classList.toggle('no-yaw', yaw == null);
      el.classList.toggle('is-approx', projConfidence(r) === 'approximate');
      var rot = el.querySelector('.gow-kratos-rot');
      if (rot && yaw != null) {
        
        var prev = S.lastYaw == null ? yaw : S.lastYaw;
        var d = ((yaw - prev) % 360 + 540) % 360 - 180;
        S.lastYaw = prev + d;
        rot.style.transform = 'rotate(' + (S.lastYaw + ((map && map.yawDeg) || 0)).toFixed(1) + 'deg)';
      }
    }
    renderBeaconPill();
    if (S.routeActive) refreshLiveRoute();
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
    var actTab = $('gowFsRealmTabs').querySelector('.gow-fs-realm-tab.active');
    if (actTab && actTab.scrollIntoView) {
      try { actTab.scrollIntoView({ behavior: 'smooth', inline: 'nearest', block: 'nearest' }); }
      catch (e) { actTab.scrollIntoView(false); }
    }
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

  function persistGuideSeen() {
    clearTimeout(S.guideSeenTimer);
    S.guideSeenTimer = null;
    try { sessionStorage.setItem('gowGuideSeen', JSON.stringify(S.guideSeen)); } catch (e) {}
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
        persistGuideSeen();
        if (item.favor) { focusGuidePoint(item.favor.id, item.index); }
        else { if (S.mode === 'favors') setMode('remaining'); focusPin(item.pin.id); }
      };
      el.querySelector('[data-guide-dismiss]').onclick = function () { persistGuideSeen(); el.hidden = true; S.guideToast = null; };
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
    clearTimeout(S.guideSeenTimer);
    S.guideSeenTimer = setTimeout(persistGuideSeen, 600);
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

  function beaconOrigin() {
    var r = liveRadar(S.data && S.data.live_telemetry);
    if (r && (r.realm_key || S.realm) === S.realmLoaded) return [r.map_lat, r.map_lng];
    if (map && map.center) return map.center;
    var rm = S.data && S.data.realms_map;
    return rm && rm.center_lat != null ? [rm.center_lat, rm.center_lng] : [0.7, -0.7];
  }

  function pinBearing(lat, lng) {
    var ref = beaconOrigin();
    var dLat = lat - ref[0], dLng = lng - ref[1];
    var deg = (Math.atan2(dLng, dLat) * 180 / Math.PI + 360) % 360;
    var dirs = ['dir_n', 'dir_ne', 'dir_e', 'dir_se', 'dir_s', 'dir_sw', 'dir_w', 'dir_nw'];
    var dir = tr(dirs[Math.round(deg / 45) % 8]);
    var r = liveRadar(S.data && S.data.live_telemetry);
    var scale = (r && (r.realm_key || S.realm) === S.realmLoaded && r.map_scale_per_metre)
      || (S.data && S.data.realms_map && S.data.realms_map.map_scale_per_metre);
    var metres = (typeof scale === 'number' && scale > 0) ? Math.round(Math.hypot(dLat, dLng) / scale) : null;
    return { metres: metres, dir: dir };
  }

  function renderBeaconPill() {
    var pill = $('gowFsBeaconPill');
    if (!pill) return;
    if (!S.beaconTarget) { pill.hidden = true; return; }
    var r = liveRadar(S.data && S.data.live_telemetry);
    var kratosHere = r && (r.realm_key || S.realm) === S.realmLoaded;
    var info = pinBearing(S.beaconTarget.lat, S.beaconTarget.lng);
    var distText = (kratosHere || info.metres == null || info.metres >= 5)
      ? (info.metres != null ? info.metres + tr('s054') + ' ' : '') + info.dir
      : '';
    $('gowFsBeaconDist').textContent = distText;
    $('gowFsBeaconDist').hidden = !distText;
    $('gowFsBeaconName').textContent = S.beaconTarget.label || '';
    var dot = $('gowFsBeaconDot');
    if (dot) {
      dot.style.background = S.beaconTarget.color || '#e5c378';
      dot.style.boxShadow = '0 0 10px ' + (S.beaconTarget.color || '#e5c378');
    }
    pill.hidden = false;
  }

  function setBeacon(lat, lng, label, colorHex, pinId, keepAuto) {
    if (lat == null || lng == null) { clearBeacon(); return; }
    S.beaconPinId = pinId || null;
    S.beaconTarget = { lat: Number(lat), lng: Number(lng), label: label || '', color: colorHex || '#e5c378' };
    if (!keepAuto) S.autoAdvanceBeacon = false;
    if (map && map.setWaypoint) map.setWaypoint(S.beaconTarget.lat, S.beaconTarget.lng, S.beaconTarget.color);
    renderBeaconPill();
  }

  function clearBeacon() {
    S.beaconPinId = null;
    S.beaconTarget = null;
    S.autoAdvanceBeacon = false;
    if (map && map.setWaypoint) map.setWaypoint(null, null);
    renderBeaconPill();
  }

  function findNearestMissingPin(excludeId) {
    var pois = (S.data && S.data.realms_map && S.data.realms_map.realm_pois) || [];
    var origin = beaconOrigin();
    function collect(excl, visibleOnly) {
      return pois.filter(function (p) {
        if ((excl && p.id === excl) || p.lat == null || p.lng == null) return false;
        var st = poiState(p);
        return p.is_completionist && (st === 'remaining' || st === 'unknown') && (!visibleOnly || isVisible(p));
      });
    }
    var pool = collect(excludeId, true);
    if (!pool.length) pool = collect(excludeId, false);
    if (!pool.length && excludeId) pool = collect(null, false);
    if (!pool.length) return null;
    var best = null, bd = Infinity;
    for (var i = 0; i < pool.length; i++) {
      var p = pool[i];
      var d2 = (p.lat - origin[0]) * (p.lat - origin[0]) + (p.lng - origin[1]) * (p.lng - origin[1]);
      if (d2 < bd) { bd = d2; best = p; }
    }
    return best;
  }

  function jumpToNearestMissing(silent) {
    var pin = findNearestMissingPin(S.beaconPinId);
    if (!pin) {
      clearBeacon();
      if (!silent) setStatus(tr('nearest_done'));
      return;
    }
    S.autoAdvanceBeacon = true;
    S.follow = false; $('gowFsFollow').classList.remove('on'); savePrefs();
    if (!markerById[pin.id]) {
      S.category = null; S.region = ''; S.query = ''; $('gowFsSearch').value = '';
      if ($('gowFsSearchClear')) $('gowFsSearchClear').hidden = true;
      if (S.mode === 'favors') setMode('remaining');
      else rerender();
    }
    if (map) map.flyTo([pin.lat, pin.lng], Math.max(map.getZoom(), 12.5), { duration: 0.6 });
    openDrawer(pin.id, true);
  }

  function mapScalePerMetre() {
    var r = liveRadar(S.data && S.data.live_telemetry);
    if (r && (r.realm_key || S.realm) === S.realmLoaded && typeof r.map_scale_per_metre === 'number' && r.map_scale_per_metre > 0) {
      return r.map_scale_per_metre;
    }
    var rm = S.data && S.data.realms_map;
    if (rm && typeof rm.map_scale_per_metre === 'number' && rm.map_scale_per_metre > 0) return rm.map_scale_per_metre;
    return null;
  }

  function resolveRouteOrigin(targetLat, targetLng, excludePinId) {
    var r = liveRadar(S.data && S.data.live_telemetry);
    if (r && (r.realm_key || S.realm) === S.realmLoaded) {
      return { kind: 'kratos', lat: r.map_lat, lng: r.map_lng, name: tr('route_from_kratos'), pinId: null };
    }
    var pois = (S.data && S.data.realms_map && S.data.realms_map.realm_pois) || [];
    var gateways = pois.filter(function (p) {
      return p.category_key === 'mystic_gateway' && p.lat != null && p.lng != null && p.id !== excludePinId;
    });
    if (gateways.length) {
      var unlockedGw = gateways.filter(function (p) { return poiState(p) === 'collected'; });
      var pool = unlockedGw.length ? unlockedGw : gateways;
      var refLat = targetLat != null ? targetLat : ((map && map.center && map.center[0]) || 0);
      var refLng = targetLng != null ? targetLng : ((map && map.center && map.center[1]) || 0);
      var best = null, bd = Infinity;
      for (var i = 0; i < pool.length; i++) {
        var d = Math.hypot(pool[i].lat - refLat, pool[i].lng - refLng);
        if (d < bd) { bd = d; best = pool[i]; }
      }
      if (best) {
        return { kind: 'gateway', lat: best.lat, lng: best.lng, name: best.name || 'Mystic Gateway', pinId: best.id };
      }
    }
    var rm = S.data && S.data.realms_map;
    var c = (rm && rm.center_lat != null) ? [rm.center_lat, rm.center_lng]
      : ((map && map.center) ? [map.center[0], map.center[1]] : [0.7, -0.7]);
    return { kind: 'center', lat: c[0], lng: c[1], name: '', pinId: null };
  }

  function renderRoutePill() {
    var pill = $('gowFsRoutePill');
    var btn = $('gowFsRoute');
    if (btn) btn.classList.toggle('on', S.routeActive);
    if (!pill) return;
    if (!S.routeActive || (!S.routePins.length && !S.routeTarget)) { pill.hidden = true; return; }
    var distTxt = S.routeMetres != null ? (S.routeMetres + tr('s054')) : '';
    if (S.routeMode === 'single' && S.routeTarget) {
      $('gowFsRouteLabel').textContent = S.routeTarget.label || tr('route_pill_title');
      var originTxt = '';
      if (S.routeOriginInfo && S.routeOriginInfo.kind === 'kratos') {
        originTxt = tr('route_from_kratos');
      } else if (S.routeOriginInfo && S.routeOriginInfo.kind === 'gateway') {
        originTxt = tr('route_from_gateway').replace('{name}', S.routeOriginInfo.name);
      }
      var parts = [originTxt, distTxt].filter(Boolean);
      $('gowFsRouteMeta').textContent = parts.join(' · ');
    } else {
      $('gowFsRouteLabel').textContent = tr('route_pill_title');
      var stopsTxt = tr('route_stops').replace('{n}', String(S.routePins.length));
      $('gowFsRouteMeta').textContent = distTxt ? (stopsTxt + ' · ' + distTxt) : stopsTxt;
    }
    pill.hidden = false;
  }

  function refreshRoutePinIcons(ids) {
    var seen = {};
    (ids || []).forEach(function (id) {
      if (!id || seen[id]) return;
      seen[id] = true;
      var q = findPoi(id);
      if (q && markerById[id]) markerById[id].setIcon(markerIcon(q));
    });
  }

  function clearClearingRoute() {
    var prevIds = S.routePins.map(function (p) { return p.id; });
    if (S.routeTarget && S.routeTarget.pinId) prevIds.push(S.routeTarget.pinId);
    if (S.routeOriginInfo && S.routeOriginInfo.pinId) prevIds.push(S.routeOriginInfo.pinId);
    var firstId = S.routePins.length ? S.routePins[0].id : (S.routeTarget && S.routeTarget.pinId);
    S.routeActive = false;
    S.routeMode = null;
    S.routeTarget = null;
    S.routeOriginInfo = null;
    S.routePins = [];
    S.routeMetres = null;
    if (map && map.setRoute) map.setRoute([]);
    if (firstId && S.beaconPinId === firstId) clearBeacon();
    refreshRoutePinIcons(prevIds);
    renderRoutePill();
  }

  function ensurePinVisibleForRoute(p) {
    if (!p || markerById[p.id]) return;
    S.category = null;
    S.region = '';
    S.query = '';
    if ($('gowFsSearch')) $('gowFsSearch').value = '';
    if ($('gowFsSearchClear')) $('gowFsSearchClear').hidden = true;
    var st = poiState(p);
    var needMode = S.mode;
    if (S.mode === 'favors' && !favorPinState(p)) needMode = st === 'resource' ? 'all' : (st === 'collected' ? 'scored' : 'remaining');
    else if (S.mode === 'remaining' && (st === 'collected' || !p.is_completionist)) needMode = p.is_completionist ? 'scored' : 'all';
    else if (S.mode === 'scored' && !p.is_completionist) needMode = 'all';
    if (needMode !== S.mode) {
      S.mode = needMode;
      savePrefs();
      renderModeMenu();
    }
    rerender();
  }

  function routeToTarget(spec) {
    if (!spec) return false;
    var targetRealm = spec.realm || null;
    if (targetRealm && targetRealm !== S.realmLoaded) {
      S.pendingRoute = spec;
      S.follow = false;
      if ($('gowFsFollow')) $('gowFsFollow').classList.remove('on');
      savePrefs();
      switchGowRealm(targetRealm);
      return true;
    }
    var targetPin = spec.pinId ? findPoi(spec.pinId) : null;
    var tLat = targetPin ? targetPin.lat : spec.lat;
    var tLng = targetPin ? targetPin.lng : spec.lng;
    if (tLat == null || tLng == null) return false;
    var label = spec.label || (targetPin ? favorPinName(targetPin) : '') || tr('s069');
    var color = spec.color || (targetPin ? catStyle(targetPin.category_key).c : '#f0cf7a');

    S.follow = false;
    if ($('gowFsFollow')) $('gowFsFollow').classList.remove('on');
    savePrefs();

    if (targetPin) ensurePinVisibleForRoute(targetPin);

    var prevIds = S.routePins.map(function (p) { return p.id; });
    if (S.routeTarget && S.routeTarget.pinId) prevIds.push(S.routeTarget.pinId);
    if (S.routeOriginInfo && S.routeOriginInfo.pinId) prevIds.push(S.routeOriginInfo.pinId);

    var origin = resolveRouteOrigin(tLat, tLng, targetPin ? targetPin.id : null);
    var distDeg = Math.hypot(tLat - origin.lat, tLng - origin.lng);
    var scale = mapScalePerMetre();
    var metres = scale ? Math.round(distDeg / scale) : null;

    S.routeActive = true;
    S.routeMode = 'single';
    S.routeTarget = {
      lat: Number(tLat), lng: Number(tLng), label: label, color: color,
      pinId: targetPin ? targetPin.id : null, realm: S.realmLoaded
    };
    S.routeOriginInfo = origin;
    S.routePins = targetPin ? [targetPin] : [];
    S.routeMetres = metres;

    var routePts = [{ lat: origin.lat, lng: origin.lng }, { lat: Number(tLat), lng: Number(tLng) }];
    if (map && map.setRoute) map.setRoute(routePts, color || '#f0cf7a');
    setBeacon(tLat, tLng, label, color, targetPin ? targetPin.id : null, false);

    if (targetPin) prevIds.push(targetPin.id);
    if (origin.pinId) prevIds.push(origin.pinId);
    refreshRoutePinIcons(prevIds);
    renderRoutePill();

    if (spec.openDrawer && targetPin) openDrawer(targetPin.id);

    if (spec.fitView !== false && map) {
      if (distDeg < 0.015) {
        map.flyTo([Number(tLat), Number(tLng)], Math.max(map.getZoom(), 13), { duration: 0.6 });
      } else {
        var o = hudPadding();
        if (spec.openDrawer) o.paddingBottomRight = [Math.min(460, window.innerWidth * 0.38), 70];
        o.maxZoom = 13;
        o.duration = 0.6;
        map.flyToBounds(L.latLngBounds([[origin.lat, origin.lng], [Number(tLat), Number(tLng)]]).pad(0.22), o);
      }
    }
    return true;
  }

  function refreshLiveRoute() {
    if (!S.routeActive || !map || !map.setRoute) return;
    var r = liveRadar(S.data && S.data.live_telemetry);
    if (!r || (r.realm_key || S.realm) !== S.realmLoaded) return;
    var scale = mapScalePerMetre();
    if (S.routeMode === 'single' && S.routeTarget) {
      var prevOriginPin = S.routeOriginInfo && S.routeOriginInfo.pinId;
      S.routeOriginInfo = { kind: 'kratos', lat: r.map_lat, lng: r.map_lng, name: tr('route_from_kratos'), pinId: null };
      var distDeg = Math.hypot(S.routeTarget.lat - r.map_lat, S.routeTarget.lng - r.map_lng);
      S.routeMetres = scale ? Math.round(distDeg / scale) : null;
      map.setRoute([{ lat: r.map_lat, lng: r.map_lng }, { lat: S.routeTarget.lat, lng: S.routeTarget.lng }], S.routeTarget.color || '#f0cf7a');
      if (prevOriginPin) refreshRoutePinIcons([prevOriginPin]);
      renderRoutePill();
    } else if (S.routeMode === 'tour' && S.routePins.length) {
      var pts = [{ lat: r.map_lat, lng: r.map_lng }].concat(S.routePins.map(function (p) { return { lat: p.lat, lng: p.lng }; }));
      var totalDeg = 0;
      for (var i = 1; i < pts.length; i++) totalDeg += Math.hypot(pts[i].lat - pts[i - 1].lat, pts[i].lng - pts[i - 1].lng);
      S.routeOriginInfo = { kind: 'kratos', lat: r.map_lat, lng: r.map_lng, name: tr('route_from_kratos'), pinId: null };
      S.routeMetres = scale ? Math.round(totalDeg / scale) : null;
      map.setRoute(pts, '#f0cf7a');
      renderRoutePill();
    }
  }

  function buildClearingRoute(fitView) {
    var pois = (S.data && S.data.realms_map && S.data.realms_map.realm_pois) || [];
    var pool = pois.filter(function (p) {
      if (p.lat == null || p.lng == null) return false;
      var st = poiState(p);
      return p.is_completionist && (st === 'remaining' || st === 'unknown') && isVisible(p);
    });
    if (!pool.length) {
      pool = pois.filter(function (p) {
        if (p.lat == null || p.lng == null) return false;
        var st = poiState(p);
        return p.is_completionist && (st === 'remaining' || st === 'unknown');
      });
    }
    if (!pool.length) {
      clearClearingRoute();
      if (fitView) setStatus(tr('route_none'));
      return;
    }
    var origin = resolveRouteOrigin(null, null, null);
    var cur = [origin.lat, origin.lng];
    var rem = pool.slice();
    var chosen = [];
    var totalDeg = 0;
    var limit = Math.min(5, rem.length);
    for (var step = 0; step < limit; step++) {
      var bestIdx = 0, bestD = Infinity;
      for (var i = 0; i < rem.length; i++) {
        var d = Math.hypot(rem[i].lat - cur[0], rem[i].lng - cur[1]);
        if (d < bestD) { bestD = d; bestIdx = i; }
      }
      var picked = rem.splice(bestIdx, 1)[0];
      chosen.push(picked);
      totalDeg += bestD;
      cur = [picked.lat, picked.lng];
    }
    var prevIds = S.routePins.map(function (p) { return p.id; });
    if (S.routeTarget && S.routeTarget.pinId) prevIds.push(S.routeTarget.pinId);
    if (S.routeOriginInfo && S.routeOriginInfo.pinId) prevIds.push(S.routeOriginInfo.pinId);
    S.routeActive = true;
    S.routeMode = 'tour';
    S.routeTarget = null;
    S.routeOriginInfo = origin;
    S.routePins = chosen;
    var scale = mapScalePerMetre();
    S.routeMetres = scale ? Math.round(totalDeg / scale) : null;
    var routePts = [{ lat: origin.lat, lng: origin.lng }].concat(chosen.map(function (p) {
      return { lat: p.lat, lng: p.lng };
    }));
    if (map && map.setRoute) map.setRoute(routePts, '#f0cf7a');
    var first = chosen[0];
    setBeacon(first.lat, first.lng, favorPinName(first) || tr('s069'), catStyle(first.category_key).c, first.id, true);
    S.autoAdvanceBeacon = true;
    refreshRoutePinIcons(prevIds.concat(chosen.map(function (p) { return p.id; }), origin.pinId ? [origin.pinId] : []));
    renderRoutePill();
    if (fitView && map) {
      var boundsPts = routePts.map(function (pt) { return [pt.lat, pt.lng]; });
      var o = hudPadding();
      o.maxZoom = 13;
      o.duration = 0.6;
      map.flyToBounds(L.latLngBounds(boundsPts).pad(0.14), o);
    }
  }

  function toggleClearingRoute() {
    if (S.routeActive && S.routeMode === 'tour') clearClearingRoute();
    else buildClearingRoute(true);
  }

  function updateWakeButton() {
    var b = $('gowFsWake');
    if (!b) return;
    b.classList.toggle('on', S.wakeLockOn);
    b.title = S.wakeLockOn ? tr('ctl_wake_on') : tr('ctl_wake');
  }

  function acquireWakeLock(silent) {
    if (!navigator.wakeLock || !navigator.wakeLock.request) {
      S.wakeLockOn = false;
      updateWakeButton();
      if (!silent) setStatus(tr('ctl_wake_unavail'), 'warn');
      return;
    }
    navigator.wakeLock.request('screen').then(function (sentinel) {
      S.wakeSentinel = sentinel;
      S.wakeLockOn = true;
      updateWakeButton();
      sentinel.addEventListener('release', function () {
        S.wakeSentinel = null;
        if (document.visibilityState === 'visible' && S.wakeLockOn) {
          S.wakeLockOn = false;
          updateWakeButton();
        }
      });
    }).catch(function () {
      S.wakeLockOn = false;
      updateWakeButton();
      if (!silent) setStatus(tr('ctl_wake_unavail'), 'warn');
    });
  }

  function releaseWakeLock() {
    S.wakeLockOn = false;
    if (S.wakeSentinel) {
      try { S.wakeSentinel.release(); } catch (e) {}
      S.wakeSentinel = null;
    }
    updateWakeButton();
  }

  function toggleWakeLock() {
    if (S.wakeLockOn) releaseWakeLock();
    else acquireWakeLock(false);
  }

  function findCodexMatchForPin(p) {
    if (!p || !S.codex) return null;
    var allowedCats = { boss: 1, berserker_gravestone: 1, sleeping_troll: 1, draugr_hole: 1, kol_raider_camp: 1 };
    if (!allowedCats[p.category_key]) return null;
    var norm = function (s) { return String(s || '').toLowerCase().replace(/[^a-z0-9\u0400-\u04ff]+/g, ' ').trim(); };
    var wordHit = function (shortStr, longStr) {
      if (shortStr.length < 4) return false;
      var padded = ' ' + longStr + ' ';
      return padded.indexOf(' ' + shortStr + ' ') >= 0;
    };
    var target = norm(p.name);
    if (!target || target.length < 3) return null;
    var secs = [['bestiary', S.codex.bestiary || []], ['lore', S.codex.lore || []]];
    var partial = null;
    for (var si = 0; si < secs.length; si++) {
      var tab = secs[si][0], list = secs[si][1];
      for (var i = 0; i < list.length; i++) {
        var b = list[i];
        if (b.is_valhalla) continue;
        var bn = norm(b.name);
        if (!bn || bn.length < 3) continue;
        if (bn === target) return { tab: tab, entry: b };
        if (!partial && (wordHit(bn, target) || wordHit(target, bn))) partial = { tab: tab, entry: b };
      }
    }
    return partial;
  }

  function findTreasureForPin(p) {
    if (!p || !S.codex || !(S.codex.treasures && S.codex.treasures.length)) return null;
    if (p.category_key !== 'treasure_map' && p.category_key !== 'buried_treasure') return null;
    var list = S.codex.treasures;
    for (var i = 0; i < list.length; i++) {
      var t = list[i];
      if ((t.map_pin && t.map_pin.id === p.id) || (t.dig_pin && t.dig_pin.id === p.id)) return t;
    }
    var norm = function (s) { return String(s || '').toLowerCase().replace(/[^a-z0-9\u0400-\u04ff]+/g, ' ').trim(); };
    var pn = norm(p.name);
    for (var j = 0; j < list.length; j++) {
      var tn = norm(list[j].name);
      if (tn && (pn === tn || pn.indexOf(tn) >= 0 || tn.indexOf(pn) >= 0)) return list[j];
    }
    return null;
  }

  function openDrawer(id, keepAuto) {
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
    setBeacon(p.lat, p.lng, favorPinName(p) || tr('s069'), cs.c, p.id, keepAuto || (S.beaconPinId === p.id && S.autoAdvanceBeacon));
    var bearing = pinBearing(p.lat, p.lng);
    var distSuffix = bearing.metres != null ? ' · ' + bearing.metres + tr('s054') + ' ' + bearing.dir : ' · ' + bearing.dir;
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
    var codexMatch = findCodexMatchForPin(p);
    var trMatch = findTreasureForPin(p);
    var routeActionsHtml =
      '<div class="gow-fs-drawer-actions">' +
        '<button type="button" class="gow-fs-btn gow-fs-route-btn" id="gowFsRouteHere" data-route-pin="' + esc(p.id) + '" data-route-realm="' + esc(S.realmLoaded || '') + '">' +
          GOW_SVG.route + '<span>' + esc(tr('route_here')) + '</span></button>';
    if (trMatch) {
      if (p.category_key === 'treasure_map' && trMatch.dig_pin) {
        routeActionsHtml += '<button type="button" class="gow-fs-btn gow-fs-route-btn is-gold" data-route-pin="' + esc(trMatch.dig_pin.id) + '" data-route-realm="' + esc(trMatch.dig_pin.realm) + '">' +
          GOW_SVG.treasure + '<span>' + esc(tr('route_to_dig')) + ' · ' + esc(trMatch.dig_pin.realm_name || REALM_SHORT[trMatch.dig_pin.realm] || '') + '</span></button>';
      } else if (p.category_key === 'buried_treasure' && trMatch.map_pin) {
        routeActionsHtml += '<button type="button" class="gow-fs-btn gow-fs-route-btn" data-route-pin="' + esc(trMatch.map_pin.id) + '" data-route-realm="' + esc(trMatch.map_pin.realm) + '">' +
          GOW_SVG.treasure + '<span>' + esc(tr('route_to_map')) + ' · ' + esc(trMatch.map_pin.realm_name || REALM_SHORT[trMatch.map_pin.realm] || '') + '</span></button>';
      }
      routeActionsHtml += '<button type="button" class="gow-fs-btn gow-fs-bestiary-link" data-open-codex-tab="treasures" data-open-bestiary="' + esc(trMatch.id) + '">' +
        GOW_SVG.book_open + '<span>' + esc(tr('open_in_treasures')) + ' · ' + esc(trMatch.name) + '</span></button>';
    }
    if (codexMatch) {
      routeActionsHtml += '<button type="button" class="gow-fs-btn gow-fs-bestiary-link" data-open-codex-tab="' + esc(codexMatch.tab) + '" data-open-bestiary="' + esc(codexMatch.entry.id) + '">' +
        GOW_SVG.book + '<span>' + esc(tr(codexMatch.tab === 'bestiary' ? 'open_in_bestiary' : 'open_in_codex')) + ' · ' + esc(codexMatch.entry.name) + '</span></button>';
    }
    routeActionsHtml += '</div>';
    var treasureClueHtml = (trMatch && trMatch.icon)
      ? '<button type="button" class="gow-fs-shot gow-fs-tr-clue" data-src="' + esc(trMatch.icon) + '"><img src="' + esc(trMatch.icon) + '" alt="" loading="lazy" /></button>'
      : '';
    var drawerHtml =
      '<div class="gow-fs-drawer-cat" style="--pin:' + cs.c + '"><span class="gow-fs-drawer-glyph">' + catGlyph(p.category_key) +
        '</span><span>' + esc(p.category || '') + '</span></div>' +
      '<h2 class="gow-fs-drawer-title" id="gowFsDrawerTitle">' + esc(favorPinName(p) || tr('s069')) + '</h2>' +
      (p.region ? '<div class="gow-fs-drawer-region">' + esc(p.region) + '</div>' : '') +
      (p.artifact ? tr('s070') + esc(p.artifact) + '</div>' : '') +
      '<div class="gow-fs-drawer-status is-' + st + '">' + (st === 'collected' ? GOW_SVG.check : GOW_SVG.dot) +
        '<span>' + statusText + distSuffix + '</span></div>' +
      routeActionsHtml +
      treasureClueHtml +
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

  function updateCodexBadge() {
    var badge = $('gowFsCodexBadge');
    if (!badge) return;
    var sum = (S.codex && S.codex.summary) || (S.data && S.data.codex_summary) || {};
    var tot = S.codexValhalla ? sum.bestiary_total : (sum.bestiary_main_total || sum.bestiary_total);
    var unl = S.codexValhalla ? sum.bestiary_unlocked : (sum.bestiary_main_unlocked != null ? sum.bestiary_main_unlocked : sum.bestiary_unlocked);
    var hasNew = Object.keys(S.codexNewIds).length > 0;
    if (tot > 0) {
      badge.textContent = (unl || 0) + '/' + tot;
      badge.hidden = false;
      badge.classList.toggle('has-new', hasNew);
    } else if (hasNew) {
      badge.textContent = tr('codex_new_badge');
      badge.hidden = false;
      badge.classList.add('has-new');
    } else {
      badge.hidden = true;
    }
  }

  function fetchCodex(silent) {
    if (S.codexLoading) return Promise.resolve(S.codex);
    S.codexLoading = true;
    return fetch('/api/codex?lang=' + window.GowI18n.lang, { cache: 'no-store' })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) {
        if (d && d.ok) {
          S.codex = d;
          updateCodexBadge();
          if ($('gowFsCodexModal').classList.contains('open')) renderCodex();
          if (S.selectedId && $('gowFsRightDrawer').classList.contains('open')) openDrawer(S.selectedId);
        }
        return d;
      })
      .catch(function () { return null; })
      .then(function (d) { S.codexLoading = false; return d; });
  }

  function showCodexToast(text, action) {
    var toast = $('gowCodexToast');
    if (!toast || !text) return;
    S.codexToastAction = action || null;
    $('gowCodexToastText').textContent = text;
    toast.hidden = false;
    clearTimeout(S.codexToastTimer);
    S.codexToastTimer = setTimeout(function () { toast.hidden = true; }, 9000);
  }

  function handleCodexDelta(delta) {
    if (!delta || !delta.has_changes) return;
    var firstMsg = null, firstAct = null;
    (delta.new_bestiary || []).forEach(function (item) {
      S.codexNewIds[item.id] = true;
      if (!firstMsg) {
        firstMsg = tr('codex_toast_bestiary').replace('{name}', item.name || item.id);
        firstAct = { tab: 'bestiary', id: item.id };
      }
    });
    (delta.new_tips || []).forEach(function (item) {
      S.codexNewIds[item.entry_id] = true;
      if (!firstMsg) {
        firstMsg = tr('codex_toast_tip').replace('{name}', item.entry_name || item.entry_id);
        firstAct = { tab: 'bestiary', id: item.entry_id };
      }
    });
    (delta.new_lore || []).forEach(function (item) {
      S.codexNewIds[item.id] = true;
      if (!firstMsg) {
        firstMsg = tr('codex_toast_lore').replace('{name}', item.name || item.id);
        firstAct = { tab: 'lore', id: item.id };
      }
    });
    (delta.new_treasures || []).forEach(function (item) {
      S.codexNewIds[item.id] = true;
      if (!firstMsg) {
        firstMsg = tr('codex_toast_treasure').replace('{name}', item.name || item.id);
        firstAct = { tab: 'treasures', id: item.id };
      }
    });
    (delta.skill_updates || []).forEach(function (item) {
      S.codexNewIds[item.id] = true;
      if (!firstMsg) {
        firstMsg = tr('codex_toast_skill').replace('{name}', item.name || item.id);
        firstAct = { tab: 'skills', id: item.id };
      }
    });
    updateCodexBadge();
    if (firstMsg) showCodexToast(firstMsg, firstAct);
    fetchCodex(true);
  }

  function connectStream() {
    if (typeof EventSource === 'undefined' || S.sse) return;
    try {
      var es = new EventSource('/api/stream?lang=' + window.GowI18n.lang);
      S.sse = es;
      es.addEventListener('hello', function (ev) {
        S.codexLive = true;
        try {
          var payload = JSON.parse(ev.data);
          if (payload.codex_summary && S.data) {
            S.data.codex_summary = payload.codex_summary;
            updateCodexBadge();
          }
          var liveEl = $('gowCodexLivePill');
          if (liveEl) liveEl.classList.add('is-live');
        } catch (e) {}
      });
      es.addEventListener('telemetry', function (ev) {
        try {
          var payload = JSON.parse(ev.data);
          if (S.data && payload.live_telemetry) {
            S.lastTelemetryAt = Date.now();
            S.data.live_telemetry = payload.live_telemetry;
            updateKratos(payload.live_telemetry);
            renderStatus();
            updateGuideToast();
            autoSwitchRealm(payload.live_telemetry);
          }
        } catch (e) {}
      });
      es.addEventListener('save_updated', function (ev) {
        refresh();
        fetchCodex(true);
      });
      es.addEventListener('codex_delta', function (ev) {
        try { handleCodexDelta(JSON.parse(ev.data)); } catch (e) {}
      });
      es.onerror = function () {
        S.codexLive = false;
        var liveEl = $('gowCodexLivePill');
        if (liveEl) liveEl.classList.remove('is-live');
      };
    } catch (e) { S.sse = null; }
  }

  function isEntryMasked(entry) {
    return S.codexSpoiler && !entry.unlocked && !S.codexRevealed[entry.id];
  }

  function filteredCodexEntries(kind) {
    var c = S.codex || {};
    var q = S.codexQuery.trim().toLowerCase();
    if (kind === 'treasures') {
      var tsrc = c.treasures || [];
      var tout = tsrc.filter(function (e) {
        if (S.treasureFilter !== 'all' && e.status !== S.treasureFilter) return false;
        if (q) {
          var maskedT = isEntryMasked(e);
          var hayT = ((maskedT ? '' : e.name) + ' ' + (maskedT ? '' : (e.description || '')) + ' ' +
            ((e.map_pin && e.map_pin.realm_name) || '') + ' ' + ((e.dig_pin && e.dig_pin.realm_name) || '')).toLowerCase();
          if (hayT.indexOf(q) < 0) return false;
        }
        return true;
      });
      var order = { active: 0, dug: 1, unfound: 2 };
      tout.sort(function (a, b) {
        if (S.codexSort === 'alpha') {
          var na = isEntryMasked(a) ? 'zzz' : a.name;
          var nb = isEntryMasked(b) ? 'zzz' : b.name;
          return na.localeCompare(nb, window.GowI18n.lang);
        }
        var oa = order[a.status] != null ? order[a.status] : 9;
        var ob = order[b.status] != null ? order[b.status] : 9;
        if (oa !== ob) return oa - ob;
        return (a.name || '').localeCompare(b.name || '', window.GowI18n.lang);
      });
      return tout;
    }
    var src = kind === 'lore' ? (c.lore || []) : (c.bestiary || []);
    var out = src.filter(function (e) {
      if (!S.codexValhalla && e.is_valhalla) return false;
      if (S.codexCat && e.category !== S.codexCat) return false;
      if (S.codexStatus === 'unlocked' && !e.unlocked) return false;
      if (S.codexStatus === 'locked' && e.unlocked) return false;
      if (S.codexStatus === 'new' && !S.codexNewIds[e.id]) return false;
      if (q) {
        var masked = isEntryMasked(e);
        var hay = ((masked ? '' : e.name) + ' ' + e.category + ' ' + (masked ? '' : (e.description || ''))).toLowerCase();
        if (!masked && e.tips) hay += ' ' + e.tips.map(function (t) { return t.text || ''; }).join(' ').toLowerCase();
        if (hay.indexOf(q) < 0) return false;
      }
      return true;
    });
    if (q) {
      var rank = function (e) {
        if (isEntryMasked(e)) return 9;
        var nm = (e.name || '').toLowerCase();
        if (nm === q) return 0;
        if (nm.indexOf(q) === 0) return 1;
        if (nm.indexOf(q) >= 0) return 2;
        if ((e.category || '').toLowerCase().indexOf(q) >= 0) return 3;
        return 4;
      };
      out.sort(function (a, b) {
        var ra = rank(a), rb = rank(b);
        if (ra !== rb) return ra - rb;
        return (b.unlocked ? 1 : 0) - (a.unlocked ? 1 : 0);
      });
    } else if (S.codexSort === 'alpha') {
      out.sort(function (a, b) {
        var na = isEntryMasked(a) ? 'zzz' : a.name;
        var nb = isEntryMasked(b) ? 'zzz' : b.name;
        return na.localeCompare(nb, window.GowI18n.lang);
      });
    } else if (S.codexSort === 'unlocked' && c.has_save) {
      out.sort(function (a, b) {
        var na = S.codexNewIds[a.id] ? 2 : (a.unlocked ? 1 : 0);
        var nb = S.codexNewIds[b.id] ? 2 : (b.unlocked ? 1 : 0);
        return nb - na;
      });
    }
    return out;
  }

  function treasureStatusText(st) {
    if (st === 'active') return tr('codex_tr_active');
    if (st === 'dug') return tr('codex_tr_dug');
    return tr('codex_tr_unfound');
  }

  function codexBookIconUrl(entry, kind) {
    if (!entry || !entry.icon) return null;
    if (kind === 'treasures') return entry.icon;
    return entry.icon + (entry.icon.indexOf('?') >= 0 ? '&ink=dark' : '?ink=dark');
  }

  function renderTreasureRouteBlock(entry, bookMode) {
    if (!entry) return '';
    var cls = bookMode ? 'gow-book-tr-routes' : 'gow-cx-map-links';
    var btnCls = bookMode ? 'gow-book-route-btn' : 'gow-cx-map-chip';
    var btns = [];
    if (entry.dig_pin) {
      var dp = entry.dig_pin;
      var dLoc = (dp.realm_name || REALM_SHORT[dp.realm] || dp.realm) + (dp.region ? ' · ' + dp.region : '');
      btns.push(
        '<button type="button" class="' + btnCls + ' is-primary' + (dp.collected ? ' is-done' : '') +
          '" data-cx-route-realm="' + esc(dp.realm) + '" data-cx-route-pin="' + esc(dp.id) + '">' +
          GOW_SVG.route +
          '<span class="gow-book-route-copy"><b>' + esc(tr('route_to_dig')) + '</b><small>' + esc(dLoc) + '</small></span>' +
        '</button>'
      );
    }
    if (entry.map_pin) {
      var mp = entry.map_pin;
      var mLoc = (mp.realm_name || REALM_SHORT[mp.realm] || mp.realm) + (mp.region ? ' · ' + mp.region : '');
      btns.push(
        '<button type="button" class="' + btnCls + (mp.collected ? ' is-done' : '') +
          '" data-cx-route-realm="' + esc(mp.realm) + '" data-cx-route-pin="' + esc(mp.id) + '">' +
          GOW_SVG.treasure +
          '<span class="gow-book-route-copy"><b>' + esc(tr('route_to_map')) + '</b><small>' + esc(mLoc) + '</small></span>' +
        '</button>'
      );
    }
    if (!btns.length) return '';
    return '<section class="' + cls + '">' + btns.join('') + '</section>';
  }

  function renderBookSectionRail(tabs) {
    var icons = {
      bestiary: GOW_SVG.boss,
      lore: GOW_SVG.quill,
      treasures: GOW_SVG.treasure,
      skills: GOW_SVG.spark,
      hero: GOW_SVG.crest
    };
    return '<nav class="gow-book-icons" role="tablist" aria-label="Codex">' +
      tabs.map(function (tb) {
        return '<button type="button" role="tab" aria-selected="' + (S.codexTab === tb.key) +
          '" class="gow-book-icon-btn' + (S.codexTab === tb.key ? ' is-active' : '') +
          '" data-cx-tab="' + tb.key + '" title="' + esc(tb.label + (tb.meta ? ' (' + tb.meta + ')' : '')) + '">' +
          (icons[tb.key] || GOW_SVG.book) +
        '</button>';
      }).join('') +
    '</nav>';
  }

  function renderCodexBook(kind, tabs) {
    var c = S.codex || {};
    var railIcons = renderBookSectionRail(tabs);
    if (!S.codex && S.codexLoading) {
      return '<div class="gow-book-stage is-empty">' + railIcons +
        '<div class="gow-cx-notice">' + GOW_SVG.book + '<p>' + esc(tr('s089') + tr('codex_title')) + '…</p></div></div>';
    }
    if (!c.game_data_available) {
      return '<div class="gow-book-stage is-empty">' + railIcons +
        '<div class="gow-cx-notice">' + GOW_SVG.book + '<p>' + esc(tr('codex_no_game_data')) + '</p></div></div>';
    }
    var entries = filteredCodexEntries(kind);
    var isTreasure = kind === 'treasures';
    var railHeading = kind === 'lore' ? tr('codex_tab_lore')
      : isTreasure ? tr('codex_tab_treasures') : tr('codex_tab_bestiary');
    var searchPh = kind === 'lore' ? tr('codex_search_lore')
      : isTreasure ? tr('codex_search_treasures') : tr('codex_search_bestiary');

    var catsHtml = '';
    var pageHeaderLeft = railHeading;
    var newInKind = 0;
    if (isTreasure) {
      var allTr = c.treasures || [];
      var countsTr = { all: allTr.length, active: 0, dug: 0, unfound: 0 };
      allTr.forEach(function (t) {
        if (countsTr[t.status] != null) countsTr[t.status]++;
        if (S.codexNewIds[t.id]) newInKind++;
      });
      var trCats = [
        ['all', tr('codex_all'), countsTr.all],
        ['active', tr('codex_tr_filter_active'), countsTr.active],
        ['dug', tr('codex_tr_filter_dug'), countsTr.dug],
        ['unfound', tr('codex_tr_filter_unfound'), countsTr.unfound]
      ];
      var curTrCat = trCats.filter(function (x) { return x[0] === S.treasureFilter; })[0];
      pageHeaderLeft = curTrCat && curTrCat[0] !== 'all' ? curTrCat[1] : tr('codex_tab_treasures');
      catsHtml = trCats.map(function (item) {
        return '<button type="button" class="gow-book-cat' + (S.treasureFilter === item[0] ? ' is-on' : '') +
          '" data-cx-tr-filter="' + item[0] + '"><span>' + esc(item[1]) + '</span><em>' + item[2] + '</em></button>';
      }).join('');
    } else {
      var rawAll = (kind === 'lore' ? (c.lore || []) : (c.bestiary || [])).filter(function (e) {
        return S.codexValhalla || !e.is_valhalla;
      });
      var catCounts = {};
      rawAll.forEach(function (e) {
        catCounts[e.category] = (catCounts[e.category] || 0) + 1;
        if (S.codexNewIds[e.id]) newInKind++;
      });
      var cats = Object.keys(catCounts).sort();
      pageHeaderLeft = S.codexCat || railHeading;
      catsHtml = '<button type="button" class="gow-book-cat' + (!S.codexCat ? ' is-on' : '') +
        '" data-cx-cat=""><span>' + esc(tr('codex_all')) + '</span><em>' + rawAll.length + '</em></button>' +
        cats.map(function (cat) {
          return '<button type="button" class="gow-book-cat' + (S.codexCat === cat ? ' is-on' : '') +
            '" data-cx-cat="' + esc(cat) + '"><span>' + esc(cat) + '</span><em>' + catCounts[cat] + '</em></button>';
        }).join('');
    }

    var selected = entries.filter(function (e) { return e.id === S.codexSelectedId; })[0] || entries[0] || null;
    if (selected && S.codexSelectedId !== selected.id) S.codexSelectedId = selected.id;

    var statusBtns = '';
    if (!isTreasure) {
      var statusItems = [['all', tr('codex_all')], ['unlocked', tr('codex_unlocked')], ['locked', tr('codex_locked')]];
      if (newInKind > 0) statusItems.push(['new', tr('codex_only_new').replace('{n}', String(newInKind))]);
      statusBtns = '<div class="gow-book-mini-seg">' + statusItems.map(function (st) {
        return '<button type="button" class="gow-book-mini-pill' + (S.codexStatus === st[0] ? ' is-on' : '') +
          '" data-cx-status="' + st[0] + '">' + esc(st[1]) + '</button>';
      }).join('') + '</div>';
    }

    var railTools =
      '<div class="gow-book-tools-pop' + (S.bookToolsOpen ? ' is-open' : '') + '" id="gowBookToolsPop">' +
        '<label class="gow-cx-search-wrap gow-book-search">' + GOW_SVG.search +
          '<input type="text" class="gow-cx-search" id="gowCxSearch" value="' + esc(S.codexQuery) + '" placeholder="' + esc(searchPh) + '" autocomplete="off" spellcheck="false" />' +
        '</label>' +
        statusBtns +
        '<div class="gow-book-mini-row">' +
          '<button type="button" class="gow-book-mini-pill' + (S.codexSort === 'alpha' ? ' is-on' : '') +
            '" data-cx-sort="1">' + esc(S.codexSort === 'alpha' ? tr('codex_sort_alpha') : tr('codex_sort_unlocked')) + '</button>' +
          (!isTreasure ? '<button type="button" class="gow-book-mini-pill' + (S.codexValhalla ? ' is-on' : '') +
            '" data-cx-valhalla="1">' + esc(tr('codex_valhalla')) + '</button>' : '') +
          '<button type="button" class="gow-book-mini-pill' + (S.codexSpoiler ? ' is-on' : '') +
            '" data-cx-spoiler="1">' + (S.codexSpoiler ? GOW_SVG.lock : GOW_SVG.eye) + '<span>' + esc(tr('codex_spoiler')) + '</span></button>' +
        '</div>' +
      '</div>';

    var unlockedInView = 0, dugInView = 0;
    entries.forEach(function (e) {
      if (e.unlocked) unlockedInView++;
      if (e.dug) dugInView++;
    });
    var leftSubText = '';
    if (entries.length) {
      if (isTreasure && c.has_save) {
        leftSubText = tr('codex_book_found_dug')
          .replace('{found}', String(unlockedInView))
          .replace('{total}', String(entries.length))
          .replace('{dug}', String(dugInView));
      } else if (c.has_save) {
        leftSubText = tr('codex_book_count')
          .replace('{done}', String(unlockedInView))
          .replace('{total}', String(entries.length));
      } else {
        leftSubText = tr('codex_book_entries').replace('{n}', String(entries.length));
      }
    }

    var listHtml = entries.length ? entries.map(function (e) {
      var masked = isEntryMasked(e);
      var isNew = !!S.codexNewIds[e.id];
      var active = !!(selected && selected.id === e.id);
      var suffix = '';
      if (isNew) suffix += '<em class="gow-book-new">' + esc(tr('codex_new_badge')) + '</em>';
      if (isTreasure) {
        if (e.status === 'dug') suffix += '<span class="gow-book-st is-dug" title="' + esc(tr('codex_tr_dug')) + '">' + GOW_SVG.check + '</span>';
        else if (e.status === 'active') suffix += '<span class="gow-book-st is-active-tr" title="' + esc(tr('codex_tr_active')) + '">' + GOW_SVG.dot + '</span>';
        else suffix += '<span class="gow-book-st is-locked">' + GOW_SVG.lock + '</span>';
      } else if (!e.unlocked) {
        suffix += '<span class="gow-book-st is-locked">' + GOW_SVG.lock + '</span>';
      }
      return '<button type="button" class="gow-cx-item gow-book-entry' +
        (active ? ' is-active' : '') +
        (e.unlocked ? ' is-unlocked' : ' is-locked') +
        (isNew ? ' is-new' : '') + '" data-cx-select="' + esc(e.id) + '">' +
        '<span class="gow-book-bullet" aria-hidden="true">' + (active ? '❖' : '◆') + '</span>' +
        '<span class="gow-book-entry-name">' + esc(masked ? '???' : e.name) + '</span>' +
        (suffix ? '<span class="gow-book-entry-end">' + suffix + '</span>' : '') +
      '</button>';
    }).join('') : '<div class="gow-book-empty">' + esc(tr('codex_empty_filter')) + '</div>';

    var rightBanner = selected ? (isEntryMasked(selected) ? '???' : selected.name) : railHeading;
    var rightBody = '<div class="gow-book-empty">' + esc(tr('codex_select_entry')) + '</div>';
    var flapHtml = '<div class="gow-book-flap-empty">' + GOW_SVG.crest + '</div>';

    if (selected) {
      var dMask = isEntryMasked(selected);
      var inkUrl = codexBookIconUrl(selected, kind);
      if (inkUrl) {
        var flapCaption = '';
        if (!dMask) {
          var flapSub = isTreasure ? tr('codex_zoom_sketch') : (selected.category || '');
          flapCaption =
            '<span class="gow-book-flap-caption">' +
              '<span class="gow-book-flap-title">' + esc(selected.name) + '</span>' +
              (flapSub ? '<span class="gow-book-flap-sub">' + esc(flapSub) + '</span>' : '') +
            '</span>';
        }
        flapHtml =
          '<button type="button" class="gow-book-sketch-btn' + (dMask ? ' is-masked' : '') + (isTreasure ? ' is-clue' : '') +
            '" data-cx-zoom-img="' + esc(inkUrl) + '" title="' + esc(tr('codex_zoom_sketch')) + '"' + (dMask ? ' disabled' : '') + '>' +
            '<img src="' + esc(inkUrl) + '" alt="" loading="lazy" />' +
            flapCaption +
            (dMask ? '<span class="gow-book-flap-lock">' + GOW_SVG.lock + '</span>' : '') +
          '</button>';
      } else if (dMask) {
        flapHtml = '<div class="gow-book-flap-empty">' + GOW_SVG.lock + '</div>';
      }

      if (dMask) {
        rightBody =
          '<div class="gow-book-spoiler">' +
            GOW_SVG.lock +
            '<p>' + esc(tr('codex_spoiler_hint')) + '</p>' +
            '<button type="button" class="gow-book-reveal-btn" data-cx-reveal="' + esc(selected.id) + '">' +
              GOW_SVG.eye + '<span>' + esc(tr('codex_reveal')) + '</span></button>' +
          '</div>';
      } else {
        var metaHtml = '';
        if (isTreasure) {
          metaHtml = '<div class="gow-book-entry-head"><span class="gow-book-stamp is-' + esc(selected.status) + '">' +
            esc(treasureStatusText(selected.status)) + '</span></div>';
        } else {
          var metaParts = [];
          if (selected.category) metaParts.push('<span class="gow-book-meta-cat">' + esc(selected.category) + '</span>');
          if (selected.is_valhalla) metaParts.push('<span class="gow-book-stamp is-dlc">' + esc(tr('codex_valhalla')) + '</span>');
          if (selected.family_kills != null) {
            metaParts.push('<span class="gow-book-meta-kills">' + esc(tr('codex_kills_family')) + ': <b>' + selected.family_kills + '</b></span>');
          }
          if (!selected.unlocked && c.has_save) {
            metaParts.push('<span class="gow-book-meta-state">' + esc(tr('codex_entry_locked')) + '</span>');
          }
          if (metaParts.length) {
            metaHtml = '<div class="gow-book-entry-head">' +
              metaParts.join('<span class="gow-book-meta-sep" aria-hidden="true">◆</span>') +
            '</div>';
          }
        }
        metaHtml += '<div class="gow-book-rule" aria-hidden="true"><span></span></div>';

        var rawDesc = String(selected.description || '').trim();
        var descLines = rawDesc ? rawDesc.split(/\r?\n/).filter(function (l) { return l.trim().length > 0; }) : [];
        var isVerse = isTreasure && descLines.length >= 3 && (rawDesc.length / descLines.length) < 64;
        var useDropcap = !isTreasure && !isVerse && rawDesc.length >= 90 && !/^[0-9*_\-\u2022]/.test(rawDesc);
        var proseCls = 'gow-book-prose' + (useDropcap ? ' has-dropcap' : '') + (isVerse ? ' is-verse' : '');
        var proseHtml = '<div class="' + proseCls + '">' + mdLite(rawDesc) + '</div>';
        var extraHtml = '';

        if (kind === 'bestiary' && selected.tips && selected.tips.length) {
          extraHtml +=
            '<section class="gow-book-section">' +
              '<h3 class="gow-book-section-head"><span>' + esc(tr('codex_combat_tips')) + '</span></h3>' +
              '<ul class="gow-book-bullets">' + selected.tips.map(function (t) {
                var tipMasked = S.codexSpoiler && !t.unlocked && !S.codexRevealed[selected.id + ':' + t.id];
                if (tipMasked) {
                  return '<li class="is-locked"><span class="gow-book-li-dot" aria-hidden="true">◆</span><div class="gow-book-li-body"><em>' +
                    esc(tr('codex_tip_locked')) + '</em><button type="button" class="gow-book-inline-link" data-cx-reveal="' +
                    esc(selected.id + ':' + t.id) + '">' + esc(tr('codex_reveal')) + '</button></div></li>';
                }
                return '<li><span class="gow-book-li-dot" aria-hidden="true">◆</span><div class="gow-book-li-body">' + mdLite(t.text) + '</div></li>';
              }).join('') + '</ul>' +
            '</section>';
        }

        if (kind === 'lore' && selected.updates && selected.updates.length) {
          extraHtml +=
            '<section class="gow-book-section">' +
              '<h3 class="gow-book-section-head"><span>' + esc(tr('codex_updates')) + '</span></h3>' +
              '<ul class="gow-book-bullets">' + selected.updates.map(function (u) {
                var uMask = S.codexSpoiler && !u.unlocked && !S.codexRevealed[selected.id + ':' + u.id];
                if (uMask) {
                  return '<li class="is-locked"><span class="gow-book-li-dot" aria-hidden="true">◆</span><div class="gow-book-li-body"><em>' +
                    esc(tr('codex_spoiler_hint')) + '</em><button type="button" class="gow-book-inline-link" data-cx-reveal="' +
                    esc(selected.id + ':' + u.id) + '">' + esc(tr('codex_reveal')) + '</button></div></li>';
                }
                return '<li><span class="gow-book-li-dot" aria-hidden="true">◆</span><div class="gow-book-li-body">' + mdLite(u.text) + '</div></li>';
              }).join('') + '</ul>' +
            '</section>';
        }

        if (isTreasure) {
          extraHtml += renderTreasureRouteBlock(selected, true);
        }

        if (selected.map_pins && selected.map_pins.length) {
          extraHtml += '<section class="gow-book-map-links"><div class="gow-book-links-head">' +
            GOW_SVG.route + '<span>' + esc(tr('codex_map_locations')) + '</span></div><div class="gow-book-link-chips">' +
            selected.map_pins.map(function (mp) {
              return '<button type="button" class="gow-book-route-btn' + (mp.collected ? ' is-done' : '') +
                '" data-cx-route-realm="' + esc(mp.realm) + '" data-cx-route-pin="' + esc(mp.id) +
                '" data-cx-jump-realm="' + esc(mp.realm) + '" data-cx-jump-pin="' + esc(mp.id) + '">' +
                (mp.collected ? GOW_SVG.check : GOW_SVG.route) +
                '<span>' + esc(mp.realm_name || REALM_SHORT[mp.realm] || mp.realm) + ' · ' + esc(mp.name) + '</span></button>';
            }).join('') + '</div></section>';
        }

        rightBody = metaHtml + proseHtml + extraHtml + '<div class="gow-book-colophon" aria-hidden="true"></div>';
      }
    }

    var wmKind = kind === 'bestiary' ? 'wm-bestiary' : 'wm-lore';
    return '<div class="gow-book-stage' + (S.codexMobileDetail ? ' is-mobile-detail' : '') +
      (S.bookCatOpen ? ' is-cat-open' : '') + '">' +
      railIcons +
      '<aside class="gow-book-rail">' +
        '<div class="gow-book-rail-rule"></div>' +
        '<div class="gow-book-rail-title">' + esc(railHeading) + '</div>' +
        '<div class="gow-book-cats">' + catsHtml + '</div>' +
        '<div class="gow-book-rail-rule is-bottom"></div>' +
      '</aside>' +
      railTools +
      '<div class="gow-book-spread">' +
        '<div class="gow-book-cover">' +
          '<section class="gow-book-page is-left ' + wmKind + '">' +
            '<button type="button" class="gow-book-banner is-btn" data-cx-cats-toggle="1" title="' + esc(tr('codex_categories')) + '"><span>' + esc(pageHeaderLeft) + '</span></button>' +
            (leftSubText ? '<div class="gow-book-page-sub"><span>' + esc(leftSubText) + '</span></div>' : '') +
            '<div class="gow-book-list" id="gowCxList">' + listHtml + '</div>' +
          '</section>' +
          '<div class="gow-book-spine" aria-hidden="true">' +
            '<span class="gow-book-tie"></span><span class="gow-book-tie"></span>' +
            '<span class="gow-book-tie"></span><span class="gow-book-tie"></span>' +
          '</div>' +
          '<article class="gow-book-page is-right ' + wmKind + '" id="gowCxDetail">' +
            '<button type="button" class="gow-cx-back gow-book-back" data-cx-back="1">' + GOW_SVG.chevron_left + '<span>' + esc(tr('codex_back_list')) + '</span></button>' +
            '<div class="gow-book-banner"><h2>' + esc(rightBanner) + '</h2></div>' +
            '<div class="gow-book-page-scroll">' + rightBody + '</div>' +
            '<div class="gow-book-page-ornament" aria-hidden="true"><span>◆</span><i></i><span>❖</span></div>' +
          '</article>' +
        '</div>' +
        '<aside class="gow-book-flap">' + flapHtml + '</aside>' +
      '</div>' +
    '</div>';
  }

  function renderCodexPortrait(entry, large, masked) {
    var cls = 'gow-cx-portrait' + (large ? ' is-lg' : ' is-sm') + (masked ? ' is-masked' : '');
    if (entry.icon) {
      return '<div class="' + cls + '"><img src="' + esc(entry.icon) + '" alt="" loading="lazy" />' +
        (masked ? '<span class="gow-cx-portrait-lock">' + GOW_SVG.lock + '</span>' : '') + '</div>';
    }
    return '<div class="' + cls + ' is-fallback">' + (masked ? GOW_SVG.lock : GOW_SVG.crest) + '</div>';
  }

  function renderCodexMasterDetail(kind) {
    var c = S.codex || {};
    if (!S.codex && S.codexLoading) {
      return '<div class="gow-cx-notice">' + GOW_SVG.book + '<p>' + esc(tr('s089') + tr('codex_title')) + '…</p></div>';
    }
    if (!c.game_data_available) {
      return '<div class="gow-cx-notice">' + GOW_SVG.book + '<p>' + esc(tr('codex_no_game_data')) + '</p></div>';
    }
    var isTreasure = kind === 'treasures';
    var entries = filteredCodexEntries(kind);
    var rawAll = isTreasure ? (c.treasures || [])
      : (kind === 'lore' ? (c.lore || []) : (c.bestiary || [])).filter(function (e) { return S.codexValhalla || !e.is_valhalla; });
    var catCounts = {};
    var newInKind = 0;
    rawAll.forEach(function (e) {
      if (!isTreasure) catCounts[e.category] = (catCounts[e.category] || 0) + 1;
      if (S.codexNewIds[e.id]) newInKind++;
    });
    var cats = Object.keys(catCounts).sort();

    var selected = entries.filter(function (e) { return e.id === S.codexSelectedId; })[0] || entries[0] || null;
    if (selected && S.codexSelectedId !== selected.id) S.codexSelectedId = selected.id;

    var searchPh = kind === 'lore' ? tr('codex_search_lore')
      : isTreasure ? tr('codex_search_treasures') : tr('codex_search_bestiary');
    var statusItems = isTreasure
      ? [['all', tr('codex_all')], ['active', tr('codex_tr_filter_active')], ['dug', tr('codex_tr_filter_dug')], ['unfound', tr('codex_tr_filter_unfound')]]
      : [['all', tr('codex_all')], ['unlocked', tr('codex_unlocked')], ['locked', tr('codex_locked')]];
    if (!isTreasure && newInKind > 0) statusItems.push(['new', tr('codex_only_new').replace('{n}', String(newInKind))]);
    var filtersHtml =
      '<div class="gow-cx-toolbar">' +
        '<label class="gow-cx-search-wrap">' + GOW_SVG.search +
          '<input type="text" class="gow-cx-search" id="gowCxSearch" value="' + esc(S.codexQuery) + '" placeholder="' + esc(searchPh) + '" autocomplete="off" spellcheck="false" />' +
        '</label>' +
        '<div class="gow-cx-seg" role="group">' +
          statusItems.map(function (st) {
            var activeSt = isTreasure ? (S.treasureFilter === st[0]) : (S.codexStatus === st[0]);
            var attr = isTreasure ? ('data-cx-tr-filter="' + st[0] + '"') : ('data-cx-status="' + st[0] + '"');
            return '<button type="button" class="gow-cx-pill' + (activeSt ? ' is-on' : '') +
              '" ' + attr + '>' + esc(st[1]) + '</button>';
          }).join('') +
        '</div>' +
        '<button type="button" class="gow-cx-pill' + (S.codexSort === 'alpha' ? ' is-on' : '') +
          '" data-cx-sort="1">' + esc(S.codexSort === 'alpha' ? tr('codex_sort_alpha') : tr('codex_sort_unlocked')) + '</button>' +
        (!isTreasure ? '<button type="button" class="gow-cx-pill' + (S.codexValhalla ? ' is-on' : '') +
          '" data-cx-valhalla="1">' + esc(tr('codex_valhalla')) + '</button>' : '') +
        '<button type="button" class="gow-cx-pill' + (S.codexSpoiler ? ' is-on' : '') +
          '" data-cx-spoiler="1">' + (S.codexSpoiler ? GOW_SVG.lock : GOW_SVG.eye) + '<span>' + esc(tr('codex_spoiler')) + '</span></button>' +
      '</div>' +
      (!isTreasure ? '<div class="gow-cx-cats">' +
        '<button type="button" class="gow-cx-cat' + (!S.codexCat ? ' is-on' : '') + '" data-cx-cat="">' +
          esc(tr('codex_all')) + ' <em>' + rawAll.length + '</em></button>' +
        cats.map(function (cat) {
          return '<button type="button" class="gow-cx-cat' + (S.codexCat === cat ? ' is-on' : '') + '" data-cx-cat="' + esc(cat) + '">' +
            esc(cat) + ' <em>' + catCounts[cat] + '</em></button>';
        }).join('') +
      '</div>' : '');

    var listHtml = entries.length ? entries.map(function (e) {
      var masked = isEntryMasked(e);
      var isNew = !!S.codexNewIds[e.id];
      var tipsDots = '';
      if (kind === 'bestiary' && e.tips && e.tips.length) {
        tipsDots = '<span class="gow-cx-tip-dots">' + e.tips.map(function (t) {
          return '<i class="' + (t.unlocked ? 'is-on' : '') + '"></i>';
        }).join('') + '</span>';
      }
      var subText = isTreasure ? treasureStatusText(e.status) : (e.category + (e.is_valhalla ? ' · DLC' : ''));
      return '<button type="button" class="gow-cx-item' +
        (selected && selected.id === e.id ? ' is-active' : '') +
        (e.unlocked ? ' is-unlocked' : ' is-locked') +
        (isNew ? ' is-new' : '') + '" data-cx-select="' + esc(e.id) + '">' +
        renderCodexPortrait(e, false, masked) +
        '<span class="gow-cx-item-info">' +
          '<span class="gow-cx-item-top">' +
            '<strong>' + esc(masked ? '???' : e.name) + '</strong>' +
            (isNew ? '<em class="gow-cx-new">' + esc(tr('codex_new_badge')) + '</em>' : '') +
          '</span>' +
          '<span class="gow-cx-item-sub">' + esc(subText) + '</span>' +
        '</span>' +
        '<span class="gow-cx-item-right">' +
          tipsDots +
          '<span class="gow-cx-state-ic">' + (e.unlocked ? GOW_SVG.check : GOW_SVG.lock) + '</span>' +
        '</span>' +
      '</button>';
    }).join('') : '<div class="gow-cx-empty">' + esc(tr('codex_empty_filter')) + '</div>';

    var detailHtml = '<div class="gow-cx-empty">' + esc(tr('codex_select_entry')) + '</div>';
    if (selected) {
      var dMask = isEntryMasked(selected);
      var metaChips = isTreasure
        ? '<span class="gow-cx-chip ' + (selected.unlocked ? 'is-unlocked' : 'is-locked') + '">' +
            (selected.dug ? GOW_SVG.check : (selected.unlocked ? GOW_SVG.dot : GOW_SVG.lock)) +
            '<span>' + esc(treasureStatusText(selected.status)) + '</span></span>'
        : '<span class="gow-cx-chip">' + esc(selected.category) + '</span>' +
          '<span class="gow-cx-chip ' + (selected.unlocked ? 'is-unlocked' : 'is-locked') + '">' +
            (selected.unlocked ? GOW_SVG.check : GOW_SVG.lock) +
            '<span>' + esc(selected.unlocked ? tr('codex_entry_unlocked') : tr('codex_entry_locked')) + '</span></span>' +
          (selected.is_valhalla ? '<span class="gow-cx-chip is-dlc">' + esc(tr('codex_valhalla')) + '</span>' : '') +
          (selected.family_kills != null ? '<span class="gow-cx-chip is-kills">' + esc(tr('codex_kills_family')) + ': <b>' + selected.family_kills + '</b></span>' : '');

      var bodySection = '';
      if (dMask) {
        bodySection =
          '<div class="gow-cx-spoiler-box">' +
            GOW_SVG.lock +
            '<p>' + esc(tr('codex_spoiler_hint')) + '</p>' +
            '<button type="button" class="gow-fs-btn" data-cx-reveal="' + esc(selected.id) + '">' +
              GOW_SVG.eye + '<span>' + esc(tr('codex_reveal')) + '</span></button>' +
          '</div>';
      } else {
        if (isTreasure && selected.icon) {
          bodySection += '<button type="button" class="gow-fs-shot gow-cx-tr-shot" data-cx-zoom-img="' + esc(selected.icon) + '">' +
            '<img src="' + esc(selected.icon) + '" alt="" loading="lazy" /></button>';
        }
        var darkDesc = String(selected.description || '').trim();
        var darkDrop = !isTreasure && darkDesc.length >= 90 && !/^[0-9*_\-\u2022]/.test(darkDesc);
        bodySection += '<div class="gow-cx-prose' + (darkDrop ? ' has-dropcap' : '') + '">' + mdLite(darkDesc) + '</div>';
        if (isTreasure) bodySection += renderTreasureRouteBlock(selected, false);
        if (kind === 'bestiary' && selected.tips && selected.tips.length) {
          bodySection += '<section class="gow-cx-tips"><h3>' + GOW_SVG.spark + '<span>' + esc(tr('codex_combat_tips')) + '</span></h3><ul>' +
            selected.tips.map(function (t) {
              var tipMasked = S.codexSpoiler && !t.unlocked && !S.codexRevealed[selected.id + ':' + t.id];
              if (tipMasked) {
                return '<li class="is-locked"><span>' + esc(tr('codex_tip_locked')) + '</span>' +
                  '<button type="button" class="gow-fs-link" data-cx-reveal="' + esc(selected.id + ':' + t.id) + '">' + esc(tr('codex_reveal')) + '</button></li>';
              }
              return '<li class="' + (t.unlocked ? 'is-unlocked' : 'is-revealed') + '">' + mdLite(t.text) + '</li>';
            }).join('') + '</ul></section>';
        }
        if (kind === 'lore' && selected.updates && selected.updates.length) {
          bodySection += '<section class="gow-cx-updates"><h3>' + GOW_SVG.book + '<span>' + esc(tr('codex_updates')) + '</span></h3>' +
            selected.updates.map(function (u) {
              var uMask = S.codexSpoiler && !u.unlocked && !S.codexRevealed[selected.id + ':' + u.id];
              if (uMask) {
                return '<div class="gow-cx-update is-locked"><span>' + esc(tr('codex_spoiler_hint')) + '</span>' +
                  '<button type="button" class="gow-fs-link" data-cx-reveal="' + esc(selected.id + ':' + u.id) + '">' + esc(tr('codex_reveal')) + '</button></div>';
              }
              return '<div class="gow-cx-update">' + mdLite(u.text) + '</div>';
            }).join('') + '</section>';
        }
        if (selected.map_pins && selected.map_pins.length) {
          bodySection += '<section class="gow-cx-map-links"><h3>' + GOW_SVG.route + '<span>' + esc(tr('codex_map_locations')) + '</span></h3><div class="gow-cx-map-chips">' +
            selected.map_pins.map(function (mp) {
              return '<button type="button" class="gow-cx-map-chip' + (mp.collected ? ' is-done' : '') +
                '" data-cx-route-realm="' + esc(mp.realm) + '" data-cx-route-pin="' + esc(mp.id) +
                '" data-cx-jump-realm="' + esc(mp.realm) + '" data-cx-jump-pin="' + esc(mp.id) + '">' +
                (mp.collected ? GOW_SVG.check : GOW_SVG.route) +
                '<span>' + esc(mp.realm_name || REALM_SHORT[mp.realm] || mp.realm) + ' · ' + esc(mp.name) + '</span></button>';
            }).join('') + '</div></section>';
        }
      }

      detailHtml =
        '<button type="button" class="gow-cx-back" data-cx-back="1">' + GOW_SVG.chevron_left + '<span>' + esc(tr('codex_back_list')) + '</span></button>' +
        '<div class="gow-cx-detail-head">' +
          (!isTreasure ? renderCodexPortrait(selected, true, dMask) : '') +
          '<div class="gow-cx-detail-meta">' +
            '<h2>' + esc(dMask ? '???' : selected.name) + '</h2>' +
            '<div class="gow-cx-chips">' + metaChips + '</div>' +
          '</div>' +
        '</div>' +
        bodySection;
    }

    return filtersHtml +
      '<div class="gow-cx-split' + (S.codexMobileDetail ? ' is-detail' : '') + '">' +
        '<div class="gow-cx-list" id="gowCxList">' + listHtml + '</div>' +
        '<article class="gow-cx-detail" id="gowCxDetail">' + detailHtml + '</article>' +
      '</div>';
  }

  function renderCodexSkills() {
    var c = S.codex || {};
    if (!S.codex && S.codexLoading) {
      return '<div class="gow-cx-notice">' + GOW_SVG.book + '<p>' + esc(tr('s089') + tr('codex_title')) + '…</p></div>';
    }
    if (!c.game_data_available) {
      return '<div class="gow-cx-notice">' + GOW_SVG.book + '<p>' + esc(tr('codex_no_game_data')) + '</p></div>';
    }
    var near = c.near_completion || [];
    var nearHtml = near.length ? (
      '<section class="gow-cx-near">' +
        '<div class="gow-fs-kicker">' + esc(tr('codex_near_title')) + '</div>' +
        '<div class="gow-cx-near-rail">' +
          near.slice(0, 6).map(function (n) {
            var p = pct(n.done, n.total);
            return '<div class="gow-cx-near-card">' +
              '<div class="gow-cx-near-top"><strong>' + esc(n.name) + '</strong><em>' + esc(tr('codex_left').replace('{n}', String(n.remaining))) + '</em></div>' +
              '<div class="gow-cx-near-sub"><span>' + esc(n.tier_label || '') + '</span><span>' + n.done + ' / ' + n.total + '</span></div>' +
              '<div class="gow-fs-bar"><i style="width:' + p + '%"></i></div>' +
            '</div>';
          }).join('') +
        '</div>' +
      '</section>'
    ) : '';

    var q = S.codexQuery.trim().toLowerCase();
    var f = S.codexSkillFilter;
    var toolbar =
      '<div class="gow-cx-toolbar">' +
        '<label class="gow-cx-search-wrap">' + GOW_SVG.search +
          '<input type="text" class="gow-cx-search" id="gowCxSearch" value="' + esc(S.codexQuery) + '" placeholder="' + esc(tr('codex_search_skills')) + '" autocomplete="off" spellcheck="false" />' +
        '</label>' +
        '<div class="gow-cx-seg" role="group">' +
          [['all', tr('codex_all')], ['axe', tr('codex_filter_axe')], ['blades', tr('codex_filter_blades')],
           ['spear', tr('codex_filter_spear')], ['labors', tr('codex_filter_labors')]].map(function (o) {
            return '<button type="button" class="gow-cx-pill' + (f === o[0] ? ' is-on' : '') +
              '" data-cx-skill-filter="' + o[0] + '">' + esc(o[1]) + '</button>';
          }).join('') +
        '</div>' +
      '</div>';

    var cards = [];
    if (f !== 'labors') {
      (c.skills || []).forEach(function (sk) {
        if (f !== 'all' && sk.weapon !== f) return;
        if (q && (sk.name + ' ' + sk.weapon_label).toLowerCase().indexOf(q) < 0) return;
        var next = sk.next_tier;
        var p = sk.completed ? 100 : (next ? pct(next.done, next.total) : pct(sk.done, sk.max_total));
        var progText = sk.completed ? tr('codex_completed') : (next ? next.done + ' / ' + next.total + ' · ' + next.tier_label : sk.done + ' / ' + sk.max_total);
        cards.push(
          '<div class="gow-cx-skill-card' + (sk.completed ? ' is-done' : '') + '">' +
            '<div class="gow-cx-skill-head"><span class="gow-cx-chip">' + esc(sk.weapon_label) + '</span>' +
              '<span class="gow-cx-tiers">' + (sk.tiers || []).map(function (ti) {
                return '<i class="gow-cx-tier is-' + esc(ti.tier) + (ti.completed ? ' is-on' : '') + '" title="' + esc(ti.tier_label + ': ' + ti.done + '/' + ti.total) + '"></i>';
              }).join('') + '</span></div>' +
            '<strong>' + esc(sk.name) + '</strong>' +
            '<div class="gow-cx-skill-meta"><span>' + esc(progText) + '</span><em>' + p + '%</em></div>' +
            '<div class="gow-fs-bar"><i style="width:' + p + '%"></i></div>' +
          '</div>'
        );
      });
    }
    if (f === 'all' || f === 'labors') {
      (c.labors || []).forEach(function (lb) {
        if (lb.is_ngp && !lb.completed && (!lb.next_tier || !lb.next_tier.done)) return;
        if (q && (lb.name + ' ' + lb.category).toLowerCase().indexOf(q) < 0) return;
        var next = lb.next_tier;
        var lastT = (lb.tiers || [])[(lb.tiers || []).length - 1];
        var p = lb.completed ? 100 : (next ? pct(next.done, next.total) : 0);
        var progText = lb.completed ? tr('codex_completed') : (next ? (next.done + ' / ' + next.total + (next.tier_label ? ' · ' + next.tier_label : '')) : (lastT ? lastT.done + ' / ' + lastT.total : ''));
        var desc = (next && next.desc) || (lastT && lastT.desc) || '';
        cards.push(
          '<div class="gow-cx-skill-card is-labor' + (lb.completed ? ' is-done' : '') + '">' +
            '<div class="gow-cx-skill-head"><span class="gow-cx-chip">' + esc(lb.category) + '</span>' +
              (lb.completed ? '<span class="gow-cx-state-ic">' + GOW_SVG.check + '</span>' : '') + '</div>' +
            '<strong>' + esc(lb.name) + '</strong>' +
            (desc ? '<div class="gow-cx-labor-desc">' + esc(desc) + '</div>' : '') +
            '<div class="gow-cx-skill-meta"><span>' + esc(progText) + '</span><em>' + p + '%</em></div>' +
            '<div class="gow-fs-bar"><i style="width:' + p + '%"></i></div>' +
          '</div>'
        );
      });
    }

    return nearHtml + toolbar +
      '<div class="gow-cx-scroll"><div class="gow-cx-cards">' +
        (cards.length ? cards.join('') : '<div class="gow-cx-empty">' + esc(tr('codex_empty_filter')) + '</div>') +
      '</div></div>';
  }

  function renderCodexHero() {
    var d = S.data || {}, save = d.save || {};
    var hero = (S.codex && S.codex.hero) || d.hero || {};
    var w = hero.wallet || {}, am = hero.amulet || {}, col = hero.collectibles || {}, ld = hero.loadout || {};
    var fmt = function (v) { return v != null && v !== '' ? Number(v).toLocaleString(window.GowI18n.lang) : null; };

    var saveRows = [
      [tr('s077'), save.place],
      [tr('s078'), save.objective],
      [tr('s079'), save.play_time],
      [tr('s080'), save.difficulty],
      [tr('s081'), hero.power_level],
      [tr('codex_gear_lvl'), hero.gear_level],
      [tr('codex_amulet'), am.sockets_unlocked != null ? (am.sockets_unlocked + ' / ' + (am.sockets_total || 9)) : null]
    ].filter(function (r) { return r[1] != null && r[1] !== ''; });

    var walletRows = [
      [tr('s082'), fmt(w.hacksilver)],
      [tr('codex_divine_ashes'), fmt(w.divine_ashes)],
      [tr('codex_kratos_xp'), fmt(w.kratos_xp)],
      [tr('codex_atreus_xp'), fmt(w.atreus_xp)],
      [tr('codex_freya_xp'), fmt(w.freya_xp)],
      [tr('s083'), w.skills_count],
      [tr('s084'), w.unused_flames]
    ].filter(function (r) { return r[1] != null && r[1] !== ''; });

    var gearList = [].concat(ld.weapons || [], ld.armor || [], ld.shields || []);
    var gearHtml = gearList.length ? '<div class="gow-cx-gear-list">' + gearList.map(function (g) {
      var slotTxt = g.label === g.name ? tr('codex_slot_weapon') : g.label;
      return '<div class="gow-cx-gear-row"><span class="gow-cx-gear-slot">' + esc(slotTxt) + '</span>' +
        '<strong>' + esc(g.name) + '</strong>' +
        (g.level ? '<em>' + esc(tr('codex_lvl')) + ' ' + g.level + '</em>' : '') + '</div>';
    }).join('') + '</div>' : '';

    var realmCats = hero.realm_categories || [];
    var colHtml = '';
    var colTitle = tr('codex_hero_collectibles');
    if (realmCats.length) {
      colTitle = tr('codex_hero_realms_progress');
      colHtml = '<div class="gow-cx-col-grid">' + realmCats.map(function (rc) {
        var p = pct(rc.collected, rc.total);
        return '<div class="gow-cx-col-item"><div class="gow-cx-skill-meta"><span>' + esc(rc.name) + '</span><em>' + rc.collected + ' / ' + rc.total + '</em></div>' +
          '<div class="gow-fs-bar"><i style="width:' + p + '%"></i></div></div>';
      }).join('') + '</div>';
    } else {
      var colItems = [
        [tr('codex_col_ravens'), col.ravens && col.ravens.collected, col.ravens && col.ravens.total],
        [tr('codex_col_nornir'), col.nornir && col.nornir.opened, 35],
        [tr('codex_col_poems'), col.kvasir_poems && col.kvasir_poems.collected, col.kvasir_poems && col.kvasir_poems.total],
        [tr('codex_col_raven_tree'), col.raven_tree && col.raven_tree.opened, col.raven_tree && col.raven_tree.total]
      ].filter(function (it) { return it[1] != null && it[2]; });
      colHtml = colItems.length ? '<div class="gow-cx-col-grid">' + colItems.map(function (it) {
        var curVal = it[1], maxVal = it[2];
        var over = curVal > maxVal;
        var p = over ? 100 : pct(curVal, maxVal);
        var counterStr = over ? String(curVal) : (curVal + ' / ' + maxVal);
        return '<div class="gow-cx-col-item"><div class="gow-cx-skill-meta"><span>' + esc(it[0]) + '</span><em>' + counterStr + '</em></div>' +
          '<div class="gow-fs-bar"><i style="width:' + p + '%"></i></div></div>';
      }).join('') + '</div>' : '';
    }

    var mq = S.codexMaterialQuery.trim().toLowerCase();
    var mats = (hero.materials || []).filter(function (m) {
      return !mq || m.name.toLowerCase().indexOf(mq) >= 0;
    });
    var matsHtml = (hero.materials && hero.materials.length) ? (
      '<section class="gow-cx-hero-card gow-cx-hero-wide">' +
        '<div class="gow-cx-hero-head"><div class="gow-fs-kicker">' + esc(tr('codex_hero_materials')) + ' (' + mats.length + ')</div>' +
          '<label class="gow-cx-search-wrap gow-cx-mat-search">' + GOW_SVG.search +
            '<input type="text" class="gow-cx-search" id="gowCxMatSearch" value="' + esc(S.codexMaterialQuery) + '" placeholder="' + esc(tr('codex_search_materials')) + '" autocomplete="off" spellcheck="false" />' +
          '</label></div>' +
        '<div class="gow-cx-mat-grid">' +
          (mats.length ? mats.map(function (m) {
            return '<div class="gow-cx-mat"><span>' + esc(m.name) + '</span><b>' + Number(m.qty).toLocaleString(window.GowI18n.lang) + '</b></div>';
          }).join('') : '<div class="gow-cx-empty">' + esc(tr('codex_empty_filter')) + '</div>') +
        '</div>' +
      '</section>'
    ) : '';

    return '<div class="gow-cx-scroll"><div class="gow-cx-hero-grid">' +
      '<section class="gow-cx-hero-card">' +
        '<div class="gow-fs-kicker">' + esc(tr('codex_hero_save')) + '</div>' +
        '<dl class="gow-fs-codex-grid">' + saveRows.map(function (r) {
          return '<dt>' + esc(r[0]) + '</dt><dd>' + esc(r[1]) + '</dd>';
        }).join('') + '</dl>' +
      '</section>' +
      (walletRows.length ? '<section class="gow-cx-hero-card"><div class="gow-fs-kicker">' + esc(tr('codex_hero_wallet')) + '</div>' +
        '<dl class="gow-fs-codex-grid">' + walletRows.map(function (r) {
          return '<dt>' + esc(r[0]) + '</dt><dd>' + esc(r[1]) + '</dd>';
        }).join('') + '</dl></section>' : '') +
      (gearHtml ? '<section class="gow-cx-hero-card"><div class="gow-fs-kicker">' + esc(tr('codex_hero_loadout')) + '</div>' + gearHtml + '</section>' : '') +
      (colHtml ? '<section class="gow-cx-hero-card"><div class="gow-fs-kicker">' + esc(colTitle) + '</div>' + colHtml + '</section>' : '') +
      matsHtml +
    '</div></div>';
  }

  function probeBookTextures() {
    if (S.bookTexChecked) return;
    S.bookTexChecked = true;
    var img = new Image();
    img.onload = function () {
      if (img.naturalWidth > 16) {
        S.bookTexReady = true;
        var st = $('gowFsCodexBody') && $('gowFsCodexBody').querySelector('.gow-book-stage');
        if (st) st.classList.add('has-game-book');
      }
    };
    img.src = '/api/codex/book/page.png';
  }

  function renderCodex() {
    var body = $('gowFsCodexBody');
    var modal = $('gowFsCodexModal');
    if (!body) return;
    var sum = (S.codex && S.codex.summary) || (S.data && S.data.codex_summary) || {};
    var bTot = S.codexValhalla ? sum.bestiary_total : (sum.bestiary_main_total || sum.bestiary_total);
    var bUnl = S.codexValhalla ? sum.bestiary_unlocked : (sum.bestiary_main_unlocked != null ? sum.bestiary_main_unlocked : sum.bestiary_unlocked);
    var lTot = S.codexValhalla ? sum.lore_total : (sum.lore_main_total || sum.lore_total);
    var lUnl = S.codexValhalla ? sum.lore_unlocked : (sum.lore_main_unlocked != null ? sum.lore_main_unlocked : sum.lore_unlocked);
    var tTot = sum.treasures_total || ((S.codex && S.codex.treasures) ? S.codex.treasures.length : 0);
    var tFound = sum.treasures_found != null ? sum.treasures_found : 0;
    var heroLvl = ((S.codex && S.codex.hero) || (S.data && S.data.hero) || {}).power_level;

    var tabs = [
      { key: 'bestiary', label: tr('codex_tab_bestiary'), meta: bTot ? (bUnl + '/' + bTot) : '' },
      { key: 'lore', label: tr('codex_tab_lore'), meta: lTot ? (lUnl + '/' + lTot) : '' },
      { key: 'treasures', label: tr('codex_tab_treasures'), meta: tTot ? (tFound + '/' + tTot) : '' },
      { key: 'skills', label: tr('codex_tab_skills'), meta: sum.skills_total ? (sum.skills_gold + '/' + sum.skills_total) : '' },
      { key: 'hero', label: tr('codex_tab_hero'), meta: heroLvl ? (tr('codex_lvl') + ' ' + heroLvl) : '' }
    ];

    var isBookTab = S.codexTab === 'bestiary' || S.codexTab === 'lore' || S.codexTab === 'treasures';
    var useBook = S.codexBookMode && isBookTab;
    body.classList.toggle('is-book-mode', useBook);
    body.classList.toggle('gow-fs-plate', !useBook);
    if (modal) modal.classList.toggle('is-book-open', useBook);
    if (useBook) probeBookTextures();

    var content = '';
    if (useBook) content = renderCodexBook(S.codexTab, tabs);
    else if (isBookTab) content = renderCodexMasterDetail(S.codexTab);
    else if (S.codexTab === 'skills') content = renderCodexSkills();
    else content = renderCodexHero();

    var focusedId = document.activeElement && body.contains(document.activeElement) ? document.activeElement.id : null;
    var selStart = focusedId && document.activeElement.selectionStart;

    var modeToggleBtn = isBookTab
      ? '<button type="button" class="gow-cx-pill gow-cx-mode-toggle' + (useBook ? ' is-on' : '') + '" data-cx-book-mode="1">' +
          GOW_SVG.book_open + '<span>' + esc(useBook ? tr('codex_dark_mode') : tr('codex_book_mode')) + '</span></button>'
      : '';

    if (useBook) {
      var hasActiveFilter = !!(S.codexQuery.trim() || S.codexStatus !== 'all' || S.codexValhalla || !S.codexSpoiler);
      body.innerHTML =
        '<div class="gow-book-float-top">' +
          '<button type="button" class="gow-book-tool-btn' + (S.bookToolsOpen || hasActiveFilter ? ' is-on' : '') +
            '" data-cx-tools-toggle="1" title="' + esc(tr('codex_filters')) + '">' + GOW_SVG.search + '</button>' +
          modeToggleBtn +
          '<span class="gow-cx-live' + (S.codexLive ? ' is-live' : '') + '" id="gowCodexLivePill" title="' + esc(tr('codex_live_tip')) + '">' +
            '<i></i><span>' + esc(tr('codex_live')) + '</span></span>' +
        '</div>' +
        '<div class="gow-cx-body gow-book-body' + (S.codexMobileDetail ? ' is-mobile-detail' : '') + '">' + content + '</div>' +
        '<footer class="gow-book-footer">' +
          '<button type="button" class="gow-book-foot-btn" data-cx-cats-toggle="1">' +
            '<span class="gow-book-key">TAB</span><span>' + esc(S.bookCatOpen ? tr('codex_select') : tr('codex_categories')) + '</span>' +
          '</button>' +
          '<button type="button" class="gow-book-foot-btn" data-close-codex title="Esc">' +
            '<span class="gow-book-key">ESC</span><span>' + esc(S.bookCatOpen ? tr('codex_back') : tr('codex_exit')) + '</span>' +
          '</button>' +
        '</footer>';
      if (S.bookTexReady) {
        var stEl = body.querySelector('.gow-book-stage');
        if (stEl) stEl.classList.add('has-game-book');
      }
    } else {
      body.innerHTML =
        '<div class="gow-cx-header">' +
          '<div class="gow-cx-title-row">' +
            '<div><div class="gow-fs-kicker">CODEX</div><h2 class="gow-fs-codex-title">' + esc(tr('codex_title')) + '</h2></div>' +
            '<div class="gow-cx-head-right">' +
              modeToggleBtn +
              '<span class="gow-cx-live' + (S.codexLive ? ' is-live' : '') + '" id="gowCodexLivePill" title="' + esc(tr('codex_live_tip')) + '">' +
                '<i></i><span>' + esc(tr('codex_live')) + '</span></span>' +
              tr('s086') + GOW_SVG.close + '</button>' +
            '</div>' +
          '</div>' +
          '<nav class="gow-cx-tabs" role="tablist">' +
            tabs.map(function (tb) {
              return '<button type="button" role="tab" aria-selected="' + (S.codexTab === tb.key) + '" class="gow-cx-tab' +
                (S.codexTab === tb.key ? ' is-active' : '') + '" data-cx-tab="' + tb.key + '">' +
                '<span>' + esc(tb.label) + '</span>' + (tb.meta ? '<em>' + esc(tb.meta) + '</em>' : '') + '</button>';
            }).join('') +
          '</nav>' +
        '</div>' +
        '<div class="gow-cx-body' + (S.codexMobileDetail && isBookTab ? ' is-mobile-detail' : '') + '">' + content + '</div>';
    }

    if (focusedId) {
      var inp = $(focusedId);
      if (inp) {
        inp.focus({ preventScroll: true });
        if (typeof selStart === 'number' && inp.setSelectionRange) {
          try { inp.setSelectionRange(selStart, selStart); } catch (e) {}
        }
      }
    }
  }

  function openCodex(tab, entryId) {
    if (tab) {
      S.codexTab = tab;
      S.codexCat = '';
      S.codexQuery = '';
      S.codexStatus = 'all';
      S.treasureFilter = 'all';
    }
    if (entryId) {
      S.codexSelectedId = entryId;
      S.codexMobileDetail = true;
      S.bookCatOpen = false;
      delete S.codexNewIds[entryId];
      if (S.codex && tab === 'bestiary') {
        var found = (S.codex.bestiary || []).filter(function (e) { return e.id === entryId; })[0];
        if (found && found.is_valhalla) S.codexValhalla = true;
      }
      updateCodexBadge();
    } else {
      S.bookCatOpen = true;
      S.bookToolsOpen = false;
    }
    $('gowFsCodexModal').classList.add('open');
    if (map && map.setPaused) map.setPaused(true);
    if (!S.codex) {
      renderCodex();
      fetchCodex(false);
    } else {
      renderCodex();
    }
    var closeBtn = $('gowFsCodexModal').querySelector('[data-close-codex]');
    if (closeBtn) closeBtn.focus({ preventScroll: true });
  }
  function closeCodex() {
    var m = $('gowFsCodexModal');
    if (!m.classList.contains('open')) return false;
    m.classList.remove('open');
    S.codexMobileDetail = false;
    if (map && map.setPaused) map.setPaused(false);
    return true;
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
    if (poiLayer) poiLayer.clearLayers();
    markerById = {};
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
    routeToTarget({ lat: p.lat, lng: p.lng, label: p.label || f.name, color: '#e5c378', realm: p.realm, fitView: true });
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
    routeToTarget({ pinId: pins[0].id, realm: S.realmLoaded, openDrawer: true, fitView: pins.length === 1 });
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
      if (map && (down(4) || down(5)) && now - padLastAt > 200) {
        if (down(4)) map.zoomOut(); else map.zoomIn();
        padLastAt = now;
      }
      if (map && map.hasWebGL2 && pad.axes && pad.axes.length >= 4) {
        var rx = pad.axes[2] || 0, ry = pad.axes[3] || 0;
        if (Math.abs(rx) > 0.18) {
          map.yawDeg -= (rx - (rx > 0 ? 0.18 : -0.18)) * 1.9;
          map.dirty = true;
        }
        if (Math.abs(ry) > 0.18) {
          map.autoPitch = false;
          map.pitchDeg = Math.max(0, Math.min(62, map.pitchDeg - (ry - (ry > 0 ? 0.18 : -0.18)) * 1.4));
          map.mode3D = map.pitchDeg > 2;
          map.dirty = true;
        }
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
    $('gowFsCodexBtn').addEventListener('click', function () { openCodex(); });
    $('gowFsCodexModal').addEventListener('click', function (e) {
      if (e.target.id === 'gowFsCodexModal' || e.target.closest('[data-close-codex]')) { closeCodex(); return; }
      var tab = e.target.closest('[data-cx-tab]');
      if (tab) {
        var nextTab = tab.getAttribute('data-cx-tab');
        if (nextTab === S.codexTab && S.codexBookMode) {
          S.bookCatOpen = !S.bookCatOpen;
        } else {
          S.codexTab = nextTab;
          S.codexCat = ''; S.codexQuery = ''; S.codexMobileDetail = false;
          S.bookCatOpen = true;
        }
        renderCodex(); return;
      }
      if (e.target.closest('[data-cx-tools-toggle]')) {
        S.bookToolsOpen = !S.bookToolsOpen; renderCodex();
        if (S.bookToolsOpen && $('gowCxSearch')) $('gowCxSearch').focus();
        return;
      }
      if (e.target.closest('[data-cx-cats-toggle]')) {
        S.bookCatOpen = !S.bookCatOpen; renderCodex(); return;
      }
      if (e.target.closest('[data-cx-book-mode]')) {
        S.codexBookMode = !S.codexBookMode; S.bookToolsOpen = false; savePrefs(); renderCodex(); return;
      }
      var trf = e.target.closest('[data-cx-tr-filter]');
      if (trf) { S.treasureFilter = trf.getAttribute('data-cx-tr-filter'); S.codexMobileDetail = false; S.bookCatOpen = false; renderCodex(); return; }
      var cat = e.target.closest('[data-cx-cat]');
      if (cat) { S.codexCat = cat.getAttribute('data-cx-cat'); S.codexMobileDetail = false; S.bookCatOpen = false; renderCodex(); return; }
      var st = e.target.closest('[data-cx-status]');
      if (st) { S.codexStatus = st.getAttribute('data-cx-status'); renderCodex(); return; }
      if (e.target.closest('[data-cx-sort]')) {
        S.codexSort = S.codexSort === 'alpha' ? 'unlocked' : 'alpha'; savePrefs(); renderCodex(); return;
      }
      if (e.target.closest('[data-cx-valhalla]')) {
        S.codexValhalla = !S.codexValhalla; savePrefs(); updateCodexBadge(); renderCodex(); return;
      }
      if (e.target.closest('[data-cx-spoiler]')) {
        S.codexSpoiler = !S.codexSpoiler; savePrefs(); renderCodex(); return;
      }
      var zImg = e.target.closest('[data-cx-zoom-img]');
      if (zImg && !zImg.disabled) {
        openLightbox(zImg.getAttribute('data-cx-zoom-img'));
        return;
      }
      var rBtn = e.target.closest('[data-cx-route-pin]');
      if (rBtn) {
        var rPin = rBtn.getAttribute('data-cx-route-pin');
        var rRealm = rBtn.getAttribute('data-cx-route-realm');
        closeCodex();
        routeToTarget({ pinId: rPin, realm: rRealm || null, openDrawer: true, fitView: true });
        return;
      }
      var jump = e.target.closest('[data-cx-jump-pin]');
      if (jump) {
        var jPin = jump.getAttribute('data-cx-jump-pin');
        var jRealm = jump.getAttribute('data-cx-jump-realm');
        closeCodex();
        routeToTarget({ pinId: jPin, realm: jRealm || null, openDrawer: true, fitView: true });
        return;
      }
      var sel = e.target.closest('[data-cx-select]');
      if (sel) {
        S.codexSelectedId = sel.getAttribute('data-cx-select');
        S.codexMobileDetail = true;
        S.bookCatOpen = false;
        delete S.codexNewIds[S.codexSelectedId];
        updateCodexBadge();
        renderCodex(); return;
      }
      if (e.target.closest('[data-cx-back]')) { S.codexMobileDetail = false; renderCodex(); return; }
      var rev = e.target.closest('[data-cx-reveal]');
      if (rev) { S.codexRevealed[rev.getAttribute('data-cx-reveal')] = true; renderCodex(); return; }
      var sf = e.target.closest('[data-cx-skill-filter]');
      if (sf) { S.codexSkillFilter = sf.getAttribute('data-cx-skill-filter'); renderCodex(); return; }
    });
    $('gowFsCodexModal').addEventListener('input', function (e) {
      if (e.target.id === 'gowCxSearch') { S.codexQuery = e.target.value; renderCodex(); }
      else if (e.target.id === 'gowCxMatSearch') { S.codexMaterialQuery = e.target.value; renderCodex(); }
    });
    $('gowCodexToastOpen').addEventListener('click', function () {
      $('gowCodexToast').hidden = true;
      var act = S.codexToastAction || { tab: 'bestiary' };
      openCodex(act.tab, act.id);
    });
    $('gowCodexToastClose').addEventListener('click', function () { $('gowCodexToast').hidden = true; });
    $('gowFsLeftToggle').addEventListener('click', toggleLeft);
    $('gowFsSearch').addEventListener('input', function (e) {
      S.query = e.target.value.trim().toLowerCase();
      if ($('gowFsSearchClear')) $('gowFsSearchClear').hidden = !e.target.value;
      renderMarkers();
    });
    if ($('gowFsSearchClear')) {
      $('gowFsSearchClear').addEventListener('click', function () {
        $('gowFsSearch').value = '';
        S.query = '';
        $('gowFsSearchClear').hidden = true;
        renderMarkers();
        $('gowFsSearch').focus();
      });
    }
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
    $('gowFs3D').addEventListener('click', function () {
      if (!map || !map.setMode3D) return;
      map.setMode3D(!map.mode3D);
      syncCameraControls();
    });
    $('gowFsRotL').addEventListener('click', function () { map && map.rotateBy && map.rotateBy(-35); });
    $('gowFsRotR').addEventListener('click', function () { map && map.rotateBy && map.rotateBy(35); });
    $('gowFsCompass').addEventListener('click', function () { map && map.resetNorth && map.resetNorth(); });
    $('gowFsNearest').addEventListener('click', function () { jumpToNearestMissing(false); });
    $('gowFsRoute').addEventListener('click', toggleClearingRoute);
    $('gowFsRouteClear').addEventListener('click', function (e) { e.stopPropagation(); clearClearingRoute(); });
    $('gowFsRoutePill').addEventListener('click', function (e) {
      if (e.target.closest('#gowFsRouteClear')) return;
      if (S.routeMode === 'single' && S.routeTarget) {
        if (map) map.flyTo([S.routeTarget.lat, S.routeTarget.lng], Math.max(map.getZoom(), 12.5), { duration: 0.6 });
        if (S.routeTarget.pinId && findPoi(S.routeTarget.pinId)) openDrawer(S.routeTarget.pinId);
        return;
      }
      if (!S.routePins.length) return;
      var first = S.routePins[0];
      if (map) map.flyTo([first.lat, first.lng], Math.max(map.getZoom(), 12.5), { duration: 0.6 });
      openDrawer(first.id, true);
    });
    $('gowFsWake').addEventListener('click', toggleWakeLock);
    function isFullscreen() {
      return Boolean(document.fullscreenElement || document.webkitFullscreenElement);
    }
    function syncFullscreenButton() {
      var btn = $('gowFsFullscreen');
      if (!btn) return;
      var root = document.documentElement;
      var supported = Boolean(
        document.fullscreenEnabled || document.webkitFullscreenEnabled ||
        (root && (root.requestFullscreen || root.webkitRequestFullscreen))
      );
      btn.hidden = !supported;
      var on = isFullscreen();
      var label = tr(on ? 'ctl_fullscreen_exit' : 'ctl_fullscreen');
      btn.classList.toggle('is-on', on);
      btn.setAttribute('aria-pressed', on ? 'true' : 'false');
      btn.setAttribute('aria-label', label);
      btn.title = label;
      btn.innerHTML = on ? GOW_SVG.fullscreen_exit : GOW_SVG.fullscreen;
      if (map && map.invalidateSize) setTimeout(function () { map.invalidateSize(); }, 80);
    }
    function toggleFullscreen() {
      try {
        if (isFullscreen()) {
          var exitFn = document.exitFullscreen || document.webkitExitFullscreen;
          if (exitFn) {
            var pExit = exitFn.call(document);
            if (pExit && typeof pExit.then === 'function') pExit.then(syncFullscreenButton, function () {});
            else setTimeout(syncFullscreenButton, 50);
          }
        } else {
          var el = document.documentElement;
          if (el && el.requestFullscreen) {
            var pReq = null;
            try { pReq = el.requestFullscreen({ navigationUI: 'hide' }); } catch (_) { pReq = el.requestFullscreen(); }
            if (pReq && typeof pReq.then === 'function') pReq.then(syncFullscreenButton, function () {});
            else setTimeout(syncFullscreenButton, 50);
          } else if (el && el.webkitRequestFullscreen) {
            el.webkitRequestFullscreen();
            setTimeout(syncFullscreenButton, 50);
          }
        }
      } catch (_) {}
    }
    if ($('gowFsFullscreen')) {
      $('gowFsFullscreen').addEventListener('click', toggleFullscreen);
      document.addEventListener('fullscreenchange', syncFullscreenButton);
      document.addEventListener('webkitfullscreenchange', syncFullscreenButton);
      syncFullscreenButton();
    }
    document.addEventListener('visibilitychange', function () {
      if (document.visibilityState === 'visible' && S.wakeLockOn && !S.wakeSentinel) acquireWakeLock(true);
    });
    $('gowFsTrail').addEventListener('click', function () {
      S.showTrail = !S.showTrail; savePrefs();
      $('gowFsTrail').classList.toggle('on', S.showTrail);
      if (map && map.setShowTrail) map.setShowTrail(S.showTrail);
    });
    if ($('gowFsWeather')) {
      $('gowFsWeather').classList.toggle('on', S.weatherOn);
      $('gowFsWeather').addEventListener('click', function () {
        S.weatherOn = !S.weatherOn; savePrefs();
        $('gowFsWeather').classList.toggle('on', S.weatherOn);
        if (map && map.setWeatherEnabled) map.setWeatherEnabled(S.weatherOn);
      });
    }
    $('gowFsBeaconClear').addEventListener('click', function (e) {
      e.stopPropagation();
      clearBeacon();
    });
    $('gowFsBeaconPill').addEventListener('click', function (e) {
      if (e.target.closest('#gowFsBeaconClear') || !S.beaconTarget) return;
      S.follow = false; $('gowFsFollow').classList.remove('on'); savePrefs();
      if (map) map.flyTo([S.beaconTarget.lat, S.beaconTarget.lng], Math.max(map.getZoom(), 12.5), { duration: 0.6 });
      if (S.beaconPinId && findPoi(S.beaconPinId)) openDrawer(S.beaconPinId, S.autoAdvanceBeacon);
    });
    $('gowFsTrail').classList.toggle('on', S.showTrail);
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
      var rp = e.target.closest('[data-route-pin]');
      if (rp) {
        routeToTarget({
          pinId: rp.getAttribute('data-route-pin'),
          realm: rp.getAttribute('data-route-realm') || S.realmLoaded,
          openDrawer: true,
          fitView: true
        });
        return;
      }
      var ob = e.target.closest('[data-open-bestiary]');
      if (ob) { openCodex(ob.getAttribute('data-open-codex-tab') || 'bestiary', ob.getAttribute('data-open-bestiary')); return; }
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
      if (e.key === 'Tab') {
        e.preventDefault();
        if ($('gowFsCodexModal').classList.contains('open') && S.codexBookMode &&
            (S.codexTab === 'bestiary' || S.codexTab === 'lore' || S.codexTab === 'treasures')) {
          S.bookCatOpen = !S.bookCatOpen; renderCodex(); return;
        }
        toggleLeft(); return;
      }
      var t = e.target;
      if (t && (t.tagName === 'INPUT' || t.tagName === 'SELECT' || t.tagName === 'TEXTAREA')) return;
      if (e.ctrlKey || e.altKey || e.metaKey) return;
      if (/^Arrow(Up|Down|Left|Right)$/.test(e.key)) {
        if ($('gowFsCodexModal').classList.contains('open') &&
            (S.codexTab === 'bestiary' || S.codexTab === 'lore' || S.codexTab === 'treasures') &&
            (e.key === 'ArrowUp' || e.key === 'ArrowDown')) {
          e.preventDefault();
          var list = filteredCodexEntries(S.codexTab);
          if (list.length) {
            var curIdx = list.findIndex(function (x) { return x.id === S.codexSelectedId; });
            var nextIdx = curIdx < 0 ? 0 : (curIdx + (e.key === 'ArrowDown' ? 1 : -1) + list.length) % list.length;
            S.codexSelectedId = list[nextIdx].id;
            renderCodex();
            var actItem = $('gowCxList') && $('gowCxList').querySelector('.gow-cx-item.is-active');
            if (actItem) actItem.scrollIntoView({ block: 'nearest' });
          }
          return;
        }
        e.preventDefault(); moveHudFocus(e.key === 'ArrowUp' || e.key === 'ArrowLeft'); return;
      }
      if (/^[0-9]$/.test(e.key)) {
        var idx = e.key === '0' ? 9 : Number(e.key) - 1;
        if (REALM_ORDER[idx]) switchGowRealm(REALM_ORDER[idx]);
      } else if (e.code === 'KeyT' || e.key === 't' || e.key === 'T') {
        if (map && map.setMode3D) { map.setMode3D(!map.mode3D); syncCameraControls(); }
      } else if (e.code === 'BracketLeft' || e.key === '[') {
        map && map.rotateBy && map.rotateBy(-30);
      } else if (e.code === 'BracketRight' || e.key === ']') {
        map && map.rotateBy && map.rotateBy(30);
      } else if (e.code === 'KeyN' || e.key === 'n' || e.key === 'N') {
        jumpToNearestMissing(false);
      } else if (e.code === 'KeyM' || e.key === 'm' || e.key === 'M') {
        toggleClearingRoute();
      } else if (e.code === 'KeyK' || e.key === 'k' || e.key === 'K') {
        if ($('gowFsCodexModal').classList.contains('open')) closeCodex();
        else openCodex();
      } else if (e.code === 'KeyF' || e.key === 'f' || e.key === 'F') {
        toggleFullscreen();
      } else if (e.key === '+' || e.key === '=') {
        map && map.zoomIn();
      } else if (e.key === '-' || e.key === '_') {
        map && map.zoomOut();
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
    var fetchStartedAt = Date.now();
    var url = '/api/map?lang=' + window.GowI18n.lang + (S.realm ? '&realm=' + encodeURIComponent(S.realm) : '');
    try {
      var savedMarks = JSON.parse(localStorage.getItem('gowMarks') || '{}');
      url += '&marked=' + encodeURIComponent(Object.keys(savedMarks).filter(function (id) { return savedMarks[id]; }).join(','));
    } catch (e) { /* Storage may be unavailable. */ }
    S.inflight = fetch(url, { cache: 'no-store' })
      .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(function (d) {
        if (!d || !d.ok || !d.realms_map) throw new Error(tr('s106'));
        if (S.lastTelemetryAt && S.lastTelemetryAt > fetchStartedAt && S.data && S.data.live_telemetry) {
          d.live_telemetry = S.data.live_telemetry;
        }
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
        if (S.pendingRoute && (!S.pendingRoute.realm || S.pendingRoute.realm === S.realmLoaded)) {
          var pr = S.pendingRoute; S.pendingRoute = null; routeToTarget(pr);
        }
        if (S.pendingGuidePoint && S.realm === S.realmLoaded) {
          var gp = S.pendingGuidePoint; S.pendingGuidePoint = null; focusGuidePoint(gp.id, gp.index);
        }
        if (S.pendingOpen && findPoi(S.pendingOpen)) { var po = S.pendingOpen; S.pendingOpen = null; focusPin(po); }
        else if (S.selectedId && changed && $('gowFsRightDrawer').classList.contains('open')) openDrawer(S.selectedId);
        if (S.autoAdvanceBeacon && S.beaconPinId) {
          var bp = findPoi(S.beaconPinId);
          if (bp && poiState(bp) === 'collected') {
            if (S.routeActive && S.routeMode === 'tour') buildClearingRoute(false);
            else jumpToNearestMissing(true);
          }
        } else if (S.routeActive && changed) {
          if (S.routeMode === 'tour') buildClearingRoute(false);
          else if (S.routeMode === 'single' && S.routeTarget) {
            routeToTarget({
              pinId: S.routeTarget.pinId,
              lat: S.routeTarget.lat,
              lng: S.routeTarget.lng,
              label: S.routeTarget.label,
              color: S.routeTarget.color,
              realm: S.realmLoaded,
              openDrawer: false,
              fitView: false
            });
          }
        }
        renderBeaconPill();
        renderRoutePill();
        updateCodexBadge();
        if (!S.codex && !S.codexLoading) fetchCodex(true);
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
    connectStream();
    window.addEventListener('beforeunload', function () {
      clearTimeout(S.guideSeenTimer);
      if (S.sse) { try { S.sse.close(); } catch (e) {} }
    });
    window.addEventListener('resize', function () { if (map) map.invalidateSize(); });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();

/* Lucent OS — 2026 concept mockups: shared shell pieces for both directions.
   Reuses the original app tiles, line glyphs and file icons of ../../lucent.js
   (window.Lucent) and adds per-direction wallpapers, folders and the taskbar.
   Attribute names differ from lucent.js on purpose so its own hydrate() ignores them:
     data-g="name"   line glyph        data-ai="app"   app tile
     data-fi="type"  file icon         data-fo="kind"  folder (per direction)
     data-wall       wallpaper layer   data-taskbar    taskbar
     .wb             window buttons    data-wp="prism-light" small wallpaper thumb */
(function () {
  const root = document.documentElement;
  const DIR = root.dataset.dir;                     // "prism" | "pebble"
  const isDark = () => root.classList.contains('dark');
  let uid = 0;
  const id = p => p + (++uid);

  // ---------------- wallpapers (original) ----------------
  // Prism — "Drift": saturated light behind folded translucent ribbons.
  function prismWall(dark) {
    const g = id('pw');
    const base = dark ? ['#050816', '#0d0a26', '#06142a'] : ['#e4ebff', '#efe4ff', '#dff1ff'];
    const blobs = dark
      ? [['#2747ff', .55, 520, 360, 620], ['#7a2cff', .50, 1980, 300, 700], ['#00a6d6', .38, 1450, 1250, 760], ['#ff3d7f', .30, 2420, 1150, 480]]
      : [['#4f7dff', .62, 560, 380, 640], ['#a46bff', .55, 1960, 280, 680], ['#38d0ff', .50, 1450, 1250, 760], ['#ff7d9c', .45, 2440, 1150, 520], ['#7ff0d8', .35, 120, 1300, 520]];
    const rib = dark
      ? [['#3a62ff', '#8e5bff'], ['#16c6ff', '#4a5bff'], ['#ff4f9a', '#9b4dff']]
      : [['#5d8dff', '#b08bff'], ['#3fd0ff', '#6d7bff'], ['#ff8db0', '#a98bff']];
    const hi = dark ? 'rgba(190,210,255,.55)' : 'rgba(255,255,255,.95)';
    const ribbon = (i, d, op) => `
      <path d="${d}" fill="url(#${g}r${i})" opacity="${op}" filter="url(#${g}s)"/>
      <path d="${d}" fill="none" stroke="url(#${g}h${i})" stroke-width="2.2" opacity=".9"/>`;
    const R = [
      'M-200 1180 C 300 900, 700 1060, 1150 760 S 1900 240, 2760 300 L 2760 520 C 2000 430, 1600 820, 1180 1010 S 400 1240, -200 1460 Z',
      'M-200 1440 C 500 1180, 1000 1320, 1500 1030 S 2200 620, 2760 700 L 2760 900 C 2250 860, 1850 1180, 1450 1300 S 500 1500, -200 1640 Z',
      'M-200 700 C 300 560, 800 760, 1250 520 S 2000 40, 2760 -60 L 2760 80 C 2100 160, 1700 600, 1250 700 S 400 760, -200 900 Z',
    ];
    return `<svg viewBox="0 0 2560 1440" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="${g}b" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${base[0]}"/><stop offset=".5" stop-color="${base[1]}"/><stop offset="1" stop-color="${base[2]}"/></linearGradient>
        <filter id="${g}f" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="150"/></filter>
        <filter id="${g}s" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="3"/></filter>
        ${rib.map(([a, b], i) => `
        <linearGradient id="${g}r${i}" x1="0" y1="1" x2=".35" y2="0"><stop offset="0" stop-color="${a}" stop-opacity="0"/><stop offset=".45" stop-color="${a}" stop-opacity="${dark ? .75 : .55}"/><stop offset=".8" stop-color="${b}" stop-opacity="${dark ? .55 : .42}"/><stop offset="1" stop-color="${b}" stop-opacity=".05"/></linearGradient>
        <linearGradient id="${g}h${i}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="${hi}" stop-opacity="0"/><stop offset=".5" stop-color="${hi}"/><stop offset="1" stop-color="${hi}" stop-opacity="0"/></linearGradient>`).join('')}
      </defs>
      <rect width="2560" height="1440" fill="url(#${g}b)"/>
      <g filter="url(#${g}f)">${blobs.map(([c, o, x, y, r]) => `<circle cx="${x}" cy="${y}" r="${r}" fill="${c}" opacity="${o}"/>`).join('')}</g>
      ${ribbon(2, R[2], .85)}${ribbon(0, R[0], 1)}${ribbon(1, R[1], .9)}
    </svg>`;
  }

  // Pebble — "Clay Hills": paper-cut hills at golden hour, film grain.
  function pebbleWall(dark) {
    const g = id('bw');
    const sky = dark ? ['#16142a', '#2e2140', '#6b3b3e'] : ['#f6e8da', '#f5dccb', '#f0c9b2'];
    const sun = dark ? ['#f3e3c8', .9, 2340, 300, 80] : ['#fff6e8', 1, 2330, 380, 140];
    const hills = dark
      ? ['#5c3a48', '#4b3044', '#3c2a3a', '#34363a', '#261d26', '#18131a']
      : ['#ecc4ab', '#e2ab8f', '#cf9478', '#b7b39a', '#a7795f', '#8a5f4c'];
    const H = [
      'M0 760 C 300 700, 520 640, 820 700 S 1400 820, 1700 720 S 2300 600, 2560 680 V1440 H0Z',
      'M0 860 C 260 800, 600 760, 900 840 S 1500 960, 1900 860 S 2400 780, 2560 820 V1440 H0Z',
      'M0 980 C 400 900, 700 880, 1050 960 S 1600 1060, 2000 990 S 2400 930, 2560 960 V1440 H0Z',
      'M0 1080 C 300 1040, 650 1000, 1000 1060 S 1700 1160, 2100 1090 S 2450 1050, 2560 1070 V1440 H0Z',
      'M0 1190 C 450 1120, 800 1150, 1200 1180 S 1900 1260, 2300 1200 S 2500 1180, 2560 1190 V1440 H0Z',
      'M0 1310 C 500 1260, 900 1290, 1300 1300 S 2000 1360, 2560 1300 V1440 H0Z',
    ];
    return `<svg viewBox="0 0 2560 1440" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="${g}s" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${sky[0]}"/><stop offset=".32" stop-color="${sky[1]}"/><stop offset=".6" stop-color="${sky[2]}"/></linearGradient>
        <radialGradient id="${g}g"><stop offset="0" stop-color="${sun[0]}" stop-opacity=".9"/><stop offset="1" stop-color="${sun[0]}" stop-opacity="0"/></radialGradient>
        <filter id="${g}n"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" stitchTiles="stitch"/><feColorMatrix values="0 0 0 0 .5  0 0 0 0 .4  0 0 0 0 .3  0 0 0 .55 0"/></filter>
        <filter id="${g}d" x="-5%" y="-20%" width="110%" height="140%"><feDropShadow dx="0" dy="-6" stdDeviation="14" flood-color="${dark ? '#000' : '#7a4a30'}" flood-opacity="${dark ? .35 : .16}"/></filter>
      </defs>
      <rect width="2560" height="1440" fill="url(#${g}s)"/>
      <circle cx="${sun[2]}" cy="${sun[3]}" r="${sun[4] * 3.2}" fill="url(#${g}g)" opacity=".7"/>
      <circle cx="${sun[2]}" cy="${sun[3]}" r="${sun[4]}" fill="${sun[0]}" opacity="${sun[1]}"/>
      ${H.map((d, i) => `<path d="${d}" fill="${hills[i]}" filter="url(#${g}d)"/>`).join('')}
      <rect width="2560" height="1440" filter="url(#${g}n)" opacity="${dark ? .22 : .16}"/>
    </svg>`;
  }

  const WALLS = {
    'prism-light': () => prismWall(false), 'prism-dark': () => prismWall(true),
    'pebble-light': () => pebbleWall(false), 'pebble-dark': () => pebbleWall(true),
  };

  // ---------------- folders (per direction) ----------------
  const GLY = { doc: 'doc', dl: 'download', img: 'image', music: 'music', video: 'video', desk: 'desktop', home: 'home' };
  function folder(kind) {
    const L = window.Lucent, gl = GLY[kind];
    const k = id('fo');
    const glyph = gl ? `<g transform="translate(21 27) scale(.92)">${L.sym(gl).replace('<svg', '<svg width="24" height="24" stroke-width="2.1"')}</g>` : '';
    if (DIR === 'prism') {
      return `<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg"><defs>
        <linearGradient id="${k}a" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#6c8dff"/><stop offset="1" stop-color="#5a4fe6"/></linearGradient>
        <linearGradient id="${k}b" x1="0" y1="0" x2=".3" y2="1"><stop offset="0" stop-color="#b9d3ff" stop-opacity=".96"/><stop offset="1" stop-color="#6f9bff" stop-opacity=".92"/></linearGradient></defs>
        <path d="M6 15a4 4 0 0 1 4-4h13.5l5 5H54a4 4 0 0 1 4 4v29a4 4 0 0 1-4 4H10a4 4 0 0 1-4-4z" fill="url(#${k}a)"/>
        <path d="M6 23a4 4 0 0 1 4-4h44a4 4 0 0 1 4 4v27a4 4 0 0 1-4 4H10a4 4 0 0 1-4-4z" fill="url(#${k}b)"/>
        <path d="M10 19.6h44a3.4 3.4 0 0 1 3.4 3.4" stroke="#fff" stroke-width="1.4" fill="none" opacity=".9" stroke-linecap="round"/>
        <g color="#ffffff" opacity=".95">${glyph}</g></svg>`;
    }
    return `<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg"><defs>
      <linearGradient id="${k}b" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f6cf9f"/><stop offset="1" stop-color="#eab079"/></linearGradient></defs>
      <path d="M6 15a4 4 0 0 1 4-4h13.5l5 5H54a4 4 0 0 1 4 4v29a4 4 0 0 1-4 4H10a4 4 0 0 1-4-4z" fill="#d8894f"/>
      <path d="M6 23a4 4 0 0 1 4-4h44a4 4 0 0 1 4 4v27a4 4 0 0 1-4 4H10a4 4 0 0 1-4-4z" fill="url(#${k}b)"/>
      <path d="M6.5 50h51" stroke="#c97a40" stroke-width="1" opacity=".5"/>
      <g color="#9b5a2a" opacity=".75">${glyph}</g></svg>`;
  }

  // ---------------- taskbar ----------------
  const PINNED = ['files', 'firefox', 'docs', 'sheets', 'gimp', 'store', 'settings'];
  const NAMES = { files: 'Files', firefox: 'Firefox', docs: 'Documents', sheets: 'Spreadsheets', gimp: 'GIMP', store: 'Software', settings: 'Settings' };
  function taskbar(el) {
    const L = window.Lucent;
    const active = el.dataset.active || '';
    const run = (el.dataset.run || '').split(',').filter(Boolean);
    const hover = el.dataset.hover || '';
    const startOn = el.dataset.start === 'on';
    el.classList.add('taskbar');
    el.innerHTML = `
      <div class="tb-start ${startOn ? 'on' : ''}">${L.logo(32)}</div>
      <div class="tb-search">${L.sym('search')}<span>Search</span></div>
      <div class="tb-apps">${PINNED.map(a => `<div class="tb-app ${a === active ? 'active' : ''} ${run.includes(a) || a === active ? 'run' : ''} ${a === hover ? 'hover' : ''}" title="${NAMES[a]}">${L.APPS[a]()}</div>`).join('')}</div>
      <div class="tb-tray">
        <div class="tb-t">${L.sym('up')}</div>
        <div class="tb-t tb-kbd">EN</div>
        <div class="tb-grp">${L.sym('wifi')}${L.sym('volume')}<span class="tb-bat">${L.sym('battery')}<span>82%</span></span></div>
        <div class="tb-clock"><b>2:32 PM</b><span>Mon, Nov 9</span></div>
      </div>`;
  }

  function hydrate() {
    const L = window.Lucent;
    document.querySelectorAll('[data-wall]').forEach(e => { e.innerHTML = WALLS[`${DIR}-${isDark() ? 'dark' : 'light'}`](); });
    document.querySelectorAll('[data-wp]').forEach(e => { e.innerHTML = WALLS[e.dataset.wp](); });
    document.querySelectorAll('[data-taskbar]').forEach(taskbar);
    document.querySelectorAll('[data-ai]').forEach(e => { e.classList.add('ai'); e.innerHTML = L.APPS[e.dataset.ai](); });
    document.querySelectorAll('[data-fi]').forEach(e => { e.innerHTML = L.fileIcon(e.dataset.fi); });
    document.querySelectorAll('[data-fo]').forEach(e => { e.innerHTML = folder(e.dataset.fo); });
    document.querySelectorAll('[data-lg]').forEach(e => { e.innerHTML = L.logo(+e.dataset.lg || 30); });
    document.querySelectorAll('.wb').forEach(e => { e.innerHTML = `<i class="min">${L.sym('min')}</i><i class="max">${L.sym('max')}</i><i class="close">${L.sym('x')}</i>`; });
    document.querySelectorAll('[data-g]').forEach(e => { e.outerHTML = L.sym(e.dataset.g).replace('<svg', `<svg class="${e.className}"`); });
  }
  window.LucentConcept = { WALLS, folder };
  // run after lucent.js has defined window.Lucent
  document.addEventListener('DOMContentLoaded', () => setTimeout(hydrate, 0));
})();

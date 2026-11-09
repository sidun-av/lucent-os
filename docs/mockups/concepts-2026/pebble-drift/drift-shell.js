/* Lucent OS 2026 — "Pebble Drift" shell pieces (wallpapers, folders, taskbar).
   Self-contained so ../shell.js (shared by prism/ and pebble/) stays untouched.
   Uses ../../lucent.js (window.Lucent) for app tiles, line glyphs and file icons.
     data-wall               desktop wallpaper, follows the mode (Drift / Drift night)
     data-wp="drift-light"   wallpaper thumb: drift-light, drift-dark, tide-light, tide-dark, aurora-light, aurora-dark
     data-fo="doc"           folder (accent family, coloured by --folder-* tokens)
     data-taskbar            taskbar   data-ai / data-fi / data-g / .wb as in shell.js */
(function () {
  const root = document.documentElement;
  const isDark = () => root.classList.contains('dark');
  let uid = 0;
  const id = p => p + (++uid);

  // shared paper grain overlay (Pebble's material, cool-tinted)
  const grainFilter = (g, dark) => `<filter id="${g}n"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" stitchTiles="stitch"/><feColorMatrix values="0 0 0 0 ${dark ? '.55 0 0 0 0 .6 0 0 0 0 .8' : '.30 0 0 0 0 .32 0 0 0 0 .48'}  0 0 0 .5 0"/></filter>`;
  const grain = (g, dark) => `<rect width="2560" height="1440" filter="url(#${g}n)" opacity="${dark ? .10 : .10}"/>`;

  // ---- Drift (from Prism): saturated light behind folded ribbons; + grain ----
  function drift(dark) {
    const g = id('dw');
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
        ${grainFilter(g, dark)}
        ${rib.map(([a, b], i) => `
        <linearGradient id="${g}r${i}" x1="0" y1="1" x2=".35" y2="0"><stop offset="0" stop-color="${a}" stop-opacity="0"/><stop offset=".45" stop-color="${a}" stop-opacity="${dark ? .75 : .55}"/><stop offset=".8" stop-color="${b}" stop-opacity="${dark ? .55 : .42}"/><stop offset="1" stop-color="${b}" stop-opacity=".05"/></linearGradient>
        <linearGradient id="${g}h${i}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="${hi}" stop-opacity="0"/><stop offset=".5" stop-color="${hi}"/><stop offset="1" stop-color="${hi}" stop-opacity="0"/></linearGradient>`).join('')}
      </defs>
      <rect width="2560" height="1440" fill="url(#${g}b)"/>
      <g filter="url(#${g}f)">${blobs.map(([c, o, x, y, r]) => `<circle cx="${x}" cy="${y}" r="${r}" fill="${c}" opacity="${o}"/>`).join('')}</g>
      ${ribbon(2, R[2], .85)}${ribbon(0, R[0], 1)}${ribbon(1, R[1], .9)}
      ${grain(g, dark)}
    </svg>`;
  }

  // ---- Tide (new): paper-cut swells in the Drift palette, a pale sun / moon ----
  function tide(dark) {
    const g = id('tw');
    const sky = dark ? ['#070a1e', '#141640', '#2c2160'] : ['#eef1ff', '#e3e6ff', '#ecdcf6'];
    const sun = dark ? ['#dfe6ff', .92, 640, 330, 74] : ['#ffffff', 1, 640, 360, 120];
    const layers = dark
      ? ['#262c6e', '#2b2468', '#1f2a5e', '#2a1d52', '#161b44', '#0d1030']
      : ['#c3cdfb', '#b8b2f2', '#9fb0f4', '#a691e6', '#7686e0', '#5a5cc4'];
    const H = [
      'M0 700 C 360 620, 640 700, 980 650 S 1700 520, 2060 600 S 2420 650, 2560 610 V1440 H0Z',
      'M0 840 C 300 780, 700 860, 1040 800 S 1700 700, 2100 780 S 2450 830, 2560 800 V1440 H0Z',
      'M0 960 C 420 900, 760 980, 1120 930 S 1800 860, 2200 940 S 2480 960, 2560 950 V1440 H0Z',
      'M0 1080 C 380 1030, 820 1100, 1220 1060 S 1900 1000, 2300 1070 S 2500 1080, 2560 1075 V1440 H0Z',
      'M0 1190 C 500 1140, 900 1200, 1300 1170 S 2000 1130, 2560 1180 V1440 H0Z',
      'M0 1310 C 520 1270, 1000 1320, 1400 1300 S 2100 1270, 2560 1300 V1440 H0Z',
    ];
    return `<svg viewBox="0 0 2560 1440" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="${g}s" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${sky[0]}"/><stop offset=".4" stop-color="${sky[1]}"/><stop offset=".7" stop-color="${sky[2]}"/></linearGradient>
        <radialGradient id="${g}g"><stop offset="0" stop-color="${sun[0]}" stop-opacity=".9"/><stop offset="1" stop-color="${sun[0]}" stop-opacity="0"/></radialGradient>
        ${layers.map((c, i) => `<linearGradient id="${g}l${i}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="${c}"/><stop offset="1" stop-color="${c}" stop-opacity=".88"/></linearGradient>`).join('')}
        ${grainFilter(g, dark)}
        <filter id="${g}d" x="-5%" y="-20%" width="110%" height="140%"><feDropShadow dx="0" dy="-6" stdDeviation="14" flood-color="${dark ? '#000' : '#2a2f80'}" flood-opacity="${dark ? .4 : .16}"/></filter>
      </defs>
      <rect width="2560" height="1440" fill="url(#${g}s)"/>
      <circle cx="${sun[2]}" cy="${sun[3]}" r="${sun[4] * 3.4}" fill="url(#${g}g)" opacity=".7"/>
      <circle cx="${sun[2]}" cy="${sun[3]}" r="${sun[4]}" fill="${sun[0]}" opacity="${sun[1]}"/>
      ${H.map((d, i) => `<path d="${d}" fill="url(#${g}l${i})" filter="url(#${g}d)"/>`).join('')}
      ${grain(g, dark)}
    </svg>`;
  }

  // ---- Aurora (new): three sweeping light curtains with vertical streaks over a quiet base ----
  function aurora(dark) {
    const g = id('aw');
    const base = dark ? ['#03051a', '#0a0d2e', '#171038'] : ['#f4f6ff', '#e6ebff', '#eee4fb'];
    // [top colour, bottom colour, opacity, path]
    const bands = [
      [dark ? '#2f7bff' : '#7d9bff', dark ? '#25e0ff' : '#5fd6ff', dark ? .85 : .85,
        'M-100 360 C 400 160, 900 520, 1400 330 S 2200 60, 2700 220 L 2700 760 C 2200 600, 1800 900, 1300 860 S 400 700, -100 980 Z'],
      [dark ? '#6a3cff' : '#a88bff', dark ? '#3d5cff' : '#7f95ff', dark ? .75 : .75,
        'M-100 640 C 500 460, 1000 760, 1500 560 S 2300 380, 2700 520 L 2700 1020 C 2200 900, 1800 1120, 1300 1080 S 400 980, -100 1180 Z'],
      [dark ? '#ff4fa3' : '#ff9ccb', dark ? '#9b4dff' : '#b98cff', dark ? .5 : .55,
        'M700 470 C 1100 300, 1800 330, 2700 170 L 2700 560 C 2100 640, 1400 560, 700 490 Z'],
    ];
    return `<svg viewBox="0 0 2560 1440" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="${g}b" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${base[0]}"/><stop offset=".6" stop-color="${base[1]}"/><stop offset="1" stop-color="${base[2]}"/></linearGradient>
        ${bands.map(([t, bt], i) => `<linearGradient id="${g}c${i}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${t}" stop-opacity="0"/><stop offset=".55" stop-color="${t}" stop-opacity=".7"/><stop offset=".85" stop-color="${bt}"/><stop offset="1" stop-color="${bt}" stop-opacity="0"/></linearGradient>`).join('')}
        <filter id="${g}f" x="-10%" y="-20%" width="120%" height="140%"><feGaussianBlur stdDeviation="10 40"/></filter>
        <filter id="${g}t" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".006 .0004" numOctaves="3" seed="7"/><feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  1.6 0 0 0 -.15"/></filter>
        <mask id="${g}m" maskUnits="userSpaceOnUse" x="0" y="0" width="2560" height="1440"><rect width="2560" height="1440" fill="#fff" opacity=".45"/><rect width="2560" height="1440" filter="url(#${g}t)"/></mask>
        <radialGradient id="${g}h" cx=".5" cy="1" r=".8"><stop offset="0" stop-color="${dark ? '#2a3cff' : '#c9d4ff'}" stop-opacity="${dark ? .35 : .6}"/><stop offset="1" stop-color="${dark ? '#2a3cff' : '#c9d4ff'}" stop-opacity="0"/></radialGradient>
        ${grainFilter(g, dark)}
      </defs>
      <rect width="2560" height="1440" fill="url(#${g}b)"/>
      <rect width="2560" height="1440" fill="url(#${g}h)"/>
      <g mask="url(#${g}m)" filter="url(#${g}f)">
        ${bands.map(([, , o, d], i) => `<path d="${d}" fill="url(#${g}c${i})" opacity="${o}"/>`).join('')}
      </g>
      <path d="M0 1250 C 500 1200, 1000 1260, 1500 1230 S 2300 1190, 2560 1220 V1440 H0Z" fill="${dark ? '#04061a' : '#dde3fb'}"/>
      <path d="M0 1330 C 600 1300, 1200 1350, 1800 1320 S 2400 1310, 2560 1325 V1440 H0Z" fill="${dark ? '#02030f' : '#cdd5f6'}"/>
      ${grain(g, dark)}
    </svg>`;
  }

  const WALLS = {
    'drift-light': () => drift(false), 'drift-dark': () => drift(true),
    'tide-light': () => tide(false), 'tide-dark': () => tide(true),
    'aurora-light': () => aurora(false), 'aurora-dark': () => aurora(true),
  };

  // ---- folder: Pebble's shape, accent-family fills via --folder-* tokens ----
  const GLY = { doc: 'doc', dl: 'download', img: 'image', music: 'music', video: 'video', desk: 'desktop', home: 'home' };
  function folder(kind) {
    const L = window.Lucent, gl = GLY[kind];
    const k = id('fo');
    const glyph = gl ? `<g transform="translate(21 27) scale(.92)">${L.sym(gl).replace('<svg', '<svg width="24" height="24" stroke-width="2.1"')}</g>` : '';
    return `<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg"><defs>
      <linearGradient id="${k}b" x1="0" y1="0" x2="0" y2="1"><stop offset="0" style="stop-color:var(--folder-front-top)"/><stop offset="1" style="stop-color:var(--folder-front-bottom)"/></linearGradient></defs>
      <path d="M6 15a4 4 0 0 1 4-4h13.5l5 5H54a4 4 0 0 1 4 4v29a4 4 0 0 1-4 4H10a4 4 0 0 1-4-4z" style="fill:var(--folder-back)"/>
      <path d="M6 23a4 4 0 0 1 4-4h44a4 4 0 0 1 4 4v27a4 4 0 0 1-4 4H10a4 4 0 0 1-4-4z" fill="url(#${k}b)"/>
      <path d="M10 19.6h44a3.4 3.4 0 0 1 3.4 3.4" stroke="#fff" stroke-width="1.2" fill="none" opacity=".55" stroke-linecap="round"/>
      <path d="M6.5 50h51" style="stroke:var(--folder-edge)" stroke-width="1" opacity=".5"/>
      <g style="color:var(--folder-glyph)" opacity=".8">${glyph}</g></svg>`;
  }

  const PINNED = ['files', 'firefox', 'docs', 'sheets', 'gimp', 'store', 'settings'];
  const NAMES = { files: 'Files', firefox: 'Firefox', docs: 'Documents', sheets: 'Spreadsheets', gimp: 'GIMP', store: 'Software', settings: 'Settings' };
  function taskbar(el) {
    const L = window.Lucent;
    const active = el.dataset.active || '';
    const run = (el.dataset.run || '').split(',').filter(Boolean);
    const hover = el.dataset.hover || '';
    el.classList.add('taskbar');
    el.innerHTML = `
      <div class="tb-start ${el.dataset.start === 'on' ? 'on' : ''}">${L.logo(32)}</div>
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
    const mode = isDark() ? 'dark' : 'light';
    document.querySelectorAll('[data-wall]').forEach(e => { e.innerHTML = WALLS[`${e.dataset.wall || 'drift'}-${mode}`](); });
    document.querySelectorAll('[data-wp]').forEach(e => { e.innerHTML = WALLS[e.dataset.wp](); });
    document.querySelectorAll('[data-taskbar]').forEach(taskbar);
    document.querySelectorAll('[data-ai]').forEach(e => { e.classList.add('ai'); e.innerHTML = L.APPS[e.dataset.ai](); });
    document.querySelectorAll('[data-fi]').forEach(e => { e.innerHTML = L.fileIcon(e.dataset.fi); });
    document.querySelectorAll('[data-fo]').forEach(e => { e.innerHTML = folder(e.dataset.fo); });
    document.querySelectorAll('.wb').forEach(e => { e.innerHTML = `<i class="min">${L.sym('min')}</i><i class="max">${L.sym('max')}</i><i class="close">${L.sym('x')}</i>`; });
    document.querySelectorAll('[data-g]').forEach(e => { e.outerHTML = L.sym(e.dataset.g).replace('<svg', `<svg class="${e.className}"`); });
    document.body.dataset.ready = '1';
  }
  window.LucentDrift = { WALLS, folder };
  document.addEventListener('DOMContentLoaded', () => setTimeout(hydrate, 0));
})();

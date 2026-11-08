/* Lucent OS mockups — shared icons, wallpaper and shell components.
   All icons are original drawings for these mockups. */
(function () {
  const dark = () => document.documentElement.classList.contains('dark');

  // ---------- app tiles ----------
  let gid = 0;
  function tile(c1, c2, glyph, opts = {}) {
    const id = 'g' + (++gid);
    const bg = opts.flat
      ? `<rect x="2" y="2" width="60" height="60" rx="15" fill="${c1}"/>`
      : `<defs><linearGradient id="${id}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${c1}"/><stop offset="1" stop-color="${c2}"/></linearGradient></defs>
         <rect x="2" y="2" width="60" height="60" rx="15" fill="url(#${id})"/>`;
    return `<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">${bg}
      <rect x="2.5" y="2.5" width="59" height="59" rx="14.5" fill="none" stroke="${opts.stroke || 'rgba(0,0,0,.08)'}"/>
      <path d="M17 2.5h30a14.5 14.5 0 0 1 14.5 14.5v2C50 12 30 10 2.5 18v-1A14.5 14.5 0 0 1 17 2.5z" fill="#fff" opacity="${opts.flat ? 0 : .10}"/>
      ${glyph}</svg>`;
  }
  const W = '#fff';
  const page = (fill = W, x = 19, y = 13, w = 26, h = 36) =>
    `<path d="M${x + 3} ${y}h${w - 11}l8 8v${h - 11}a3 3 0 0 1-3 3H${x + 3}a3 3 0 0 1-3-3V${y + 3}a3 3 0 0 1 3-3z" fill="${fill}"/><path d="M${x + w - 8} ${y}v6a2 2 0 0 0 2 2h6" fill="${fill}" opacity=".55"/>`;
  const craftFacet = `<path d="M2 46 L46 2 H50 L2 50z" fill="#fff" opacity=".10"/>`;
  const APPS = {
    files: () => tile('#5aa6ff', '#2c63ea',
      `<path d="M13 21a3 3 0 0 1 3-3h10l4 4h18a3 3 0 0 1 3 3v19a3 3 0 0 1-3 3H16a3 3 0 0 1-3-3z" fill="#cfe2ff"/>
       <path d="M13 27a3 3 0 0 1 3-3h32a3 3 0 0 1 3 3v17a3 3 0 0 1-3 3H16a3 3 0 0 1-3-3z" fill="#fff"/>`),
    firefox: () => tile('#2b2160', '#160f3a',
      `<defs><linearGradient id="ffg${gid}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffcf4a"/><stop offset=".5" stop-color="#ff6a3d"/><stop offset="1" stop-color="#d63a8c"/></linearGradient></defs>
       <circle cx="32" cy="32" r="17" fill="url(#ffg${gid})"/>
       <path d="M32 15c-5 5-5 29 0 34M32 15c5 5 5 29 0 34M15.5 27h33M15.5 37h33" stroke="#fff" stroke-width="2" fill="none" opacity=".85"/>
       <path d="M44 14c5 2 9 7 9 13" stroke="#ffcf4a" stroke-width="3" fill="none" stroke-linecap="round"/>`),
    docs: () => tile('#ffffff', '#eef2f8', page('#2f6ff0') +
      `<path d="M24 31h16M24 36h16M24 41h10" stroke="#fff" stroke-width="2.4" stroke-linecap="round"/>`, { stroke: 'rgba(0,0,0,.12)' }),
    sheets: () => tile('#ffffff', '#eef2f8', page('#1e9e5a') +
      `<path d="M23 29h18v13H23zM23 35.5h18M32 29v13" stroke="#fff" stroke-width="2" fill="none"/>`, { stroke: 'rgba(0,0,0,.12)' }),
    slides: () => tile('#ffffff', '#eef2f8', page('#f07a1e') +
      `<rect x="23" y="29" width="18" height="11" rx="1.5" fill="none" stroke="#fff" stroke-width="2"/><path d="M28 44h8" stroke="#fff" stroke-width="2.2" stroke-linecap="round"/>`, { stroke: 'rgba(0,0,0,.12)' }),
    okular: () => tile('#ff7a6b', '#d9373f', page(W, 16, 12, 26, 36) +
      `<circle cx="39" cy="38" r="8" fill="#d9373f" stroke="#fff" stroke-width="3"/><path d="M45 44l6 6" stroke="#fff" stroke-width="4" stroke-linecap="round"/>
       <path d="M21 26h12M21 31h9" stroke="#d9373f" stroke-width="2.2" stroke-linecap="round"/>`),
    pdfarranger: () => tile('#f3f5f9', '#dde3ec',
      `<rect x="14" y="17" width="20" height="28" rx="3" fill="#fff" stroke="#c84040" stroke-width="2"/>
       <rect x="30" y="20" width="20" height="28" rx="3" fill="#e5484d"/>
       <path d="M35 29h10M35 34h10M35 39h6" stroke="#fff" stroke-width="2" stroke-linecap="round"/>
       <path d="M19 51c4 3 10 3 14 0" stroke="#5b6475" stroke-width="2.4" fill="none" stroke-linecap="round"/><path d="M33 47l1 4.5-4.5 1" stroke="#5b6475" stroke-width="2.4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>`, { stroke: 'rgba(0,0,0,.12)' }),
    gimp: () => tile('#ffad5a', '#e5602b',
      `<path d="M42 13l9 9-17 17-9-9z" fill="#fff"/><path d="M25 30l9 9c-2 6-7 10-16 11 1-9 3-16 7-20z" fill="#7a3418"/>
       <circle cx="20" cy="22" r="4" fill="#fff" opacity=".7"/>`),
    krita: () => tile('#c27bff', '#6a39d8',
      `<path d="M14 46c10-2 14-10 18-18s10-14 18-14c-1 9-6 15-14 19s-12 9-22 13z" fill="#fff"/>
       <circle cx="18" cy="20" r="3" fill="#ffd36b"/><circle cx="26" cy="15" r="2.4" fill="#7fe0ff"/>`),
    inkscape: () => tile('#2d3546', '#141821',
      `<path d="M14 44C22 20 42 44 50 20" stroke="#fff" stroke-width="3" fill="none" stroke-linecap="round"/>
       <path d="M14 44L24 24M50 20L40 40" stroke="#8fb4ff" stroke-width="1.6"/>
       <rect x="10.5" y="40.5" width="7" height="7" rx="1.5" fill="#141821" stroke="#fff" stroke-width="2"/>
       <rect x="46.5" y="16.5" width="7" height="7" rx="1.5" fill="#141821" stroke="#fff" stroke-width="2"/>
       <circle cx="24" cy="24" r="3" fill="#8fb4ff"/><circle cx="40" cy="40" r="3" fill="#8fb4ff"/>`),
    darktable: () => tile('#3d434f', '#1b1e25',
      `<circle cx="32" cy="32" r="17" fill="#0f1115" stroke="#59606e" stroke-width="2"/>
       ${[0, 60, 120, 180, 240, 300].map((a, i) => `<path d="M32 32 L32 16 A16 16 0 0 1 45.9 24z" transform="rotate(${a} 32 32)" fill="${['#ff6b5e', '#ffb547', '#ffe14d', '#4fd18b', '#46a8ff', '#a77bff'][i]}" opacity=".95"/>`).join('')}
       <circle cx="32" cy="32" r="6.5" fill="#0f1115"/>`),
    kdenlive: () => tile('#2fd0bf', '#10877b',
      `<rect x="13" y="27" width="38" height="22" rx="3" fill="#fff"/>
       <path d="M13 20l36-6 1.3 7.5-36 6z" fill="#fff"/><path d="M20 19l5 6.5M29 17.5l5 6.5M38 16l5 6.5" stroke="#10877b" stroke-width="3"/>
       <path d="M28 33v11l9-5.5z" fill="#10877b"/>`),
    settings: () => tile('#a4adbd', '#5c6577',
      `<g transform="translate(32 32)" fill="#fff">${Array.from({ length: 8 }, (_, i) => `<rect x="-3.5" y="-19" width="7" height="9" rx="2" transform="rotate(${i * 45})"/>`).join('')}
       <circle r="13"/></g><circle cx="32" cy="32" r="5.5" fill="#6a7385"/>`),
    store: () => tile('#3ed08a', '#159456',
      `<path d="M17 25h30l-2.5 21a3 3 0 0 1-3 2.6H22.5a3 3 0 0 1-3-2.6z" fill="#fff"/>
       <path d="M25 27v-5a7 7 0 0 1 14 0v5" stroke="#fff" stroke-width="3" fill="none" stroke-linecap="round"/>
       <path d="M26 36l4.5 4.5L39 32" stroke="#159456" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>`),
    notepadpp: () => tile('#b5ec7a', '#58ad35',
      `<rect x="12" y="16" width="27" height="35" rx="3" fill="#fff"/>
       <path d="M17 25h17M17 31h17M17 37h11" stroke="#58ad35" stroke-width="2.4" stroke-linecap="round"/>
       <path d="M16 13v6M22 13v6M28 13v6M34 13v6" stroke="#2f6a1b" stroke-width="2.4" stroke-linecap="round"/>
       <path d="M42 22h9M46.5 17.5v9M42 36h9M46.5 31.5v9" stroke="#fff" stroke-width="3" stroke-linecap="round"/>`),
    terminal: () => tile('#3a4150', '#1b1f28',
      `<path d="M18 24l8 7-8 7" stroke="#7ef0a8" stroke-width="3.2" fill="none" stroke-linecap="round" stroke-linejoin="round"/><path d="M30 40h14" stroke="#fff" stroke-width="3.2" stroke-linecap="round"/>`),
    trash: () => tile('rgba(255,255,255,.35)', 'rgba(255,255,255,.15)',
      `<path d="M21 24h22l-2 22a3 3 0 0 1-3 2.7H26a3 3 0 0 1-3-2.7z" fill="#fff" opacity=".9"/><rect x="17" y="18" width="30" height="4" rx="2" fill="#fff"/><path d="M28 18v-2a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke="#fff" stroke-width="2.4" fill="none"/>
       <path d="M28 29v14M36 29v14" stroke="#8a93a5" stroke-width="2" stroke-linecap="round"/>`, { stroke: 'rgba(0,0,0,.10)' }),
    // ArtCraft family — shared diagonal facet motif
    photocraft: () => tile('#ff8a5c', '#ec3f86', craftFacet +
      `<circle cx="41" cy="22" r="6" fill="#fff"/><path d="M12 48l14-18 9 11 6-6 11 13z" fill="#fff"/>`),
    vectorcraft: () => tile('#8a6bff', '#4632d4', craftFacet +
      `<path d="M32 12l9 21-9 18-9-18z" fill="#fff"/><circle cx="32" cy="30" r="3.2" fill="#4632d4"/><path d="M32 30v-12" stroke="#4632d4" stroke-width="2"/>`),
    pdfcraft: () => tile('#ff6464', '#b8204f', craftFacet +
      page(W, 19, 12, 26, 38) + `<path d="M24 34h16M24 40h10" stroke="#b8204f" stroke-width="2.6" stroke-linecap="round"/><path d="M24 28h16" stroke="#b8204f" stroke-width="2.6" stroke-linecap="round"/>`),
    wordcraft: () => tile('#46b2ff', '#2557e6', craftFacet +
      `<path d="M15 19h34M15 27h34M15 35h34M15 43h20" stroke="#fff" stroke-width="3.6" stroke-linecap="round"/>`),
    gridcraft: () => tile('#36dba0', '#0f936a', craftFacet +
      `<rect x="14" y="16" width="36" height="32" rx="4" fill="none" stroke="#fff" stroke-width="3"/><path d="M14 27h36M14 37h36M27 16v32" stroke="#fff" stroke-width="3"/><rect x="28" y="28" width="21" height="8" fill="#fff" opacity=".55"/>`),
    deckcraft: () => tile('#ffc04d', '#f0731c', craftFacet +
      `<rect x="12" y="15" width="40" height="27" rx="4" fill="#fff"/><path d="M32 42v8M24 50h16" stroke="#fff" stroke-width="3.2" stroke-linecap="round"/><path d="M19 35l7-8 6 5 7-9 6 12z" fill="#f0731c"/>`),
    migrate: () => tile('#5aa6ff', '#3b46e0',
      `<rect x="11" y="18" width="20" height="26" rx="3" fill="#fff" opacity=".55"/><rect x="33" y="18" width="20" height="26" rx="3" fill="#fff"/>
       <path d="M18 31h24m-6-6 6 6-6 6" stroke="#3b46e0" stroke-width="3.2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>`),
  };

  // Lucent logo: a lens — circle with refracted highlight
  function logo(size = 30) {
    const id = 'lg' + (++gid);
    return `<svg viewBox="0 0 32 32" width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
      <defs><linearGradient id="${id}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#6fb4ff"/><stop offset=".55" stop-color="#3b6ef5"/><stop offset="1" stop-color="#7a4dff"/></linearGradient></defs>
      <rect x="1" y="1" width="30" height="30" rx="9" fill="url(#${id})"/>
      <circle cx="16" cy="16" r="8.5" fill="none" stroke="#fff" stroke-width="2.6"/>
      <path d="M11.5 14.5a5 5 0 0 1 4-4" stroke="#fff" stroke-width="2.4" stroke-linecap="round" fill="none" opacity=".9"/></svg>`;
  }

  // ---------- symbolic icons (24px, stroke) ----------
  const S = {
    home: '<path d="M4 11l8-7 8 7v8a1.5 1.5 0 0 1-1.5 1.5H15v-6H9v6H5.5A1.5 1.5 0 0 1 4 19z"/>',
    clock: '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
    doc: '<path d="M7 3.5h7l4 4V19a1.5 1.5 0 0 1-1.5 1.5h-9A1.5 1.5 0 0 1 6 19V5a1.5 1.5 0 0 1 1-1.5z"/><path d="M14 3.5V8h4M9 12.5h6M9 16h6"/>',
    download: '<path d="M12 4v11m-4.5-4.5L12 15l4.5-4.5M5 19.5h14"/>',
    image: '<rect x="3.5" y="5" width="17" height="14" rx="2"/><circle cx="9" cy="10" r="1.6"/><path d="M4 17l5-5 4 4 2.5-2.5L20 18"/>',
    music: '<path d="M9 17.5V6l10-2v11.5"/><circle cx="6.5" cy="17.5" r="2.5"/><circle cx="16.5" cy="15.5" r="2.5"/>',
    video: '<rect x="3.5" y="6" width="12.5" height="12" rx="2"/><path d="M16 10.5l4.5-3v9l-4.5-3"/>',
    desktop: '<rect x="3.5" y="4.5" width="17" height="12" rx="2"/><path d="M9 20h6M12 16.5V20"/>',
    drive: '<rect x="3.5" y="7" width="17" height="10" rx="2.5"/><path d="M7 12h5"/><circle cx="16.5" cy="12" r="1" fill="currentColor"/>',
    pc: '<rect x="3.5" y="4.5" width="17" height="11.5" rx="2"/><path d="M8 20h8M12 16v4"/>',
    lock: '<rect x="5.5" y="10.5" width="13" height="9.5" rx="2"/><path d="M8.5 10.5V8a3.5 3.5 0 0 1 7 0v2.5"/>',
    eject: '<path d="M12 5l7 8H5z"/><path d="M5 18.5h14"/>',
    trash: '<path d="M4.5 7h15M9.5 7V5h5v2M6.5 7l1 12.5h9l1-12.5"/>',
    wifi: '<path d="M3 9.5a13 13 0 0 1 18 0M6 13a8.5 8.5 0 0 1 12 0M9 16.4a4 4 0 0 1 6 0"/><circle cx="12" cy="19.3" r="1.1" fill="currentColor"/>',
    volume: '<path d="M4 9.5h3.5L12 5.5v13l-4.5-4H4z"/><path d="M15.5 9a4.5 4.5 0 0 1 0 6M18 6.5a8 8 0 0 1 0 11"/>',
    battery: '<rect x="2.5" y="7" width="17" height="10" rx="2.5"/><path d="M21.5 10.5v3"/><rect x="4.5" y="9" width="10.5" height="6" rx="1" fill="currentColor" stroke="none"/>',
    search: '<circle cx="10.5" cy="10.5" r="6"/><path d="M15 15l5 5"/>',
    left: '<path d="M14.5 5.5L8 12l6.5 6.5"/>',
    right: '<path d="M9.5 5.5L16 12l-6.5 6.5"/>',
    up: '<path d="M12 19V5.5M6 11.5l6-6 6 6"/>',
    down: '<path d="M6 9.5l6 6 6-6"/>',
    grid: '<rect x="4" y="4" width="6.5" height="6.5" rx="1.5"/><rect x="13.5" y="4" width="6.5" height="6.5" rx="1.5"/><rect x="4" y="13.5" width="6.5" height="6.5" rx="1.5"/><rect x="13.5" y="13.5" width="6.5" height="6.5" rx="1.5"/>',
    list: '<path d="M9 6.5h11M9 12h11M9 17.5h11"/><circle cx="4.8" cy="6.5" r="1" fill="currentColor"/><circle cx="4.8" cy="12" r="1" fill="currentColor"/><circle cx="4.8" cy="17.5" r="1" fill="currentColor"/>',
    columns: '<rect x="3.5" y="5" width="17" height="14" rx="2"/><path d="M9.5 5v14M15 5v14"/>',
    split: '<rect x="3.5" y="5" width="17" height="14" rx="2"/><path d="M12 5v14"/>',
    sliders: '<path d="M4 7h9M17 7h3M4 17h3M11 17h9"/><circle cx="15" cy="7" r="2"/><circle cx="9" cy="17" r="2"/>',
    bluetooth: '<path d="M7 7.5l10 9-5 4v-17l5 4-10 9"/>',
    display: '<rect x="3" y="4.5" width="18" height="12" rx="2"/><path d="M8.5 20h7"/>',
    palette: '<path d="M12 3.5a8.5 8.5 0 0 0 0 17c1.4 0 2-1 1.6-2.1-.5-1.4.3-2.4 1.7-2.4h2.1A3.1 3.1 0 0 0 20.5 13 8.5 8.5 0 0 0 12 3.5z"/><circle cx="8" cy="11" r="1.1" fill="currentColor"/><circle cx="11" cy="7.6" r="1.1" fill="currentColor"/><circle cx="15.3" cy="8.4" r="1.1" fill="currentColor"/>',
    users: '<circle cx="9" cy="8.5" r="3.5"/><path d="M3 19.5c.6-3.3 3-5 6-5s5.4 1.7 6 5"/><path d="M15.5 5.3a3.3 3.3 0 0 1 0 6.4M17.8 14.6c1.6.7 2.8 2.3 3.2 4.9"/>',
    refresh: '<path d="M19.5 12a7.5 7.5 0 1 1-2.2-5.3"/><path d="M19.5 4.5v4.2h-4.2"/>',
    undo: '<path d="M9 7.5L4.5 12 9 16.5"/><path d="M4.5 12h10a5 5 0 0 1 0 10H12"/>',
    winapp: '<rect x="3.5" y="4.5" width="17" height="15" rx="2.5"/><path d="M3.5 9h17"/><circle cx="6.6" cy="6.8" r=".6" fill="currentColor"/><circle cx="8.8" cy="6.8" r=".6" fill="currentColor"/>',
    keyboard: '<rect x="2.5" y="6" width="19" height="12" rx="2.5"/><path d="M6 10h.01M9.5 10h.01M13 10h.01M16.5 10h.01M8 14h8"/>',
    check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    info: '<circle cx="12" cy="12" r="8.5"/><path d="M12 11v5.5M12 7.8v.2"/>',
    globe: '<circle cx="12" cy="12" r="8.5"/><path d="M3.5 12h17M12 3.5c-3 3-3 14 0 17M12 3.5c3 3 3 14 0 17"/>',
    star: '<path d="M12 4l2.4 5 5.4.7-4 3.7 1 5.4L12 16.2 7.2 18.8l1-5.4-4-3.7 5.4-.7z"/>',
    shield: '<path d="M12 3.5l7 2.8v5.4c0 4.3-2.9 7.6-7 8.8-4.1-1.2-7-4.5-7-8.8V6.3z"/><path d="M9 12l2 2 4-4"/>',
    x: '<path d="M6.5 6.5l11 11M17.5 6.5l-11 11"/>',
    min: '<path d="M5.5 12h13"/>',
    max: '<rect x="5.5" y="5.5" width="13" height="13" rx="2.5"/>',
    sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M5.3 18.7l1.4-1.4M17.3 6.7l1.4-1.4"/>',
    moon: '<path d="M19.5 14.5A8 8 0 0 1 9.5 4.5a8 8 0 1 0 10 10z"/>',
    chip: '<rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9.5 3v3M14.5 3v3M9.5 18v3M14.5 18v3M3 9.5h3M3 14.5h3M18 9.5h3M18 14.5h3"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    menu: '<path d="M4.5 7h15M4.5 12h15M4.5 17h15"/>',
    more: '<circle cx="6" cy="12" r="1.3" fill="currentColor"/><circle cx="12" cy="12" r="1.3" fill="currentColor"/><circle cx="18" cy="12" r="1.3" fill="currentColor"/>',
    bookmark: '<path d="M7 4h10v16.5l-5-3.8-5 3.8z"/>',
    folder: '<path d="M3.5 7.5a2 2 0 0 1 2-2h4l2 2h7a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-13a2 2 0 0 1-2-2z"/>',
    copy: '<rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V5.5A1.5 1.5 0 0 0 14.5 4h-9A1.5 1.5 0 0 0 4 5.5v9A1.5 1.5 0 0 0 5.5 16H8"/>',
    flask: '<path d="M9.5 3.5h5M10.5 3.5v5.2L5 18a1.8 1.8 0 0 0 1.6 2.5h10.8A1.8 1.8 0 0 0 19 18l-5.5-9.3V3.5"/><path d="M7.5 15h9"/>',
    apps: '<circle cx="6.5" cy="6.5" r="2"/><circle cx="12" cy="6.5" r="2"/><circle cx="17.5" cy="6.5" r="2"/><circle cx="6.5" cy="12" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="17.5" cy="12" r="2"/><circle cx="6.5" cy="17.5" r="2"/><circle cx="12" cy="17.5" r="2"/><circle cx="17.5" cy="17.5" r="2"/>',
    office: '<path d="M7 3.5h7l4 4V19a1.5 1.5 0 0 1-1.5 1.5h-9A1.5 1.5 0 0 1 6 19V5a1.5 1.5 0 0 1 1-1.5z"/><path d="M14 3.5V8h4"/>',
    brush: '<path d="M14.5 4.5l5 5-7.5 7.5-5-5z"/><path d="M7 12c-2.5 1-3 4-3.5 7.5 3.5-.5 6.5-1 7.5-3.5"/>',
    film: '<rect x="3.5" y="5" width="17" height="14" rx="2"/><path d="M8 5v14M16 5v14M3.5 9.5H8M3.5 14.5H8M16 9.5h4.5M16 14.5h4.5"/>',
    game: '<path d="M7 8h10a4 4 0 0 1 4 4.5l-.6 3.6a2.4 2.4 0 0 1-4.2 1L15 15.5H9l-1.2 1.6a2.4 2.4 0 0 1-4.2-1L3 12.5A4 4 0 0 1 7 8z"/><path d="M8 10.5v3M6.5 12h3"/><circle cx="15.5" cy="11" r=".7" fill="currentColor"/><circle cx="17" cy="13" r=".7" fill="currentColor"/>',
    code: '<path d="M8.5 7L3.5 12l5 5M15.5 7l5 5-5 5"/>',
    arrowr: '<path d="M4.5 12h14m-5-5 5 5-5 5"/>',
    cloud: '<path d="M7 18.5a4.5 4.5 0 0 1-.6-9 6 6 0 0 1 11.4 1.6A3.8 3.8 0 0 1 17.5 18.5z"/>',
    pin: '<path d="M9 4h6l-1 6 3 3H7l3-3zM12 13v7"/>',
  };
  function sym(name, extra = '') {
    return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" ${extra}>${S[name] || ''}</svg>`;
  }

  // ---------- file-type icons for file views ----------
  function fileIcon(type) {
    if (type === 'folder' || type.startsWith('folder')) {
      const glyph = { 'folder-doc': S.doc, 'folder-dl': S.download, 'folder-img': S.image, 'folder-music': S.music, 'folder-video': S.video, 'folder-desk': S.desktop }[type] || '';
      return `<svg viewBox="0 0 64 64"><path d="M6 16a4 4 0 0 1 4-4h14l5 5h25a4 4 0 0 1 4 4v29a4 4 0 0 1-4 4H10a4 4 0 0 1-4-4z" fill="#4a8cf7"/>
        <path d="M6 24a4 4 0 0 1 4-4h44a4 4 0 0 1 4 4v26a4 4 0 0 1-4 4H10a4 4 0 0 1-4-4z" fill="#7fb3ff"/>
        ${glyph ? `<g transform="translate(22 27) scale(.85)" fill="none" stroke="#2c63ea" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" opacity=".75">${glyph}</g>` : ''}</svg>`;
    }
    const map = { docx: ['#2f6ff0', 'DOC'], xlsx: ['#1e9e5a', 'XLS'], pdf: ['#e5484d', 'PDF'], pptx: ['#f07a1e', 'PPT'], exe: ['#5b6475', 'EXE'], zip: ['#a77bff', 'ZIP'], txt: ['#8a93a5', 'TXT'] };
    if (type === 'jpg') {
      return `<svg viewBox="0 0 64 64"><rect x="8" y="12" width="48" height="40" rx="5" fill="#fff" stroke="#d6dbe4" stroke-width="1.5"/>
        <defs><linearGradient id="sky${++gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#9ccaff"/><stop offset="1" stop-color="#ffd7b0"/></linearGradient></defs>
        <rect x="11" y="15" width="42" height="34" rx="3" fill="url(#sky${gid})"/><circle cx="42" cy="24" r="4" fill="#fff6d6"/><path d="M11 45l12-14 9 10 6-6 15 14v0a3 3 0 0 1-3 3H14a3 3 0 0 1-3-3z" fill="#3f8f6a"/></svg>`;
    }
    const [c, t] = map[type] || map.txt;
    const isDark = dark();
    return `<svg viewBox="0 0 64 64"><path d="M16 6h22l12 12v36a4 4 0 0 1-4 4H16a4 4 0 0 1-4-4V10a4 4 0 0 1 4-4z" fill="${isDark ? '#e9edf3' : '#fff'}" stroke="${isDark ? 'none' : '#d6dbe4'}" stroke-width="1.5"/>
      <path d="M38 6v8a4 4 0 0 0 4 4h8" fill="#dfe4ec"/>
      ${type === 'exe' ? `<rect x="20" y="24" width="24" height="18" rx="3" fill="none" stroke="${c}" stroke-width="2.4"/><path d="M20 30h24" stroke="${c}" stroke-width="2.4"/>` :
        `<path d="M20 28h22M20 33h22M20 38h14" stroke="#c9cfd9" stroke-width="2" stroke-linecap="round"/>`}
      <rect x="12" y="44" width="28" height="12" rx="3" fill="${c}"/><text x="26" y="53" text-anchor="middle" font-family="Inter,sans-serif" font-size="8.5" font-weight="700" fill="#fff">${t}</text></svg>`;
  }

  // ---------- wallpaper: "Lucent Flow" — soft light ribbons ----------
  function wallpaper() {
    const d = dark();
    const bg = d ? ['#0d1222', '#1a1540', '#0b1a2e'] : ['#e9eefb', '#f6e9f1', '#dde9fb'];
    const blobs = d
      ? [['#3b4cff', .55, 600, 300, 700], ['#8a3dff', .45, 2000, 380, 760], ['#00a3c4', .35, 1300, 1250, 820], ['#ff4f8b', .25, 2350, 1300, 500]]
      : [['#8fb0ff', .75, 520, 260, 760], ['#ffb3cf', .70, 2050, 300, 720], ['#a8e4ff', .70, 1300, 1260, 860], ['#ffd2a6', .60, 2420, 1320, 520], ['#c7b5ff', .55, 80, 1300, 600]];
    const rib = d ? ['rgba(130,150,255,.35)', 'rgba(190,120,255,.28)', 'rgba(90,210,255,.22)'] : ['rgba(255,255,255,.75)', 'rgba(255,255,255,.55)', 'rgba(255,255,255,.40)'];
    return `<svg viewBox="0 0 2560 1440" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="wbg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${bg[0]}"/><stop offset=".5" stop-color="${bg[1]}"/><stop offset="1" stop-color="${bg[2]}"/></linearGradient>
        <filter id="wb1" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="160"/></filter>
        <filter id="wb2" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="18"/></filter>
        <linearGradient id="rg1" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="${rib[0]}" stop-opacity="0"/><stop offset=".35" stop-color="${rib[0]}"/><stop offset="1" stop-color="${rib[0]}" stop-opacity="0"/></linearGradient>
        <linearGradient id="rg2" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="${rib[1]}" stop-opacity="0"/><stop offset=".6" stop-color="${rib[1]}"/><stop offset="1" stop-color="${rib[1]}" stop-opacity="0"/></linearGradient>
        <linearGradient id="rg3" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="${rib[2]}" stop-opacity="0"/><stop offset=".5" stop-color="${rib[2]}"/><stop offset="1" stop-color="${rib[2]}" stop-opacity="0"/></linearGradient>
      </defs>
      <rect width="2560" height="1440" fill="url(#wbg)"/>
      <g filter="url(#wb1)">${blobs.map(([c, o, x, y, r]) => `<circle cx="${x}" cy="${y}" r="${r}" fill="${c}" opacity="${o}"/>`).join('')}</g>
      <g filter="url(#wb2)">
        <path d="M-100 1010 C 500 760, 900 1180, 1450 880 S 2300 560, 2700 760 L 2700 860 C 2300 690, 1900 1000, 1450 1010 S 500 920, -100 1130z" fill="url(#rg1)"/>
        <path d="M-100 1150 C 600 980, 1100 1300, 1700 1060 S 2400 900, 2700 1000 L 2700 1050 C 2350 980, 2000 1200, 1650 1170 S 600 1120, -100 1230z" fill="url(#rg2)"/>
        <path d="M-100 820 C 400 700, 1000 900, 1500 760 S 2200 520, 2700 600 L 2700 630 C 2200 580, 1900 820, 1450 830 S 400 780, -100 880z" fill="url(#rg3)"/>
      </g></svg>`;
  }

  // ---------- taskbar ----------
  const PINNED = ['files', 'firefox', 'docs', 'sheets', 'gimp', 'store', 'settings'];
  function taskbar(el) {
    const active = el.dataset.active || '';
    const run = (el.dataset.run || '').split(',').filter(Boolean);
    const hover = el.dataset.hover || '';
    const extra = (el.dataset.extra || '').split(',').filter(Boolean);
    const apps = [...PINNED, ...extra];
    el.innerHTML = `
      <div class="start"><span class="lg">${logo(30)}</span></div>
      <div class="tsearch">${sym('search')}<span>Поиск</span></div>
      <div class="apps">${apps.map(a => `<div class="di ${a === active ? 'active' : ''} ${run.includes(a) || a === active ? 'run' : ''} ${a === hover ? 'hover' : ''}" data-app="${a}">${APPS[a]()}</div>`).join('')}</div>
      <div class="tray">
        <div class="t">${sym('up')}</div>
        <div class="t"><span class="kbd">RU</span></div>
        <div class="grp">${sym('wifi')}${sym('volume')}<span style="display:flex;align-items:center;gap:6px">${sym('battery')}<span style="font-size:14.5px">82%</span></span></div>
        <div class="clock"><b>14:32</b><span>вс, 8 нояб.</span></div>
      </div>`;
  }

  function titlebars() {
    document.querySelectorAll('.titlebar').forEach(tb => {
      if (tb.dataset.app) tb.insertAdjacentHTML('afterbegin', `<span class="ti"><span style="width:20px;height:20px;display:block">${APPS[tb.dataset.app]()}</span></span>`);
      if (!tb.querySelector('.wb') && !tb.hasAttribute('data-nobuttons'))
        tb.insertAdjacentHTML('beforeend', `<span class="wb"><i>${sym('min')}</i><i>${sym('max')}</i><i class="close">${sym('x')}</i></span>`);
    });
  }

  function hydrate() {
    const w = document.getElementById('wall'); if (w) w.innerHTML = wallpaper();
    const t = document.getElementById('taskbar'); if (t) taskbar(t);
    document.querySelectorAll('[data-icon]').forEach(e => { e.classList.add('appicon'); e.innerHTML = APPS[e.dataset.icon](); });
    document.querySelectorAll('[data-sym]').forEach(e => { e.outerHTML = sym(e.dataset.sym); });
    document.querySelectorAll('[data-file]').forEach(e => { e.innerHTML = fileIcon(e.dataset.file); });
    document.querySelectorAll('[data-logo]').forEach(e => { e.innerHTML = logo(+e.dataset.logo || 30); });
    titlebars();
  }
  window.Lucent = { APPS, sym, fileIcon, logo, wallpaper };
  document.addEventListener('DOMContentLoaded', hydrate);
})();

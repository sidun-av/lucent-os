/* Lucent OS 2026 — "Glass Card" shell pieces. Loads after ../../lucent.js and
   ../pebble-drift/drift-shell.js (which still supplies wallpapers, folders, data-ai/data-g/.wb).
     URL hash: #dark → dark mode, #solid → "Reduce transparency" (opaque fallback); combinable.
     <div data-dock data-active="files" data-run="files:2,okular" data-hover="" data-open="launcher|search">
   The dock = launcher, search, pinned + running apps (dots), separator, compact tray, clock. */
(function () {
  const h = location.hash;
  const root = document.documentElement;
  if (h.includes('dark')) { root.classList.remove('light'); root.classList.add('dark'); }
  if (h.includes('solid')) root.classList.add('solid');

  const PINNED = ['files', 'firefox', 'docs', 'sheets', 'gimp', 'store', 'settings'];
  function dock(el) {
    const L = window.Lucent;
    const runs = Object.fromEntries((el.dataset.run || '').split(',').filter(Boolean).map(s => { const [a, n] = s.split(':'); return [a, +(n || 1)]; }));
    const active = el.dataset.active || '';
    const extra = Object.keys(runs).filter(a => !PINNED.includes(a));
    const app = a => `<div class="dk ${a === active ? 'active' : ''} ${a === el.dataset.hover ? 'hover' : ''}" data-app="${a}"><span class="ai">${L.APPS[a]()}</span>${runs[a] ? `<span class="run">${'<i></i>'.repeat(a === active ? 1 : runs[a])}</span>` : ''}</div>`;
    el.classList.add('dock');
    el.innerHTML = `
      <div class="dk ${el.dataset.open === 'launcher' ? 'open' : ''}" data-app="launcher">${L.logo(40)}</div>
      <div class="dk ${el.dataset.open === 'search' ? 'open' : ''}" data-app="search">${L.sym('search')}</div>
      <div class="dk-sep"></div>
      ${PINNED.map(app).join('')}${extra.map(app).join('')}
      <div class="dk-sep"></div>
      <div class="tray">
        <div class="t">${L.sym('up')}</div>
        <div class="t lang">EN</div>
        <div class="t">${L.sym('wifi')}</div>
        <div class="t">${L.sym('volume')}</div>
        <div class="t bat">${L.sym('battery')}<span>82%</span></div>
        <div class="clock"><b>2:32 PM</b><span>Mon, Nov 9</span></div>
      </div>`;
  }
  document.addEventListener('DOMContentLoaded', () => document.querySelectorAll('[data-dock]').forEach(dock));
  // <div data-anchor="files" data-gap="12">: centre a popover / tooltip above that dock item
  // (clamped to the screen), or above the whole dock with data-anchor="dock".
  window.addEventListener('load', () => document.querySelectorAll('[data-anchor]').forEach(p => {
    const a = p.dataset.anchor === 'dock' ? document.querySelector('.dock') : document.querySelector(`.dock [data-app="${p.dataset.anchor}"]`);
    const r = a.getBoundingClientRect(), w = p.offsetWidth;
    p.style.left = Math.max(16, Math.min(2560 - w - 16, r.left + r.width / 2 - w / 2)) + 'px';
    p.style.bottom = (1440 - document.querySelector('.dock').getBoundingClientRect().top + +(p.dataset.gap || 12)) + 'px';
    document.body.dataset.placed = '1';
  }));
})();

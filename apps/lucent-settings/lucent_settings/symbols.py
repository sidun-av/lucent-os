"""Line symbols, from the mockups' icon set (docs/mockups/lucent.js, drawn
 for Lucent; 24x24, stroke 1.8, round caps), rendered in any colour."""

SYMBOLS = {
    "wifi": '<path d="M3 9.5a13 13 0 0 1 18 0M6 13a8.5 8.5 0 0 1 12 0M9 16.4a4 4 0 0 1 6 0"/><circle cx="12" cy="19.3" r="1.1" fill="currentColor"/>',
    "bluetooth": '<path d="M7 7.5l10 9-5 4v-17l5 4-10 9"/>',
    "display": '<rect x="3" y="4.5" width="18" height="12" rx="2"/><path d="M8.5 20h7"/>',
    "volume": '<path d="M4 9.5h3.5L12 5.5v13l-4.5-4H4z"/><path d="M15.5 9a4.5 4.5 0 0 1 0 6M18 6.5a8 8 0 0 1 0 11"/>',
    "palette": '<path d="M12 3.5a8.5 8.5 0 0 0 0 17c1.4 0 2-1 1.6-2.1-.5-1.4.3-2.4 1.7-2.4h2.1A3.1 3.1 0 0 0 20.5 13 8.5 8.5 0 0 0 12 3.5z"/><circle cx="8" cy="11" r="1.1" fill="currentColor"/><circle cx="11" cy="7.6" r="1.1" fill="currentColor"/><circle cx="15.3" cy="8.4" r="1.1" fill="currentColor"/>',
    "keyboard": '<rect x="2.5" y="6" width="19" height="12" rx="2.5"/><path d="M6 10h.01M9.5 10h.01M13 10h.01M16.5 10h.01M8 14h8"/>',
    "users": '<circle cx="9" cy="8.5" r="3.5"/><path d="M3 19.5c.6-3.3 3-5 6-5s5.4 1.7 6 5"/><path d="M15.5 5.3a3.3 3.3 0 0 1 0 6.4M17.8 14.6c1.6.7 2.8 2.3 3.2 4.9"/>',
    "refresh": '<path d="M19.5 12a7.5 7.5 0 1 1-2.2-5.3"/><path d="M19.5 4.5v4.2h-4.2"/>',
    "winapp": '<rect x="3.5" y="4.5" width="17" height="15" rx="2.5"/><path d="M3.5 9h17"/><circle cx="6.6" cy="6.8" r=".6" fill="currentColor"/><circle cx="8.8" cy="6.8" r=".6" fill="currentColor"/>',
    "info": '<circle cx="12" cy="12" r="8.5"/><path d="M12 11v5.5M12 7.8v.2"/>',
    "search": '<circle cx="10.5" cy="10.5" r="6"/><path d="M15 15l5 5"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M5.3 18.7l1.4-1.4M17.3 6.7l1.4-1.4"/>',
    "moon": '<path d="M19.5 14.5A8 8 0 0 1 9.5 4.5a8 8 0 1 0 10 10z"/>',
    "download": '<path d="M12 4v11m-4.5-4.5L12 15l4.5-4.5M5 19.5h14"/>',
    "undo": '<path d="M9 7.5L4.5 12 9 16.5"/><path d="M4.5 12h10a5 5 0 0 1 0 10H12"/>',
    "check": '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    "x": '<path d="M6.5 6.5l11 11M17.5 6.5l-11 11"/>',
    "min": '<path d="M5.5 12h13"/>',
    "max": '<rect x="5.5" y="5.5" width="13" height="13" rx="2.5"/>',
    "chip": '<rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9.5 3v3M14.5 3v3M9.5 18v3M14.5 18v3M3 9.5h3M3 14.5h3M18 9.5h3M18 14.5h3"/>',
    "lock": '<rect x="5.5" y="10.5" width="13" height="9.5" rx="2"/><path d="M8.5 10.5V8a3.5 3.5 0 0 1 7 0v2.5"/>',
    "folder": '<path d="M3.5 7.5a2 2 0 0 1 2-2h4l2 2h7a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-13a2 2 0 0 1-2-2z"/>',
    "trash": '<path d="M4.5 7h15M9.5 7V5h5v2M6.5 7l1 12.5h9l1-12.5"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "more": '<circle cx="6" cy="12" r="1.3" fill="currentColor"/><circle cx="12" cy="12" r="1.3" fill="currentColor"/><circle cx="18" cy="12" r="1.3" fill="currentColor"/>',
    "left": '<path d="M14.5 5.5L8 12l6.5 6.5"/>',
    "right": '<path d="M9.5 5.5L16 12l-6.5 6.5"/>',
    "down": '<path d="M6 9.5l6 6 6-6"/>',
    "arrowr": '<path d="M4.5 12h14m-5-5 5 5-5 5"/>',
    "shield": '<path d="M12 3.5l7 2.8v5.4c0 4.3-2.9 7.6-7 8.8-4.1-1.2-7-4.5-7-8.8V6.3z"/><path d="M9 12l2 2 4-4"/>',
    "desktop": '<rect x="3.5" y="4.5" width="17" height="12" rx="2"/><path d="M9 20h6M12 16.5V20"/>',
    "pc": '<rect x="3.5" y="4.5" width="17" height="11.5" rx="2"/><path d="M8 20h8M12 16v4"/>',
    "drive": '<rect x="3.5" y="7" width="17" height="10" rx="2.5"/><path d="M7 12h5"/><circle cx="16.5" cy="12" r="1" fill="currentColor"/>',
    "battery": '<rect x="2.5" y="7" width="17" height="10" rx="2.5"/><path d="M21.5 10.5v3"/><rect x="4.5" y="9" width="10.5" height="6" rx="1" fill="currentColor" stroke="none"/>',
    "globe": '<circle cx="12" cy="12" r="8.5"/><path d="M3.5 12h17M12 3.5c-3 3-3 14 0 17M12 3.5c3 3 3 14 0 17"/>',
    "sliders": '<path d="M4 7h9M17 7h3M4 17h3M11 17h9"/><circle cx="15" cy="7" r="2"/><circle cx="9" cy="17" r="2"/>',
    "star": '<path d="M12 4l2.4 5 5.4.7-4 3.7 1 5.4L12 16.2 7.2 18.8l1-5.4-4-3.7 5.4-.7z"/>',
    "copy": '<rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V5.5A1.5 1.5 0 0 0 14.5 4h-9A1.5 1.5 0 0 0 4 5.5v9A1.5 1.5 0 0 0 5.5 16H8"/>',
    "headphones": '<path d="M4.5 14v-2a7.5 7.5 0 0 1 15 0v2"/><rect x="3.5" y="13.5" width="4" height="6.5" rx="1.6"/><rect x="16.5" y="13.5" width="4" height="6.5" rx="1.6"/>',
    "mouse": '<rect x="6.5" y="3.5" width="11" height="17" rx="5.5"/><path d="M12 7v3.5"/>',
    "speaker": '<rect x="6" y="3.5" width="12" height="17" rx="2.5"/><circle cx="12" cy="14" r="3"/><circle cx="12" cy="7.5" r=".9" fill="currentColor"/>',
    "mic": '<rect x="9" y="3.5" width="6" height="11" rx="3"/><path d="M5.5 11.5a6.5 6.5 0 0 0 13 0M12 18v2.5"/>',
    "mute": '<path d="M4 9.5h3.5L12 5.5v13l-4.5-4H4z"/><path d="M16 9.5l5 5M21 9.5l-5 5"/>',
    "cable": '<path d="M8 3.5v4M16 3.5v4M6.5 7.5h11v3a5.5 5.5 0 0 1-11 0zM12 16v4.5"/>',
    "phone": '<rect x="7" y="3" width="10" height="18" rx="2.5"/><path d="M11 17.5h2"/>',
    "gamepad": '<path d="M7 8h10a4 4 0 0 1 4 4.5l-.6 3.6a2.4 2.4 0 0 1-4.2 1L15 15.5H9l-1.2 1.6a2.4 2.4 0 0 1-4.2-1L3 12.5A4 4 0 0 1 7 8z"/><path d="M8 10.5v3M6.5 12h3"/>',
}


def svg(name: str, color: str) -> bytes:
    body = SYMBOLS.get(name, "").replace("currentColor", color)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" '
            f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{body}</svg>').encode()

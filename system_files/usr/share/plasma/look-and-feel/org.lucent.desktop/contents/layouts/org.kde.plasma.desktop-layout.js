// Lucent OS default layout, applied by plasmashell on a user's first login.
// Uses only the stock Plasma 6 desktop scripting API.
//
// One floating taskbar at the bottom (docs/mockups/01-desktop, lucent.css
// #taskbar): 64 px tall, 14/12 px from the screen edges (the gap comes from
// the Lucent Plasma theme), translucent and blurred.
//
//   [start] [ Search      ]  ....  [pinned + running apps]  ....  [tray] [time/date]
//
// The task manager is icons-only and behaves like the Windows taskbar
// (running windows grouped per app, hover thumbnails, click = minimise or
// restore). There is deliberately no global menu: Flatpak/GTK/Electron apps
// (ONLYOFFICE, GIMP, Firefox...) mostly don't export one, and Windows users
// expect menus inside the window.

var desktopsArray = desktopsForActivity(currentActivity());
for (var i = 0; i < desktopsArray.length; i++) {
    var d = desktopsArray[i];
    d.wallpaperPlugin = "org.kde.image";
    d.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
    d.writeConfig("Image", "file:///usr/share/wallpapers/Drift/");
}

var bar = new Panel;
bar.location = "bottom";
bar.height = 64;
bar.lengthMode = "fill";
bar.floating = true;
bar.hiding = "none";

var launcher = bar.addWidget("org.lucent.launcher");
launcher.currentConfigGroup = ["Shortcuts"];
launcher.writeConfig("global", "Alt+F1");

bar.addWidget("org.lucent.search");
bar.addWidget("org.kde.plasma.panelspacer");

var tasks = bar.addWidget("org.kde.plasma.icontasks");
tasks.currentConfigGroup = ["General"];
tasks.writeConfig("launchers", [
    "applications:org.kde.dolphin.desktop",
    "applications:org.mozilla.firefox.desktop",
    "applications:org.onlyoffice.desktopeditors.desktop",
    "applications:org.kde.okular.desktop",
    "applications:org.gimp.GIMP.desktop",
    "applications:org.lucent.Store.desktop",
    "applications:org.lucent.Settings.desktop"
]);
tasks.writeConfig("groupingStrategy", 1);          // group windows by app
tasks.writeConfig("groupedTaskVisualization", 1);  // click group = thumbnails
tasks.writeConfig("showToolTips", true);           // hover = live thumbnail
tasks.writeConfig("highlightWindows", true);
tasks.writeConfig("minimizeActiveTaskOnClick", true);
tasks.writeConfig("indicateAudioStreams", true);
tasks.writeConfig("iconSpacing", 1);
tasks.writeConfig("maxStripes", 1);

bar.addWidget("org.kde.plasma.panelspacer");
var tray = bar.addWidget("org.kde.plasma.systemtray");
tray.currentConfigGroup = ["General"];
// The mockup tray is keyboard layout, network, volume, battery. Display
// layout and brightness live one click away under the arrow.
tray.writeConfig("hiddenItems", ["org.kde.kscreen", "org.kde.plasma.brightness"]);

var clock = bar.addWidget("org.kde.plasma.digitalclock");
clock.currentConfigGroup = ["Appearance"];
clock.writeConfig("showDate", true);
clock.writeConfig("dateDisplayFormat", 2);       // BelowTime: two lines
clock.writeConfig("dateFormat", "custom");
clock.writeConfig("customDateFormat", "ddd, MMM d");
clock.writeConfig("autoFontAndSize", false);
clock.writeConfig("fontSize", 11);
// With no family set the clock takes the whole system font (weight 400 too).
clock.writeConfig("fontFamily", "Inter");
clock.writeConfig("fontWeight", 600);            // semibold, like the mockup's time
